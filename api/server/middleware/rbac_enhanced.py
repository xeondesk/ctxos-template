"""
Enhanced Role-Based Access Control (RBAC) for multi-tenant environment.
"""
from typing import List, Dict, Set, Optional, Union
from enum import Enum
from functools import wraps
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


class Permission(str, Enum):
    """System-wide permissions."""
    # Tenant permissions
    TENANT_READ = "tenant:read"
    TENANT_UPDATE = "tenant:update"
    TENANT_DELETE = "tenant:delete"
    TENANT_MEMBERS_ADD = "tenant:members:add"
    TENANT_MEMBERS_UPDATE = "tenant:members:update"
    TENANT_MEMBERS_REMOVE = "tenant:members:remove"
    
    # Project permissions
    PROJECTS_CREATE = "projects:create"
    PROJECTS_READ = "projects:read"
    PROJECTS_UPDATE = "projects:update"
    PROJECTS_DELETE = "projects:delete"
    
    # Project-specific permissions
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_MEMBERS_ADD = "project:members:add"
    PROJECT_MEMBERS_UPDATE = "project:members:update"
    PROJECT_MEMBERS_REMOVE = "project:members:remove"
    
    # Data permissions
    DATA_READ = "data:read"
    DATA_CREATE = "data:create"
    DATA_UPDATE = "data:update"
    DATA_DELETE = "data:delete"
    
    # System permissions
    SYSTEM_ADMIN = "system:admin"
    USER_MANAGE = "user:manage"
    AUDIT_READ = "audit:read"


class ResourceType(str, Enum):
    """Resource types for permission checking."""
    TENANT = "tenant"
    PROJECT = "project"
    ENTITY = "entity"
    SIGNAL = "signal"
    SCORE = "score"
    AGENT = "agent"
    CONFIG = "config"
    AUDIT = "audit"


