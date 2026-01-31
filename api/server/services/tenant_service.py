"""
Tenant and workspace management service.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status

from ..models.tenant import (
    Tenant,
    Project,
    TenantMember,
    ProjectMember,
    TenantCreate,
    TenantUpdate,
    ProjectCreate,
    ProjectUpdate,
    TenantMemberCreate,
    TenantMemberUpdate,
    ProjectMemberCreate,
    ProjectMemberUpdate,
    TenantResponse,
    ProjectResponse,
    UserContext,
    UserTenantAccess,
    UserProjectAccess,
    TenantStatus,
    ProjectStatus,
    TenantRole,
    ProjectRole,
)
from ..models.user import User


class TenantService:
    """Service for managing tenants and projects."""

    def __init__(self, db: Session):
        self.db = db

    # Tenant Management
    async def create_tenant(self, tenant_data: TenantCreate, creator_id: int) -> TenantResponse:
        """Create a new tenant."""
        # Check if slug already exists
        existing = self.db.query(Tenant).filter(Tenant.slug == tenant_data.slug).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tenant with slug '{tenant_data.slug}' already exists",
            )

        # Create tenant
        tenant = Tenant(
            name=tenant_data.name,
            slug=tenant_data.slug,
            description=tenant_data.description,
            settings=tenant_data.settings,
            storage_quota_gb=tenant_data.storage_quota_gb,
            user_limit=tenant_data.user_limit,
            project_limit=tenant_data.project_limit,
            created_by=creator_id,
            status=TenantStatus.ACTIVE,
        )

        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)

        # Add creator as owner
        member = TenantMember(
            tenant_id=tenant.id, user_id=creator_id, role=TenantRole.OWNER, invited_by=creator_id
        )
        self.db.add(member)
        self.db.commit()

        return await self.get_tenant(tenant.id)

    async def get_tenant(self, tenant_id: int) -> TenantResponse:
        """Get tenant by ID."""
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

        # Get counts
        member_count = (
            self.db.query(TenantMember).filter(TenantMember.tenant_id == tenant_id).count()
        )

        project_count = self.db.query(Project).filter(Project.tenant_id == tenant_id).count()

        return TenantResponse(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            description=tenant.description,
            status=tenant.status,
            settings=tenant.settings,
            storage_quota_gb=tenant.storage_quota_gb,
            user_limit=tenant.user_limit,
            project_limit=tenant.project_limit,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
            created_by=tenant.created_by,
            member_count=member_count,
            project_count=project_count,
        )

    async def update_tenant(
        self, tenant_id: int, tenant_data: TenantUpdate, user_id: int
    ) -> TenantResponse:
        """Update tenant."""
        # Check permissions
        await self._check_tenant_permission(
            tenant_id, user_id, [TenantRole.OWNER, TenantRole.ADMIN]
        )

        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

        # Update fields
        update_data = tenant_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tenant, field, value)

        tenant.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(tenant)

        return await self.get_tenant(tenant_id)

    async def delete_tenant(self, tenant_id: int, user_id: int) -> bool:
        """Delete tenant (soft delete by setting status to inactive)."""
        await self._check_tenant_permission(tenant_id, user_id, [TenantRole.OWNER])

        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

        tenant.status = TenantStatus.INACTIVE
        tenant.updated_at = datetime.utcnow()
        self.db.commit()

        return True

    async def list_user_tenants(self, user_id: int) -> List[TenantResponse]:
        """List all tenants accessible to user."""
        members = self.db.query(TenantMember).filter(TenantMember.user_id == user_id).all()

        tenant_ids = [member.tenant_id for member in members]
        tenants = self.db.query(Tenant).filter(Tenant.id.in_(tenant_ids)).all()

        result = []
        for tenant in tenants:
            member_count = (
                self.db.query(TenantMember).filter(TenantMember.tenant_id == tenant.id).count()
            )

            project_count = self.db.query(Project).filter(Project.tenant_id == tenant.id).count()

            result.append(
                TenantResponse(
                    id=tenant.id,
                    name=tenant.name,
                    slug=tenant.slug,
                    description=tenant.description,
                    status=tenant.status,
                    settings=tenant.settings,
                    storage_quota_gb=tenant.storage_quota_gb,
                    user_limit=tenant.user_limit,
                    project_limit=tenant.project_limit,
                    created_at=tenant.created_at,
                    updated_at=tenant.updated_at,
                    created_by=tenant.created_by,
                    member_count=member_count,
                    project_count=project_count,
                )
            )

        return result

    # Project Management
    async def create_project(self, project_data: ProjectCreate, creator_id: int) -> ProjectResponse:
        """Create a new project."""
        # Check tenant permissions
        await self._check_tenant_permission(
            project_data.tenant_id,
            creator_id,
            [TenantRole.OWNER, TenantRole.ADMIN, TenantRole.MEMBER],
        )

        # Check if slug already exists in tenant
        existing = (
            self.db.query(Project)
            .filter(
                and_(Project.tenant_id == project_data.tenant_id, Project.slug == project_data.slug)
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Project with slug '{project_data.slug}' already exists in this tenant",
            )

        # Check tenant project limit
        tenant = await self._get_tenant_for_user(project_data.tenant_id, creator_id)
        project_count = (
            self.db.query(Project).filter(Project.tenant_id == project_data.tenant_id).count()
        )

        if project_count >= tenant.project_limit:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Tenant project limit reached"
            )

        # Create project
        project = Project(
            tenant_id=project_data.tenant_id,
            name=project_data.name,
            slug=project_data.slug,
            description=project_data.description,
            settings=project_data.settings,
            storage_quota_gb=project_data.storage_quota_gb,
            created_by=creator_id,
            status=ProjectStatus.ACTIVE,
        )

        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        # Add creator as owner
        member = ProjectMember(
            project_id=project.id, user_id=creator_id, role=ProjectRole.OWNER, added_by=creator_id
        )
        self.db.add(member)
        self.db.commit()

        return await self.get_project(project.id)

    async def get_project(self, project_id: int) -> ProjectResponse:
        """Get project by ID."""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        # Get tenant name and member count
        tenant = self.db.query(Tenant).filter(Tenant.id == project.tenant_id).first()
        member_count = (
            self.db.query(ProjectMember).filter(ProjectMember.project_id == project_id).count()
        )

        return ProjectResponse(
            id=project.id,
            tenant_id=project.tenant_id,
            tenant_name=tenant.name if tenant else None,
            name=project.name,
            slug=project.slug,
            description=project.description,
            status=project.status,
            settings=project.settings,
            storage_quota_gb=project.storage_quota_gb,
            created_at=project.created_at,
            updated_at=project.updated_at,
            created_by=project.created_by,
            member_count=member_count,
        )

    async def update_project(
        self, project_id: int, project_data: ProjectUpdate, user_id: int
    ) -> ProjectResponse:
        """Update project."""
        await self._check_project_permission(
            project_id, user_id, [ProjectRole.OWNER, ProjectRole.ADMIN]
        )

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        # Update fields
        update_data = project_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        project.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(project)

        return await self.get_project(project_id)

    async def delete_project(self, project_id: int, user_id: int) -> bool:
        """Delete project (soft delete by setting status to archived)."""
        await self._check_project_permission(project_id, user_id, [ProjectRole.OWNER])

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        project.status = ProjectStatus.ARCHIVED
        project.updated_at = datetime.utcnow()
        self.db.commit()

        return True

    async def list_tenant_projects(self, tenant_id: int, user_id: int) -> List[ProjectResponse]:
        """List all projects in a tenant accessible to user."""
        await self._check_tenant_permission(
            tenant_id, user_id, [TenantRole.OWNER, TenantRole.ADMIN, TenantRole.MEMBER]
        )

        projects = (
            self.db.query(Project)
            .filter(and_(Project.tenant_id == tenant_id, Project.status != ProjectStatus.ARCHIVED))
            .all()
        )

        result = []
        for project in projects:
            member_count = (
                self.db.query(ProjectMember).filter(ProjectMember.project_id == project.id).count()
            )

            result.append(
                ProjectResponse(
                    id=project.id,
                    tenant_id=project.tenant_id,
                    name=project.name,
                    slug=project.slug,
                    description=project.description,
                    status=project.status,
                    settings=project.settings,
                    storage_quota_gb=project.storage_quota_gb,
                    created_at=project.created_at,
                    updated_at=project.updated_at,
                    created_by=project.created_by,
                    member_count=member_count,
                )
            )

        return result

    # Member Management
    async def add_tenant_member(
        self, tenant_id: int, member_data: TenantMemberCreate, user_id: int
    ) -> bool:
        """Add member to tenant."""
        await self._check_tenant_permission(
            tenant_id, user_id, [TenantRole.OWNER, TenantRole.ADMIN]
        )

        # Check if user exists
        user = self.db.query(User).filter(User.id == member_data.user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Check if already member
        existing = (
            self.db.query(TenantMember)
            .filter(
                and_(
                    TenantMember.tenant_id == tenant_id, TenantMember.user_id == member_data.user_id
                )
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this tenant",
            )

        # Check tenant user limit
        tenant = await self._get_tenant_for_user(tenant_id, user_id)
        member_count = (
            self.db.query(TenantMember).filter(TenantMember.tenant_id == tenant_id).count()
        )

        if member_count >= tenant.user_limit:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Tenant user limit reached"
            )

        # Add member
        member = TenantMember(
            tenant_id=tenant_id,
            user_id=member_data.user_id,
            role=member_data.role,
            invited_by=user_id,
        )
        self.db.add(member)
        self.db.commit()

        return True

    async def update_tenant_member(
        self, tenant_id: int, user_id: int, member_data: TenantMemberUpdate, current_user_id: int
    ) -> bool:
        """Update tenant member role."""
        await self._check_tenant_permission(
            tenant_id, current_user_id, [TenantRole.OWNER, TenantRole.ADMIN]
        )

        member = (
            self.db.query(TenantMember)
            .filter(and_(TenantMember.tenant_id == tenant_id, TenantMember.user_id == user_id))
            .first()
        )

        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

        member.role = member_data.role
        member.updated_at = datetime.utcnow()
        self.db.commit()

        return True

    async def remove_tenant_member(
        self, tenant_id: int, user_id: int, current_user_id: int
    ) -> bool:
        """Remove member from tenant."""
        await self._check_tenant_permission(
            tenant_id, current_user_id, [TenantRole.OWNER, TenantRole.ADMIN]
        )

        member = (
            self.db.query(TenantMember)
            .filter(and_(TenantMember.tenant_id == tenant_id, TenantMember.user_id == user_id))
            .first()
        )

        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

        self.db.delete(member)
        self.db.commit()

        return True

    async def add_project_member(
        self, project_id: int, member_data: ProjectMemberCreate, user_id: int
    ) -> bool:
        """Add member to project."""
        await self._check_project_permission(
            project_id, user_id, [ProjectRole.OWNER, ProjectRole.ADMIN]
        )

        # Check if user exists
        user = self.db.query(User).filter(User.id == member_data.user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Check if already member
        existing = (
            self.db.query(ProjectMember)
            .filter(
                and_(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == member_data.user_id,
                )
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this project",
            )

        # Add member
        member = ProjectMember(
            project_id=project_id,
            user_id=member_data.user_id,
            role=member_data.role,
            added_by=user_id,
        )
        self.db.add(member)
        self.db.commit()

        return True

    async def update_project_member(
        self, project_id: int, user_id: int, member_data: ProjectMemberUpdate, current_user_id: int
    ) -> bool:
        """Update project member role."""
        await self._check_project_permission(
            project_id, current_user_id, [ProjectRole.OWNER, ProjectRole.ADMIN]
        )

        member = (
            self.db.query(ProjectMember)
            .filter(and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id))
            .first()
        )

        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

        member.role = member_data.role
        member.updated_at = datetime.utcnow()
        self.db.commit()

        return True

    async def remove_project_member(
        self, project_id: int, user_id: int, current_user_id: int
    ) -> bool:
        """Remove member from project."""
        await self._check_project_permission(
            project_id, current_user_id, [ProjectRole.OWNER, ProjectRole.ADMIN]
        )

        member = (
            self.db.query(ProjectMember)
            .filter(and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id))
            .first()
        )

        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

        self.db.delete(member)
        self.db.commit()

        return True

    # User Context
    async def get_user_context(self, user_id: int) -> UserContext:
        """Get complete user context including all accessible tenants and projects."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Get tenant memberships
        tenant_members = self.db.query(TenantMember).filter(TenantMember.user_id == user_id).all()
        tenants = []

        for member in tenant_members:
            tenant = self.db.query(Tenant).filter(Tenant.id == member.tenant_id).first()
            if tenant:
                permissions = await self._get_tenant_permissions(member.role)
                tenants.append(
                    UserTenantAccess(
                        tenant_id=tenant.id,
                        tenant_name=tenant.name,
                        tenant_slug=tenant.slug,
                        role=member.role,
                        permissions=permissions,
                    )
                )

        # Get project memberships
        project_members = (
            self.db.query(ProjectMember).filter(ProjectMember.user_id == user_id).all()
        )
        projects = []

        for member in project_members:
            project = self.db.query(Project).filter(Project.id == member.project_id).first()
            if project:
                tenant = self.db.query(Tenant).filter(Tenant.id == project.tenant_id).first()
                permissions = await self._get_project_permissions(member.role)
                projects.append(
                    UserProjectAccess(
                        project_id=project.id,
                        project_name=project.name,
                        project_slug=project.slug,
                        tenant_id=project.tenant_id,
                        tenant_name=tenant.name if tenant else "",
                        role=member.role,
                        permissions=permissions,
                    )
                )

        return UserContext(
            user_id=user.id,
            username=user.username,
            email=user.email,
            tenants=tenants,
            projects=projects,
        )

    # Helper Methods
    async def _check_tenant_permission(
        self, tenant_id: int, user_id: int, required_roles: List[TenantRole]
    ) -> None:
        """Check if user has required tenant role."""
        member = (
            self.db.query(TenantMember)
            .filter(and_(TenantMember.tenant_id == tenant_id, TenantMember.user_id == user_id))
            .first()
        )

        if not member or member.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for tenant operation",
            )

    async def _check_project_permission(
        self, project_id: int, user_id: int, required_roles: List[ProjectRole]
    ) -> None:
        """Check if user has required project role."""
        member = (
            self.db.query(ProjectMember)
            .filter(and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id))
            .first()
        )

        if not member or member.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for project operation",
            )

    async def _get_tenant_for_user(self, tenant_id: int, user_id: int) -> Tenant:
        """Get tenant if user has access."""
        member = (
            self.db.query(TenantMember)
            .filter(and_(TenantMember.tenant_id == tenant_id, TenantMember.user_id == user_id))
            .first()
        )

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to tenant"
            )

        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

        return tenant

    async def _get_tenant_permissions(self, role: TenantRole) -> List[str]:
        """Get permissions for tenant role."""
        permissions = {
            TenantRole.OWNER: [
                "tenant:read",
                "tenant:update",
                "tenant:delete",
                "tenant:members:add",
                "tenant:members:update",
                "tenant:members:remove",
                "projects:create",
                "projects:read",
                "projects:update",
                "projects:delete",
            ],
            TenantRole.ADMIN: [
                "tenant:read",
                "tenant:update",
                "tenant:members:add",
                "tenant:members:update",
                "tenant:members:remove",
                "projects:create",
                "projects:read",
                "projects:update",
                "projects:delete",
            ],
            TenantRole.MEMBER: [
                "tenant:read",
                "projects:create",
                "projects:read",
                "projects:update",
            ],
            TenantRole.VIEWER: ["tenant:read", "projects:read"],
        }
        return permissions.get(role, [])

    async def _get_project_permissions(self, role: ProjectRole) -> List[str]:
        """Get permissions for project role."""
        permissions = {
            ProjectRole.OWNER: [
                "project:read",
                "project:update",
                "project:delete",
                "project:members:add",
                "project:members:update",
                "project:members:remove",
                "data:read",
                "data:create",
                "data:update",
                "data:delete",
            ],
            ProjectRole.ADMIN: [
                "project:read",
                "project:update",
                "project:members:add",
                "project:members:update",
                "project:members:remove",
                "data:read",
                "data:create",
                "data:update",
                "data:delete",
            ],
            ProjectRole.MEMBER: ["project:read", "data:read", "data:create", "data:update"],
            ProjectRole.VIEWER: ["project:read", "data:read"],
            ProjectRole.COLLABORATOR: ["project:read", "data:read", "data:create", "data:update"],
        }
        return permissions.get(role, [])
