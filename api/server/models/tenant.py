"""
Tenant and workspace models for multi-tenancy.
"""
from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TenantStatus(str, Enum):
    """Tenant status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class ProjectStatus(str, Enum):
    """Project status enumeration."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"
    PENDING = "pending"


class TenantRole(str, Enum):
    """User role within tenant."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class ProjectRole(str, Enum):
    """User role within project."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"
    COLLABORATOR = "collaborator"


# Database Models
class Tenant(Base):
    """Tenant model for workspace isolation."""
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    status = Column(String(20), default=TenantStatus.ACTIVE)
    
    # Configuration
    settings = Column(JSON)
    storage_quota_gb = Column(Integer, default=100)
    user_limit = Column(Integer, default=50)
    project_limit = Column(Integer, default=10)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    projects = relationship("Project", back_populates="tenant", cascade="all, delete-orphan")
    members = relationship("TenantMember", back_populates="tenant", cascade="all, delete-orphan")


class Project(Base):
    """Project model for sub-organization within tenants."""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(String(20), default=ProjectStatus.ACTIVE)
    
    # Configuration
    settings = Column(JSON)
    storage_quota_gb = Column(Integer, default=10)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    tenant = relationship("Tenant", back_populates="projects")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")


class TenantMember(Base):
    """Tenant membership model."""
    __tablename__ = "tenant_members"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default=TenantRole.MEMBER)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    invited_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    tenant = relationship("Tenant", back_populates="members")


class ProjectMember(Base):
    """Project membership model."""
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default=ProjectRole.MEMBER)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    added_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    project = relationship("Project", back_populates="members")


# Pydantic Models for API
class TenantBase(BaseModel):
    """Base tenant model."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[dict] = {}
    storage_quota_gb: Optional[int] = Field(100, ge=1, le=10000)
    user_limit: Optional[int] = Field(50, ge=1, le=1000)
    project_limit: Optional[int] = Field(10, ge=1, le=100)

    @validator('slug')
    def validate_slug(cls, v, values):
        if v is None:
            # Generate slug from name
            name = values.get('name', '')
            import re
            v = re.sub(r'[^a-zA-Z0-9-]', '-', name.lower())
            v = re.sub(r'-+', '-', v).strip('-')
        return v


class TenantCreate(TenantBase):
    """Tenant creation model."""
    pass


class TenantUpdate(BaseModel):
    """Tenant update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    settings: Optional[dict] = None
    storage_quota_gb: Optional[int] = Field(None, ge=1, le=10000)
    user_limit: Optional[int] = Field(None, ge=1, le=1000)
    project_limit: Optional[int] = Field(None, ge=1, le=100)
    status: Optional[TenantStatus] = None


class TenantInDB(TenantBase):
    """Tenant model as stored in database."""
    id: int
    status: TenantStatus
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    """Base project model."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[dict] = {}
    storage_quota_gb: Optional[int] = Field(10, ge=1, le=1000)

    @validator('slug')
    def validate_slug(cls, v, values):
        if v is None:
            # Generate slug from name
            name = values.get('name', '')
            import re
            v = re.sub(r'[^a-zA-Z0-9-]', '-', name.lower())
            v = re.sub(r'-+', '-', v).strip('-')
        return v


class ProjectCreate(ProjectBase):
    """Project creation model."""
    tenant_id: int


class ProjectUpdate(BaseModel):
    """Project update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    settings: Optional[dict] = None
    storage_quota_gb: Optional[int] = Field(None, ge=1, le=1000)
    status: Optional[ProjectStatus] = None


class ProjectInDB(ProjectBase):
    """Project model as stored in database."""
    id: int
    tenant_id: int
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


class TenantMemberBase(BaseModel):
    """Base tenant member model."""
    user_id: int
    role: TenantRole = TenantRole.MEMBER


class TenantMemberCreate(TenantMemberBase):
    """Tenant member creation model."""
    tenant_id: int


class TenantMemberUpdate(BaseModel):
    """Tenant member update model."""
    role: TenantRole


class TenantMemberInDB(TenantMemberBase):
    """Tenant member model as stored in database."""
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime
    invited_by: Optional[int] = None

    class Config:
        from_attributes = True


class ProjectMemberBase(BaseModel):
    """Base project member model."""
    user_id: int
    role: ProjectRole = ProjectRole.MEMBER


class ProjectMemberCreate(ProjectMemberBase):
    """Project member creation model."""
    project_id: int


class ProjectMemberUpdate(BaseModel):
    """Project member update model."""
    role: ProjectRole


class ProjectMemberInDB(ProjectMemberBase):
    """Project member model as stored in database."""
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    added_by: Optional[int] = None

    class Config:
        from_attributes = True


# Response Models
class TenantResponse(TenantInDB):
    """Tenant response model."""
    member_count: Optional[int] = 0
    project_count: Optional[int] = 0


class ProjectResponse(ProjectInDB):
    """Project response model."""
    tenant_name: Optional[str] = None
    member_count: Optional[int] = 0


class UserTenantAccess(BaseModel):
    """User tenant access information."""
    tenant_id: int
    tenant_name: str
    tenant_slug: str
    role: TenantRole
    permissions: List[str]


class UserProjectAccess(BaseModel):
    """User project access information."""
    project_id: int
    project_name: str
    project_slug: str
    tenant_id: int
    tenant_name: str
    role: ProjectRole
    permissions: List[str]


class UserContext(BaseModel):
    """Complete user context for multi-tenancy."""
    user_id: int
    username: str
    email: str
    tenants: List[UserTenantAccess]
    projects: List[UserProjectAccess]
    current_tenant: Optional[UserTenantAccess] = None
    current_project: Optional[UserProjectAccess] = None
