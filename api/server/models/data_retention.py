"""
Data retention and versioning models.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class RetentionPolicy(str, Enum):
    """Retention policy enumeration."""
    IMMEDIATE = "immediate"  # Delete immediately
    DAYS_30 = "30_days"
    DAYS_90 = "90_days"
    DAYS_180 = "180_days"
    DAYS_365 = "365_days"
    YEARS_2 = "2_years"
    YEARS_5 = "5_years"
    YEARS_7 = "7_years"
    PERMANENT = "permanent"  # Never delete
    CUSTOM = "custom"  # Custom retention period


class VersionStatus(str, Enum):
    """Version status enumeration."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    CORRUPTED = "corrupted"


class ArchiveStatus(str, Enum):
    """Archive status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# Database Models
class RetentionRule(Base):
    """Data retention rule model."""
    __tablename__ = "retention_rules"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Rule configuration
    name = Column(String(255), nullable=False)
    description = Column(Text)
    resource_type = Column(String(50), nullable=False, index=True)  # entity, signal, score, evidence, etc.
    retention_policy = Column(SQLEnum(RetentionPolicy), nullable=False)
    custom_retention_days = Column(Integer)  # For custom policy
    conditions = Column(JSON)  # Conditions for applying this rule
    
    # Archive configuration
    archive_before_delete = Column(Boolean, default=True)
    archive_location = Column(String(255))  # S3, local, etc.
    compress_archive = Column(Boolean, default=True)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)  # Lower number = higher priority
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    tenant = relationship("Tenant", backref="retention_rules")
    creator = relationship("User", backref="retention_rules_created")
    executions = relationship("RetentionExecution", back_populates="rule", cascade="all, delete-orphan")


class RetentionExecution(Base):
    """Retention rule execution log."""
    __tablename__ = "retention_executions"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("retention_rules.id"), nullable=False)
    
    # Execution details
    execution_type = Column(String(50))  # scheduled, manual, test
    status = Column(String(50))  # running, completed, failed, cancelled
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Results
    items_processed = Column(Integer, default=0)
    items_archived = Column(Integer, default=0)
    items_deleted = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    
    # Error information
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # Metadata
    triggered_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    rule = relationship("RetentionRule", back_populates="executions")
    trigger_user = relationship("User", backref="retention_executions_triggered")


class DataVersion(Base):
    """Data version model for tracking changes."""
    __tablename__ = "data_versions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    
    # Version information
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(255), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    status = Column(SQLEnum(VersionStatus), default=VersionStatus.ACTIVE)
    
    # Data content
    data_content = Column(JSON)
    data_hash = Column(String(64))  # SHA-256 hash
    data_size = Column(Integer)
    
    # Change information
    change_type = Column(String(50))  # create, update, delete, merge
    change_description = Column(Text)
    changed_fields = Column(JSON)  # List of changed fields
    
    # Actor information
    changed_by = Column(Integer, ForeignKey("users.id"))
    changed_at = Column(DateTime, default=datetime.utcnow)
    change_reason = Column(String(255))
    
    # Version relationships
    parent_version_id = Column(Integer, ForeignKey("data_versions.id"))
    merged_from_versions = Column(JSON)  # List of version IDs merged
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # Relationships
    tenant = relationship("Tenant", backref="data_versions")
    project = relationship("Project", backref="data_versions")
    changer = relationship("User", backref="data_versions_changed")
    parent_version = relationship("DataVersion", remote_side=[id])
    attachments = relationship("VersionAttachment", back_populates="version", cascade="all, delete-orphan")


class Archive(Base):
    """Archive model for storing archived data."""
    __tablename__ = "archives"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Archive information
    archive_name = Column(String(255), nullable=False)
    archive_type = Column(String(50))  # full, incremental, differential
    resource_type = Column(String(50))
    resource_ids = Column(JSON)  # List of resource IDs in this archive
    
    # Storage information
    storage_location = Column(String(500))
    storage_path = Column(String(500))
    storage_size = Column(Integer)
    storage_format = Column(String(50))  # zip, tar, gzip, etc.
    compression_ratio = Column(Float)
    
    # Archive status
    status = Column(SQLEnum(ArchiveStatus), default=ArchiveStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    # Content information
    item_count = Column(Integer, default=0)
    checksum = Column(String(64))  # SHA-256 of archive file
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    retention_rule_id = Column(Integer, ForeignKey("retention_rules.id"))
    
    # Relationships
    tenant = relationship("Tenant", backref="archives")
    creator = relationship("User", backref="archives_created")
    retention_rule = relationship("RetentionRule", backref="archives_created")


class VersionAttachment(Base):
    """Version attachment model."""
    __tablename__ = "version_attachments"

    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("data_versions.id"), nullable=False)
    
    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255))
    file_type = Column(String(100))
    file_size = Column(Integer)
    file_path = Column(String(500))
    file_hash = Column(String(64))
    
    # Metadata
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    version = relationship("DataVersion", back_populates="attachments")
    uploader = relationship("User", backref="version_attachments")


# Pydantic Models for API
class RetentionRuleBase(BaseModel):
    """Base retention rule model."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    resource_type: str = Field(..., min_length=1, max_length=50)
    retention_policy: RetentionPolicy
    custom_retention_days: Optional[int] = Field(None, ge=1, le=36500)
    conditions: Optional[Dict[str, Any]] = {}
    archive_before_delete: bool = True
    archive_location: Optional[str] = None
    compress_archive: bool = True
    priority: int = Field(100, ge=1, le=1000)

    @validator('custom_retention_days')
    def validate_custom_retention(cls, v, values):
        if values.get('retention_policy') == RetentionPolicyPolicy.CUSTOM and v is None:
            raise ValueError('custom_retention_days is required for custom retention policy')
        return v