class Action(str, Enum):
    """Actions for permission checking."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    MANAGE = "manage"


# Role-Permission Mapping
TENANT_ROLE_PERMISSIONS = {
    "owner": [
        Permission.TENANT_READ, Permission.TENANT_UPDATE, Permission.TENANT_DELETE,
        Permission.TENANT_MEMBERS_ADD, Permission.TENANT_MEMBERS_UPDATE, Permission.TENANT_MEMBERS_REMOVE,
        Permission.PROJECTS_CREATE, Permission.PROJECTS_READ, Permission.PROJECTS_UPDATE, Permission.PROJECTS_DELETE,
        Permission.DATA_READ, Permission.DATA_CREATE, Permission.DATA_UPDATE, Permission.DATA_DELETE,
        Permission.AUDIT_READ
    ],
    "admin": [
        Permission.TENANT_READ, Permission.TENANT_UPDATE,
        Permission.TENANT_MEMBERS_ADD, Permission.TENANT_MEMBERS_UPDATE, Permission.TENANT_MEMBERS_REMOVE,
        Permission.PROJECTS_CREATE, Permission.PROJECTS_READ, Permission.PROJECTS_UPDATE, Permission.PROJECTS_DELETE,
        Permission.DATA_READ, Permission.DATA_CREATE, Permission.DATA_UPDATE, Permission.DATA_DELETE,
        Permission.AUDIT_READ
    ],
    "member": [
        Permission.TENANT_READ,
        Permission.PROJECTS_CREATE, Permission.PROJECTS_READ, Permission.PROJECTS_UPDATE,
        Permission.DATA_READ, Permission.DATA_CREATE, Permission.DATA_UPDATE
    ],
    "viewer": [
        Permission.TENANT_READ,
        Permission.PROJECTS_READ,
        Permission.DATA_READ
    ]
}

PROJECT_ROLE_PERMISSIONS = {
    "owner": [
        Permission.PROJECT_READ, Permission.PROJECT_UPDATE, Permission.PROJECT_DELETE,
        Permission.PROJECT_MEMBERS_ADD, Permission.PROJECT_MEMBERS_UPDATE, Permission.PROJECT_MEMBERS_REMOVE,
        Permission.DATA_READ, Permission.DATA_CREATE, Permission.DATA_UPDATE, Permission.DATA_DELETE
    ],
    "admin": [
        Permission.PROJECT_READ, Permission.PROJECT_UPDATE,
        Permission.PROJECT_MEMBERS_ADD, Permission.PROJECT_MEMBERS_UPDATE, Permission.PROJECT_MEMBERS_REMOVE,
        Permission.DATA_READ, Permission.DATA_CREATE, Permission.DATA_UPDATE, Permission.DATA_DELETE
    ],
    "member": [
        Permission.PROJECT_READ,
        Permission.DATA_READ, Permission.DATA_CREATE, Permission.DATA_UPDATE
    ],
    "viewer": [
        Permission.PROJECT_READ,
        Permission.DATA_READ
    ],
    "collaborator": [
        Permission.PROJECT_READ,
        Permission.DATA_READ, Permission.DATA_CREATE, Permission.DATA_UPDATE
    ]
}

SYSTEM_ROLE_PERMISSIONS = {
    "super_admin": [
        Permission.SYSTEM_ADMIN, Permission.USER_MANAGE, Permission.AUDIT_READ,
        # All tenant and project permissions
        *[p for p in Permission if p != Permission.SYSTEM_ADMIN]
    ],
    "admin": [
        Permission.USER_MANAGE, Permission.AUDIT_READ,
        Permission.TENANT_READ, Permission.PROJECTS_READ,
        Permission.DATA_READ
    ]
}


class EnhancedRBAC:
    """Enhanced RBAC system for multi-tenant environment."""

    def __init__(self):
        self.permission_cache = {}

    def get_user_permissions(
        self,
        user_id: int,
        tenant_id: Optional[int] = None,
        project_id: Optional[int] = None,
        db_session=None
    ) -> Set[Permission]:
        """Get all permissions for a user in specific context."""
        cache_key = f"{user_id}:{tenant_id}:{project_id}"
        
        if cache_key in self.permission_cache:
            return self.permission_cache[cache_key]

        permissions = set()

        if db_session:
            # Get user's system role
            from ..models.user import User
            user = db_session.query(User).filter(User.id == user_id).first()
            if user and user.role in SYSTEM_ROLE_PERMISSIONS:
                permissions.update(SYSTEM_ROLE_PERMISSIONS[user.role])

            # Get tenant permissions
            if tenant_id:
                from ..models.tenant import TenantMember
                tenant_member = db_session.query(TenantMember).filter(
                    TenantMember.tenant_id == tenant_id,
                    TenantMember.user_id == user_id
                ).first()
                
                if tenant_member:
                    role_permissions = TENANT_ROLE_PERMISSIONS.get(tenant_member.role, [])
                    permissions.update(role_permissions)

            # Get project permissions
            if project_id:
                from ..models.tenant import ProjectMember
                project_member = db_session.query(ProjectMember).filter(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id
                ).first()
                
                if project_member:
                    role_permissions = PROJECT_ROLE_PERMISSIONS.get(project_member.role, [])
                    permissions.update(role_permissions)

        self.permission_cache[cache_key] = permissions
        return permissions

    def check_permission(
        self,
        user_id: int,
        required_permission: Permission,
        tenant_id: Optional[int] = None,
        project_id: Optional[int] = None,
        db_session=None
    ) -> bool:
        """Check if user has specific permission."""
        permissions = self.get_user_permissions(user_id, tenant_id, project_id, db_session)
        return required_permission in permissions

    def check_any_permission(
        self,
        user_id: int,
        required_permissions: List[Permission],
        tenant_id: Optional[int] = None,
        project_id: Optional[int] = None,
        db_session=None
    ) -> bool:
        """Check if user has any of the required permissions."""
        permissions = self.get_user_permissions(user_id, tenant_id, project_id, db_session)
        return any(perm in permissions for perm in required_permissions)

    def check_all_permissions(
        self,
        user_id: int,
        required_permissions: List[Permission],
        tenant_id: Optional[int] = None,
        project_id: Optional[int] = None,
        db_session=None
    ) -> bool:
        """Check if user has all required permissions."""
        permissions = self.get_user_permissions(user_id, tenant_id, project_id, db_session)
        return all(perm in permissions for perm in required_permissions)

    def clear_cache(self, user_id: Optional[int] = None):
        """Clear permission cache."""
        if user_id:
            # Clear cache for specific user
            keys_to_remove = [k for k in self.permission_cache.keys() if k.startswith(f"{user_id}:")]
            for key in keys_to_remove:
                del self.permission_cache[key]
        else:
            # Clear all cache
            self.permission_cache.clear()

    def get_accessible_resources(
        self,
        user_id: int,
        resource_type: ResourceType,
        action: Action,
        db_session=None
    ) -> List[int]:
        """Get list of resource IDs user can access with specific action."""
        # Map resource types and actions to permissions
        permission_map = {
            (ResourceType.TENANT, Action.READ): Permission.TENANT_READ,
            (ResourceType.TENANT, Action.UPDATE): Permission.TENANT_UPDATE,
            (ResourceType.TENANT, Action.DELETE): Permission.TENANT_DELETE,
            (ResourceType.PROJECT, Action.READ): Permission.PROJECT_READ,
            (ResourceType.PROJECT, Action.UPDATE): Permission.PROJECT_UPDATE,
            (ResourceType.PROJECT, Action.DELETE): Permission.PROJECT_DELETE,
            (ResourceType.ENTITY, Action.READ): Permission.DATA_READ,
            (ResourceType.ENTITY, Action.CREATE): Permission.DATA_CREATE,
            (ResourceType.ENTITY, Action.UPDATE): Permission.DATA_UPDATE,
            (ResourceType.ENTITY, Action.DELETE): Permission.DATA_DELETE,
        }

        required_permission = permission_map.get((resource_type, action))
        if not required_permission:
            return []

        accessible_ids = []

        if db_session:
            if resource_type == ResourceType.TENANT:
                from ..models.tenant import TenantMember
                members = db_session.query(TenantMember).filter(
                    TenantMember.user_id == user_id
                ).all()
                
                for member in members:
                    if self.check_permission(
                        user_id, required_permission, member.tenant_id, None, db_session
                    ):
                        accessible_ids.append(member.tenant_id)

            elif resource_type == ResourceType.PROJECT:
                from ..models.tenant import ProjectMember
                members = db_session.query(ProjectMember).filter(
                    ProjectMember.user_id == user_id
                ).all()
                
                for member in members:
                    if self.check_permission(
                        user_id, required_permission, None, member.project_id, db_session
                    ):
                        accessible_ids.append(member.project_id)

        return accessible_ids


# Global RBAC instance
rbac = EnhancedRBAC()


def require_permission(
    permission: Union[Permission, List[Permission]],
    require_all: bool = False,
    tenant_context: bool = False,
    project_context: bool = False
):
    """Decorator to require specific permission(s) for endpoint."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and user from kwargs
            request = None
            current_user = None
            db = None
            
            for key, value in kwargs.items():
                if hasattr(value, 'url'):  # Request object
                    request = value
                elif hasattr(value, 'id'):  # User object
                    current_user = value
                elif hasattr(value, 'query'):  # DB session
                    db = value

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Get tenant/project context
            tenant_id = None
            project_id = None
            
            if request:
                if hasattr(request.state, 'tenant_id'):
                    tenant_id = request.state.tenant_id
                if hasattr(request.state, 'project_id'):
                    project_id = request.state.project_id

            # Check permissions
            if isinstance(permission, list):
                if require_all:
                    has_permission = rbac.check_all_permissions(
                        current_user.id, permission, tenant_id, project_id, db
                    )
                else:
                    has_permission = rbac.check_any_permission(
                        current_user.id, permission, tenant_id, project_id, db
                    )
            else:
                has_permission = rbac.check_permission(
                    current_user.id, permission, tenant_id, project_id, db
                )

            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_tenant_role(role: Union[str, List[str]]):
    """Decorator to require specific tenant role(s)."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            current_user = None
            db = None
            
            for key, value in kwargs.items():
                if hasattr(value, 'url'):
                    request = value
                elif hasattr(value, 'id'):
                    current_user = value
                elif hasattr(value, 'query'):
                    db = value

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            tenant_id = None
            if request and hasattr(request.state, 'tenant_id'):
                tenant_id = request.state.tenant_id

            if not tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tenant context required"
                )

            # Check tenant role
            from ..models.tenant import TenantMember
            member = db.query(TenantMember).filter(
                TenantMember.tenant_id == tenant_id,
                TenantMember.user_id == current_user.id
            ).first()

            if not member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: not a tenant member"
                )

            if isinstance(role, list):
                if member.role not in role:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied: requires one of roles {role}"
                    )
            else:
                if member.role != role:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied: requires role {role}"
                    )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_project_role(role: Union[str, List[str]]):
    """Decorator to require specific project role(s)."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            current_user = None
            db = None
            
            for key, value in kwargs.items():
                if hasattr(value, 'url'):
                    request = value
                elif hasattr(value, 'id'):
                    current_user = value
                elif hasattr(value, 'query'):
                    db = value

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            project_id = None
            if request and hasattr(request.state, 'project_id'):
                project_id = request.state.project_id

            if not project_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Project context required"
                )

            # Check project role
            from ..models.tenant import ProjectMember
            member = db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == current_user.id
            ).first()

            if not member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: not a project member"
                )

            if isinstance(role, list):
                if member.role not in role:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied: requires one of roles {role}"
                    )
            else:
                if member.role != role:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied: requires role {role}"
                    )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Dependency functions for FastAPI
