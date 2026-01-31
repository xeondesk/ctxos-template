"""
Middleware for tenant context and isolation.
"""
from typing import Optional, List
from fastapi import HTTPException, status, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Middleware to handle tenant context and data isolation."""

    def __init__(self, app, excluded_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/auth/login",
            "/auth/refresh",
            "/auth/verify",
        ]

    async def dispatch(self, request: Request, call_next):
        """Process request and add tenant context."""

        # Skip tenant context for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        # Get tenant context from headers
        tenant_id = request.headers.get("X-Tenant-ID")
        project_id = request.headers.get("X-Project-ID")

        # Validate tenant context if provided
        if tenant_id:
            try:
                tenant_id = int(tenant_id)
                request.state.tenant_id = tenant_id
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tenant ID format"
                )

        if project_id:
            try:
                project_id = int(project_id)
                request.state.project_id = project_id
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project ID format"
                )

        # Process request
        response = await call_next(request)

        # Add tenant context headers to response
        if hasattr(request.state, "tenant_id"):
            response.headers["X-Tenant-ID"] = str(request.state.tenant_id)
        if hasattr(request.state, "project_id"):
            response.headers["X-Project-ID"] = str(request.state.project_id)

        return response


def get_tenant_context(request: Request) -> dict:
    """Get tenant context from request state."""
    context = {}

    if hasattr(request.state, "tenant_id"):
        context["tenant_id"] = request.state.tenant_id
    if hasattr(request.state, "project_id"):
        context["project_id"] = request.state.project_id

    return context


def require_tenant_context(request: Request):
    """Require tenant context to be present."""
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required. Include X-Tenant-ID header.",
        )
    return request.state.tenant_id


def require_project_context(request: Request):
    """Require project context to be present."""
    if not hasattr(request.state, "project_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project context required. Include X-Project-ID header.",
        )
    return request.state.project_id


class TenantIsolationMixin:
    """Mixin for database operations with tenant isolation."""

    @staticmethod
    def apply_tenant_filter(
        query, tenant_id: Optional[int] = None, project_id: Optional[int] = None
    ):
        """Apply tenant and project filters to database queries."""
        from ..models.tenant import Project

        if tenant_id:
            # Filter by tenant_id directly or through project relationship
            query = query.filter(
                (getattr(query.column_descriptions[0]["type"], "tenant_id") == tenant_id)
                | (
                    getattr(query.column_descriptions[0]["type"], "project_id").has(
                        Project.tenant_id == tenant_id
                    )
                )
            )

        if project_id:
            query = query.filter(
                getattr(query.column_descriptions[0]["type"], "project_id") == project_id
            )

        return query

    @staticmethod
    def validate_tenant_access(obj, tenant_id: int, user_id: int, db_session):
        """Validate that user has access to tenant data."""
        from ..services.tenant_service import TenantService

        tenant_service = TenantService(db_session)

        # Check if object belongs to tenant
        if hasattr(obj, "tenant_id"):
            if obj.tenant_id != tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: object belongs to different tenant",
                )
        elif hasattr(obj, "project_id"):
            # Check project tenant
            from ..models.tenant import Project

            project = db_session.query(Project).filter(Project.id == obj.project_id).first()
            if project and project.tenant_id != tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: project belongs to different tenant",
                )

        # Check user permissions
        try:
            await tenant_service._check_tenant_permission(
                tenant_id, user_id, ["owner", "admin", "member", "viewer"]
            )
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: insufficient permissions",
            )

    @staticmethod
    def validate_project_access(obj, project_id: int, user_id: int, db_session):
        """Validate that user has access to project data."""
        from ..services.tenant_service import TenantService

        tenant_service = TenantService(db_session)

        # Check if object belongs to project
        if hasattr(obj, "project_id"):
            if obj.project_id != project_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: object belongs to different project",
                )

        # Check user permissions
        try:
            await tenant_service._check_project_permission(
                project_id, user_id, ["owner", "admin", "member", "viewer", "collaborator"]
            )
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: insufficient permissions",
            )


def with_tenant_context(required: bool = True):
    """Decorator to require tenant context for endpoints."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if hasattr(arg, "url"):  # FastAPI Request object
                    request = arg
                    break

            if request and required:
                require_tenant_context(request)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def with_project_context(required: bool = True):
    """Decorator to require project context for endpoints."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if hasattr(arg, "url"):  # FastAPI Request object
                    request = arg
                    break

            if request and required:
                require_project_context(request)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Database session extension for tenant isolation
class TenantAwareSession:
    """Database session extension for tenant-aware operations."""

    def __init__(self, session, tenant_id: Optional[int] = None, project_id: Optional[int] = None):
        self.session = session
        self.tenant_id = tenant_id
        self.project_id = project_id

    def query(self, *args, **kwargs):
        """Create query with tenant filters applied."""
        query = self.session.query(*args, **kwargs)

        if self.tenant_id or self.project_id:
            query = TenantIsolationMixin.apply_tenant_filter(query, self.tenant_id, self.project_id)

        return query

    def add(self, obj):
        """Add object with tenant context."""
        if self.tenant_id and hasattr(obj, "tenant_id"):
            obj.tenant_id = self.tenant_id
        if self.project_id and hasattr(obj, "project_id"):
            obj.project_id = self.project_id

        return self.session.add(obj)

    def __getattr__(self, name):
        """Delegate other methods to underlying session."""
        return getattr(self.session, name)


def get_tenant_aware_session(
    db_session, tenant_id: Optional[int] = None, project_id: Optional[int] = None
):
    """Get tenant-aware database session."""
    return TenantAwareSession(db_session, tenant_id, project_id)