class RetentionRuleCreate(RetentionRuleBase):
    """Retention rule creation model."""
    tenant_id: int


class RetentionRuleUpdate(BaseModel):
    """Retention rule update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    retention_policy: Optional[RetentionPolicy] = None
    custom_retention_days: Optional[int] = Field(None, ge=1, le=36500)
    conditions: Optional[Dict[str, Any]] = None
    archive_before_delete: Optional[bool] = None
    archive_location: Optional[str] = None
    compress_archive: Optional[bool] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=1000)


class RetentionRuleInDB(RetentionRuleBase):
    """Retention rule model as stored in database."""
    id: int
    tenant_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]

    class Config:
        from_attributes = True


class DataVersionBase(BaseModel):
    """Base data version model."""
    resource_type: str = Field(..., min_length=1, max_length=50)
    resource_id: str = Field(..., min_length=1, max_length=255)
    data_content: Optional[Dict[str, Any]] = {}
    change_type: Optional[str] = None
    change_description: Optional[str] = None
    changed_fields: Optional[List[str]] = []
    change_reason: Optional[str] = None
    parent_version_id: Optional[int] = None
    merged_from_versions: Optional[List[int]] = []
    expires_at: Optional[datetime] = None


class DataVersionCreate(DataVersionBase):
    """Data version creation model."""
    tenant_id: int
    project_id: Optional[int] = None


class DataVersionUpdate(BaseModel):
    """Data version update model."""
    status: Optional[VersionStatus] = None
    expires_at: Optional[datetime] = None


class DataVersionInDB(DataVersionBase):
    """Data version model as stored in database."""
    id: int
    tenant_id: int
    project_id: Optional[int]
    version_number: int
    status: VersionStatus
    data_hash: Optional[str]
    data_size: Optional[int]
    changed_by: Optional[int]
    changed_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ArchiveBase(BaseModel):
    """Base archive model."""
    archive_name: str = Field(..., min_length=1, max_length=255)
    archive_type: Optional[str] = "full"
    resource_type: Optional[str] = None
    resource_ids: Optional[List[str]] = []
    storage_location: Optional[str] = None
    storage_format: Optional[str] = "zip"
    expires_at: Optional[datetime] = None


class ArchiveCreate(ArchiveBase):
    """Archive creation model."""
    tenant_id: int


class ArchiveUpdate(BaseModel):
    """Archive update model."""
    status: Optional[ArchiveStatus] = None
    expires_at: Optional[datetime] = None


class ArchiveInDB(ArchiveBase):
    """Archive model as stored in database."""
    id: int
    tenant_id: int
    storage_path: Optional[str]
    storage_size: Optional[int]
    compression_ratio: Optional[float]
    status: ArchiveStatus
    created_at: datetime
    completed_at: Optional[datetime]
    item_count: int
    checksum: Optional[str]
    created_by: Optional[int]
    retention_rule_id: Optional[int]

    class Config:
        from_attributes = True


# Response Models
class RetentionRuleResponse(RetentionRuleInDB):
    """Retention rule response model."""
    creator_username: Optional[str] = None
    execution_count: Optional[int] = 0
    last_execution: Optional[datetime] = None


class RetentionExecutionResponse(BaseModel):
    """Retention execution response model."""
    id: int
    rule_id: int
    rule_name: str
    execution_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    items_processed: int
    items_archived: int
    items_deleted: int
    items_failed: int
    error_message: Optional[str]
    triggered_by_username: Optional[str] = None


class DataVersionResponse(DataVersionInDB):
    """Data version response model."""
    changer_username: Optional[str] = None
    parent_version_number: Optional[int] = None
    attachment_count: Optional[int] = 0


class ArchiveResponse(ArchiveInDB):
    """Archive response model."""
    creator_username: Optional[str] = None
    rule_name: Optional[str] = None


# Search and Filter Models
class RetentionFilter(BaseModel):
    """Retention rule filter model."""
    tenant_id: Optional[int] = None
    resource_type: Optional[str] = None
    retention_policy: Optional[RetentionPolicy] = None
    is_active: Optional[bool] = None
    priority_min: Optional[int] = None
    priority_max: Optional[int] = None


class VersionFilter(BaseModel):
    """Data version filter model."""
    tenant_id: Optional[int] = None
    project_id: Optional[int] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    status: Optional[VersionStatus] = None
    change_type: Optional[str] = None
    changed_by: Optional[int] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class ArchiveFilter(BaseModel):
    """Archive filter model."""
    tenant_id: Optional[int] = None
    archive_type: Optional[str] = None
    resource_type: Optional[str] = None
    status: Optional[ArchiveStatus] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class RetentionAnalysis(BaseModel):
    """Retention analysis model."""
    tenant_id: int
    analysis_date: datetime
    total_items: int
    items_by_policy: Dict[str, int]
    upcoming_deletions: List[Dict[str, Any]]
    storage_usage: Dict[str, Any]
    recommendations: List[str]


class VersionHistory(BaseModel):
    """Version history model."""
    resource_id: str
    resource_type: str
    versions: List[DataVersionResponse]
    current_version: Optional[DataVersionResponse]
    total_versions: int


class StorageReport(BaseModel):
    """Storage usage report model."""
    tenant_id: int
    report_date: datetime
    total_storage_gb: float
    active_data_gb: float
    archived_data_gb: float
    versioned_data_gb: float
    storage_by_type: Dict[str, float]
    growth_trend: List[Dict[str, Any]]
    projected_growth: Dict[str, Any]
