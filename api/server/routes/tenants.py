"""
Tenant and workspace management API routes.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.tenant import (
    TenantCreate, TenantUpdate, TenantResponse,
    ProjectCreate, ProjectUpdate, ProjectResponse,
    TenantMemberCreate, TenantMemberUpdate,
    ProjectMemberCreate, ProjectMemberUpdate,
    UserContext
)
from ..services.tenant_service import TenantService
from ..middleware.auth import get_current_user
from ..models.user import User

router = APIRouter(prefix="/tenants", tags=["tenants"])
security = HTTPBearer()


def get_tenant_service(db: Session = Depends(get_db)) -> TenantService:
    """Get tenant service instance."""
    return TenantService(db)


# Tenant Routes
@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Create a new tenant."""
    return await tenant_service.create_tenant(tenant_data, current_user.id)


@router.get("/", response_model=List[TenantResponse])
async def list_user_tenants(
    current_user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """List all tenants accessible to the current user."""
    return await tenant_service.list_user_tenants(current_user.id)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: int,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Get tenant by ID."""
    return await tenant_service.get_tenant(tenant_id)


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: int,
    tenant_data: TenantUpdate,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Update tenant."""
    return await tenant_service.update_tenant(tenant_id, tenant_data, current_user.id)


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: int,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Delete tenant (soft delete)."""
    await tenant_service.delete_tenant(tenant_id, current_user.id)


# Tenant Member Routes
@router.post("/{tenant_id}/members", status_code=status.HTTP_201_CREATED)
async def add_tenant_member(
    tenant_id: int,
    member_data: TenantMemberCreate,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Add member to tenant."""
    member_data.tenant_id = tenant_id
    await tenant_service.add_tenant_member(tenant_id, member_data, current_user.id)
    return {"message": "Member added successfully"}


@router.put("/{tenant_id}/members/{user_id}")
async def update_tenant_member(
    tenant_id: int,
    user_id: int,
    member_data: TenantMemberUpdate,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Update tenant member role."""
    await tenant_service.update_tenant_member(tenant_id, user_id, member_data, current_user.id)
    return {"message": "Member updated successfully"}


@router.delete("/{tenant_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tenant_member(
    tenant_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Remove member from tenant."""
    await tenant_service.remove_tenant_member(tenant_id, user_id, current_user.id)


# Project Routes
@router.post("/{tenant_id}/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    tenant_id: int,
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Create a new project in tenant."""
    project_data.tenant_id = tenant_id
    return await tenant_service.create_project(project_data, current_user.id)


@router.get("/{tenant_id}/projects", response_model=List[ProjectResponse])
async def list_tenant_projects(
    tenant_id: int,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """List all projects in tenant."""
    return await tenant_service.list_tenant_projects(tenant_id, current_user.id)


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Get project by ID."""
    return await tenant_service.get_project(project_id)


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Update project."""
    return await tenant_service.update_project(project_id, project_data, current_user.id)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Delete project (soft delete)."""
    await tenant_service.delete_project(project_id, current_user.id)


# Project Member Routes
@router.post("/projects/{project_id}/members", status_code=status.HTTP_201_CREATED)
async def add_project_member(
    project_id: int,
    member_data: ProjectMemberCreate,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Add member to project."""
    member_data.project_id = project_id
    await tenant_service.add_project_member(project_id, member_data, current_user.id)
    return {"message": "Member added successfully"}


@router.put("/projects/{project_id}/members/{user_id}")
async def update_project_member(
    project_id: int,
    user_id: int,
    member_data: ProjectMemberUpdate,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Update project member role."""
    await tenant_service.update_project_member(project_id, user_id, member_data, current_user.id)
    return {"message": "Member updated successfully"}


@router.delete("/projects/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Remove member from project."""
    await tenant_service.remove_project_member(project_id, user_id, current_user.id)


# User Context
@router.get("/context/user", response_model=UserContext)
async def get_user_context(
    current_user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Get complete user context including all accessible tenants and projects."""
    return await tenant_service.get_user_context(current_user.id)