async def get_current_user_permissions(
    request: Request,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
) -> Set[Permission]:
    """Get current user's permissions."""
    tenant_id = getattr(request.state, 'tenant_id', None)
    project_id = getattr(request.state, 'project_id', None)
    
    return rbac.get_user_permissions(
        current_user.id, tenant_id, project_id, db
    )


async def check_user_permission(
    permission: Permission,
    request: Request,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Check if current user has specific permission."""
    tenant_id = getattr(request.state, 'tenant_id', None)
    project_id = getattr(request.state, 'project_id', None)
    
    if not rbac.check_permission(
        current_user.id, permission, tenant_id, project_id, db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions: {permission}"
        )


# Permission checking utilities
def can_access_tenant(user_id: int, tenant_id: int, db_session) -> bool:
    """Check if user can access tenant."""
    return rbac.check_permission(
        user_id, Permission.TENANT_READ, tenant_id, None, db_session
    )


def can_access_project(user_id: int, project_id: int, db_session) -> bool:
    """Check if user can access project."""
    return rbac.check_permission(
        user_id, Permission.PROJECT_READ, None, project_id, db_session
    )


def can_manage_tenant(user_id: int, tenant_id: int, db_session) -> bool:
    """Check if user can manage tenant."""
    return rbac.check_any_permission(
        user_id, [Permission.TENANT_UPDATE, Permission.TENANT_DELETE], 
        tenant_id, None, db_session
    )


def can_manage_project(user_id: int, project_id: int, db_session) -> bool:
    """Check if user can manage project."""
    return rbac.check_any_permission(
        user_id, [Permission.PROJECT_UPDATE, Permission.PROJECT_DELETE], 
        None, project_id, db_session
    )
