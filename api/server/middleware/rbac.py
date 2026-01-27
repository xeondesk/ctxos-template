"""
Role-Based Access Control (RBAC) middleware.
"""

from fastapi import Depends, HTTPException, status, Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Set, Optional, Callable
from enum import Enum

from api.server.middleware.auth import TokenData


class Role(str, Enum):
    """User roles."""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    API_CLIENT = "api_client"


# Role-based permissions mapping
ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    Role.ADMIN: {
        "read", "write", "delete", "manage_users", "manage_config",
        "view_audit_logs", "manage_rules",
    },
    Role.ANALYST: {
        "read", "write", "run_agents", "run_pipelines", "view_audit_logs",
    },
    Role.VIEWER: {
        "read", "view_audit_logs",
    },
    Role.API_CLIENT: {
        "read", "run_agents", "run_pipelines",
    },
}

# Endpoint-to-permission mapping
ENDPOINT_PERMISSIONS: Dict[str, Set[str]] = {
    # Scoring endpoints
    "/api/v1/score/risk": {"read"},
    "/api/v1/score/exposure": {"read"},
    "/api/v1/score/drift": {"read"},
    
    # Agent endpoints
    "/api/v1/agents/run": {"run_agents"},
    "/api/v1/agents/status": {"read"},
    "/api/v1/agents/pipeline": {"run_pipelines"},
    
    # Config endpoints
    "/api/v1/config": {"read"},
    "/api/v1/config/update": {"manage_config"},
    "/api/v1/config/rules": {"manage_rules"},
    
    # Audit endpoints
    "/api/v1/audit/logs": {"view_audit_logs"},
}


class RBACMiddleware(BaseHTTPMiddleware):
    """RBAC middleware for request authorization."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request with RBAC checks."""
        # Skip RBAC for public endpoints
        public_paths = {"/", "/health", "/api/docs", "/api/openapi.json"}
        if request.url.path in public_paths:
            return await call_next(request)
        
        # Extract token from request (if available)
        # This will be populated by FastAPI dependency injection
        # For now, just pass through
        return await call_next(request)


def require_permission(
    required_permission: str,
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
    user_permissions = ROLE_PERMISSIONS.get(token_data.role, set())
    
    if required_permission not in user_permissions:
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role required: {required_role.value}",
        )
    
    return token_data


def require_role_in(
    required_roles: list[str],
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
    if token_data.role not in required_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"One of these roles required: {', '.join(required_roles)}",
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
    return permission_levels.get(role, 0)


class AuthorizationService:
    """Service for authorization checks."""
    
    @staticmethod
    def check_permission(
        token_data: TokenData,
        required_permission: str,
    ) -> bool:
        """Check if token has required permission.
        
        Args:
            token_data: Token data
            required_permission: Required permission
            
        Returns:
            True if authorized, False otherwise
        """
        user_permissions = ROLE_PERMISSIONS.get(token_data.role, set())
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
    def get_permissions(token_data: TokenData) -> Set[str]:
        """Get all permissions for token.
        
        Args:
            token_data: Token data
            
        Returns:
            Set of permissions
        """
        return ROLE_PERMISSIONS.get(token_data.role, set())
