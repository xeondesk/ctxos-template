"""
Role-Based Access Control (RBAC) middleware.
"""

from fastapi import Depends, HTTPException, status, Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Set, Optional, Callable, List
from enum import Enum
import logging

from api.server.middleware.auth import TokenData

logger = logging.getLogger(__name__)


class Role(str, Enum):
    """User roles."""

    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    API_CLIENT = "api_client"


class Permission(str, Enum):
    """Permission types."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    MANAGE_USERS = "manage_users"
    MANAGE_CONFIG = "manage_config"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_RULES = "manage_rules"
    RUN_AGENTS = "run_agents"
    RUN_PIPELINES = "run_pipelines"
    MANAGE_PIPELINES = "manage_pipelines"


# Role-based permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        Permission.READ,
        Permission.WRITE,
        Permission.DELETE,
        Permission.MANAGE_USERS,
        Permission.MANAGE_CONFIG,
        Permission.VIEW_AUDIT_LOGS,
        Permission.MANAGE_RULES,
        Permission.RUN_AGENTS,
        Permission.RUN_PIPELINES,
        Permission.MANAGE_PIPELINES,
    },
    Role.ANALYST: {
        Permission.READ,
        Permission.WRITE,
        Permission.RUN_AGENTS,
        Permission.RUN_PIPELINES,
        Permission.VIEW_AUDIT_LOGS,
    },
    Role.VIEWER: {
        Permission.READ,
        Permission.VIEW_AUDIT_LOGS,
    },
    Role.API_CLIENT: {
        Permission.READ,
        Permission.RUN_AGENTS,
        Permission.RUN_PIPELINES,
    },
}

# Endpoint-to-permission mapping
ENDPOINT_PERMISSIONS: Dict[str, Set[Permission]] = {
    # Scoring endpoints
    "/api/v1/score": {Permission.READ},
    "/api/v1/score/batch": {Permission.READ},
    "/api/v1/score/history": {Permission.READ},
    "/api/v1/score/engines": {Permission.READ},
    "/api/v1/score/aggregate": {Permission.READ},
    "/api/v1/score/compare": {Permission.READ},
    "/api/v1/score/status": {Permission.READ},
    # Agent endpoints
    "/api/v1/agents/run": {Permission.RUN_AGENTS},
    "/api/v1/agents/pipeline": {Permission.RUN_PIPELINES},
    "/api/v1/agents/bulk": {Permission.RUN_AGENTS},
    "/api/v1/agents/list": {Permission.READ},
    "/api/v1/agents/status": {Permission.READ},
    "/api/v1/agents/pipelines": {Permission.READ},
    "/api/v1/agents/create-pipeline": {Permission.MANAGE_PIPELINES},
    "/api/v1/agents/filter": {Permission.READ},
    "/api/v1/agents/audit-logs": {Permission.VIEW_AUDIT_LOGS},
    "/api/v1/agents/metrics": {Permission.READ},
    "/api/v1/agents/health": {Permission.READ},
    # Config endpoints
    "/api/v1/config": {Permission.READ},
    "/api/v1/config/update": {Permission.MANAGE_CONFIG},
    "/api/v1/config/rules": {Permission.MANAGE_RULES},
    # User management endpoints
    "/api/v1/users": {Permission.MANAGE_USERS},
    "/api/v1/users/create": {Permission.MANAGE_USERS},
    "/api/v1/users/update": {Permission.MANAGE_USERS},
    "/api/v1/users/delete": {Permission.MANAGE_USERS},
}


class RBACMiddleware(BaseHTTPMiddleware):
    """RBAC middleware for request authorization."""

    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next):
        """Process request with RBAC checks."""
        # Skip RBAC for public endpoints
        public_paths = {"/", "/health", "/api/docs", "/api/openapi.json", "/api/v1/auth/login"}
        if request.url.path in public_paths:
            return await call_next(request)

        # Skip RBAC for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            self.logger.warning(f"No auth header for {request.method} {request.url.path}")
            return await call_next(request)  # Let endpoint handle auth

        # For now, just pass through - actual auth is handled by dependencies
        return await call_next(request)


def require_permission(
    required_permission: Permission,
    token_data: TokenData = Depends(),
) -> TokenData:
    """Dependency to require specific permission.

    Args:
        required_permission: Required permission
        token_data: Token data from auth

    Returns:
        TokenData if authorized

    Raises:
        HTTPException: If not authorized
    """
    user_permissions = ROLE_PERMISSIONS.get(Role(token_data.role), set())

    if required_permission not in user_permissions:
        logger.warning(
            f"Permission denied: user {token_data.username} ({token_data.role}) "
            f"lacks permission {required_permission}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {required_permission} required",
        )

    return token_data


def require_role(
    required_role: Role,
    token_data: TokenData = Depends(),
) -> TokenData:
    """Dependency to require specific role.

    Args:
        required_role: Required role
        token_data: Token data from auth

    Returns:
        TokenData if authorized

    Raises:
        HTTPException: If not authorized
    """
    if token_data.role != required_role.value:
        logger.warning(
            f"Role required: user {token_data.username} ({token_data.role}) "
            f"is not {required_role.value}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role required: {required_role.value}",
        )

    return token_data


def require_role_in(
    required_roles: List[Role],
    token_data: TokenData = Depends(),
) -> TokenData:
    """Dependency to require one of multiple roles.

    Args:
        required_roles: List of allowed roles
        token_data: Token data from auth

    Returns:
        TokenData if authorized

    Raises:
        HTTPException: If not authorized
    """
    allowed_role_values = [role.value for role in required_roles]
    if token_data.role not in allowed_role_values:
        logger.warning(
            f"Role required: user {token_data.username} ({token_data.role}) "
            f"not in {allowed_role_values}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"One of these roles required: {', '.join(allowed_role_values)}",
        )

    return token_data


def require_any_permission(
    required_permissions: List[Permission],
    token_data: TokenData = Depends(),
) -> TokenData:
    """Dependency to require any of multiple permissions.

    Args:
        required_permissions: List of allowed permissions
        token_data: Token data from auth

    Returns:
        TokenData if authorized

    Raises:
        HTTPException: If not authorized
    """
    user_permissions = ROLE_PERMISSIONS.get(Role(token_data.role), set())

    if not any(perm in user_permissions for perm in required_permissions):
        required_perm_names = [perm.value for perm in required_permissions]
        logger.warning(
            f"Permission denied: user {token_data.username} ({token_data.role}) "
            f"lacks any of {required_perm_names}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"One of these permissions required: {', '.join(required_perm_names)}",
        )

    return token_data


def get_permission_level(role: str) -> int:
    """Get numeric permission level for a role.

    Args:
        role: Role name

    Returns:
        Permission level (higher = more permissions)
    """
    permission_levels = {
        Role.VIEWER: 1,
        Role.ANALYST: 2,
        Role.API_CLIENT: 2,
        Role.ADMIN: 3,
    }
    return permission_levels.get(Role(role), 0)


def check_endpoint_permission(
    request_path: str,
    method: str,
    token_data: TokenData,
) -> bool:
    """Check if token has permission for endpoint.

    Args:
        request_path: Request path
        method: HTTP method
        token_data: Token data

    Returns:
        True if authorized, False otherwise
    """
    # Get required permissions for endpoint
    endpoint_perms = ENDPOINT_PERMISSIONS.get(request_path, set())

    # Check write permissions for write methods
    if method in {"POST", "PUT", "DELETE", "PATCH"} and Permission.WRITE not in endpoint_perms:
        endpoint_perms.add(Permission.WRITE)

    user_permissions = ROLE_PERMISSIONS.get(Role(token_data.role), set())

    return any(perm in user_permissions for perm in endpoint_perms)


class AuthorizationService:
    """Service for authorization checks."""

    @staticmethod
    def check_permission(
        token_data: TokenData,
        required_permission: Permission,
    ) -> bool:
        """Check if token has required permission.

        Args:
            token_data: Token data
            required_permission: Required permission

        Returns:
            True if authorized, False otherwise
        """
        user_permissions = ROLE_PERMISSIONS.get(Role(token_data.role), set())
        return required_permission in user_permissions

    @staticmethod
    def check_role(
        token_data: TokenData,
        required_role: str,
    ) -> bool:
        """Check if token has required role.

        Args:
            token_data: Token data
            required_role: Required role

        Returns:
            True if role matches, False otherwise
        """
        return token_data.role == required_role

    @staticmethod
    def get_permissions(token_data: TokenData) -> Set[Permission]:
        """Get all permissions for token.

        Args:
            token_data: Token data

        Returns:
            Set of permissions
        """
        return ROLE_PERMISSIONS.get(Role(token_data.role), set())

    @staticmethod
    def can_access_resource(
        token_data: TokenData,
        resource_type: str,
        action: str,
    ) -> bool:
        """Check if user can access resource with specific action.

        Args:
            token_data: Token data
            resource_type: Type of resource (e.g., "agent", "config", "user")
            action: Action to perform (e.g., "read", "write", "delete")

        Returns:
            True if authorized, False otherwise
        """
        # Map resource/action to permissions
        permission_map = {
            ("agent", "read"): Permission.READ,
            ("agent", "run"): Permission.RUN_AGENTS,
            ("config", "read"): Permission.READ,
            ("config", "write"): Permission.MANAGE_CONFIG,
            ("user", "read"): Permission.MANAGE_USERS,
            ("user", "write"): Permission.MANAGE_USERS,
            ("user", "delete"): Permission.MANAGE_USERS,
            ("audit", "read"): Permission.VIEW_AUDIT_LOGS,
            ("rule", "read"): Permission.READ,
            ("rule", "write"): Permission.MANAGE_RULES,
            ("pipeline", "read"): Permission.READ,
            ("pipeline", "run"): Permission.RUN_PIPELINES,
            ("pipeline", "manage"): Permission.MANAGE_PIPELINES,
        }

        required_permission = permission_map.get((resource_type, action))
        if not required_permission:
            # Default to read permission for unknown combinations
            required_permission = Permission.READ

        return AuthorizationService.check_permission(token_data, required_permission)

    @staticmethod
    def get_user_capabilities(token_data: TokenData) -> Dict[str, Any]:
        """Get user capabilities summary.

        Args:
            token_data: Token data

        Returns:
            Dictionary of user capabilities
        """
        permissions = AuthorizationService.get_permissions(token_data)
        role_level = get_permission_level(token_data.role)

        return {
            "user_id": token_data.user_id,
            "username": token_data.username,
            "role": token_data.role,
            "role_level": role_level,
            "permissions": [perm.value for perm in permissions],
            "can_read": Permission.READ in permissions,
            "can_write": Permission.WRITE in permissions,
            "can_delete": Permission.DELETE in permissions,
            "can_manage_users": Permission.MANAGE_USERS in permissions,
            "can_manage_config": Permission.MANAGE_CONFIG in permissions,
            "can_run_agents": Permission.RUN_AGENTS in permissions,
            "can_run_pipelines": Permission.RUN_PIPELINES in permissions,
            "can_view_audit_logs": Permission.VIEW_AUDIT_LOGS in permissions,
            "can_manage_rules": Permission.MANAGE_RULES in permissions,
            "can_manage_pipelines": Permission.MANAGE_PIPELINES in permissions,
        }


def log_access_attempt(
    request_path: str,
    method: str,
    token_data: Optional[TokenData],
    success: bool,
    reason: Optional[str] = None,
):
    """Log access attempt for audit purposes.

    Args:
        request_path: Request path
        method: HTTP method
        token_data: Token data (if available)
        success: Whether access was successful
        reason: Reason for failure (if applicable)
    """
    if token_data:
        logger.info(
            f"Access {'granted' if success else 'denied'}: "
            f"user={token_data.username}({token_data.role}) "
            f"method={method} path={request_path}" + (f" reason={reason}" if reason else "")
        )
    else:
        logger.info(
            f"Access {'granted' if success else 'denied'}: "
            f"anonymous method={method} path={request_path}"
            + (f" reason={reason}" if reason else "")
        )
