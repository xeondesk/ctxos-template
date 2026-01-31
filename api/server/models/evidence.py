"""
Evidence logging and approval workflow models.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class EvidenceType(str, Enum):
    """Evidence type enumeration."""

    SYSTEM_ACTION = "system_action"
    USER_ACTION = "user_action"
    DATA_CHANGE = "data_change"
    CONFIG_CHANGE = "config_change"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_CHECK = "compliance_check"
    APPROVAL_REQUEST = "approval_request"
    APPROVAL_DECISION = "approval_decision"
    AUDIT_LOG = "audit_log"


class EvidenceStatus(str, Enum):
    """Evidence status enumeration."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"
    FLAGGED = "flagged"


class ApprovalStatus(str, Enum):
    """Approval status enumeration."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    """Priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Database Models
class Evidence(Base):
    """Evidence log model for audit trail."""

    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)

    # Evidence metadata
    evidence_type = Column(SQLEnum(EvidenceType), nullable=False, index=True)
    status = Column(SQLEnum(EvidenceStatus), default=EvidenceStatus.PENDING, index=True)
    priority = Column(SQLEnum(Priority), default=Priority.MEDIUM, index=True)

    # Event details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100), index=True)
    tags = Column(JSON)  # List of tags

    # Actor information
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    actor_role = Column(String(50))
    actor_ip = Column(String(45))
    actor_user_agent = Column(Text)

    # Resource information
    resource_type = Column(String(50))  # entity, signal, score, config, etc.
    resource_id = Column(String(255))
    resource_data = Column(JSON)  # Before/after state

    # Action details
    action = Column(String(100))
    action_result = Column(String(50))
    action_details = Column(JSON)

    # Compliance and security
    compliance_rules = Column(JSON)  # Applicable compliance rules
    security_flags = Column(JSON)  # Security-related flags
    risk_score = Column(Integer, default=0)  # Risk score 0-100

    # Workflow
    requires_approval = Column(Boolean, default=False)
    approval_workflow_id = Column(Integer, ForeignKey("approval_workflows.id"))
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    approval_notes = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)
    archived_at = Column(DateTime)

    # Relationships
    tenant = relationship("Tenant", backref="evidence")
    project = relationship("Project", backref="evidence")
    actor = relationship("User", foreign_keys=[actor_id], backref="evidence_created")
    approver = relationship("User", foreign_keys=[approved_by], backref="evidence_approved")
    approval_workflow = relationship("ApprovalWorkflow", backref="evidence")
    attachments = relationship(
        "EvidenceAttachment", back_populates="evidence", cascade="all, delete-orphan"
    )


class ApprovalWorkflow(Base):
    """Approval workflow model."""

    __tablename__ = "approval_workflows"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)

    # Workflow configuration
    name = Column(String(255), nullable=False)
    description = Column(Text)
    workflow_type = Column(String(50))  # evidence_type this workflow applies to
    is_active = Column(Boolean, default=True)

    # Approval rules
    min_approvers = Column(Integer, default=1)
    required_roles = Column(JSON)  # List of roles that can approve
    approval_timeout_hours = Column(Integer, default=72)
    auto_approve_conditions = Column(JSON)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    tenant = relationship("Tenant", backref="approval_workflows")
    creator = relationship("User", backref="workflows_created")
    steps = relationship("ApprovalStep", back_populates="workflow", cascade="all, delete-orphan")


class ApprovalStep(Base):
    """Approval step model."""

    __tablename__ = "approval_steps"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("approval_workflows.id"), nullable=False)

    # Step configuration
    step_order = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Approval rules for this step
    approver_type = Column(String(50))  # role, user, group
    approver_config = Column(JSON)  # Specific approvers
    min_approvers = Column(Integer, default=1)
    is_parallel = Column(Boolean, default=False)  # Can approve in parallel

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    workflow = relationship("ApprovalWorkflow", back_populates="steps")
    approvals = relationship("Approval", back_populates="step", cascade="all, delete-orphan")


class Approval(Base):
    """Individual approval record."""

    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False)
    workflow_id = Column(Integer, ForeignKey("approval_workflows.id"), nullable=False)
    step_id = Column(Integer, ForeignKey("approval_steps.id"), nullable=False)

    # Approval details
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING)
    decision = Column(String(20))  # approve, reject, abstain
    comments = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime)

    # Relationships
    evidence = relationship("Evidence", backref="approvals")
    workflow = relationship("ApprovalWorkflow", backref="approvals")
    step = relationship("ApprovalStep", back_populates="approvals")
    approver = relationship("User", backref="approvals_made")


class EvidenceAttachment(Base):
    """Evidence attachment model."""

    __tablename__ = "evidence_attachments"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False)

    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255))
    file_type = Column(String(100))
    file_size = Column(Integer)
    file_path = Column(String(500))
    file_hash = Column(String(64))  # SHA-256 hash

    # Metadata
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    evidence = relationship("Evidence", back_populates="attachments")
    uploader = relationship("User", backref="evidence_attachments")


# Pydantic Models for API
class EvidenceBase(BaseModel):
    """Base evidence model."""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = []
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_data: Optional[Dict[str, Any]] = {}
    action: Optional[str] = None
    action_result: Optional[str] = None
    action_details: Optional[Dict[str, Any]] = {}
    compliance_rules: Optional[List[str]] = []
    security_flags: Optional[Dict[str, Any]] = {}
    risk_score: Optional[int] = Field(0, ge=0, le=100)
    requires_approval: Optional[bool] = False


class EvidenceCreate(EvidenceBase):
    """Evidence creation model."""

    evidence_type: EvidenceType
    tenant_id: int
    project_id: Optional[int] = None
    priority: Priority = Priority.MEDIUM


class EvidenceUpdate(BaseModel):
    """Evidence update model."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[EvidenceStatus] = None
    priority: Optional[Priority] = None
    risk_score: Optional[int] = Field(None, ge=0, le=100)
    approval_notes: Optional[str] = None


class EvidenceInDB(EvidenceBase):
    """Evidence model as stored in database."""

    id: int
    evidence_type: EvidenceType
    tenant_id: int
    project_id: Optional[int]
    status: EvidenceStatus
    priority: Priority
    actor_id: int
    actor_role: Optional[str]
    actor_ip: Optional[str]
    actor_user_agent: Optional[str]
    requires_approval: bool
    approval_workflow_id: Optional[int]
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    approval_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    archived_at: Optional[datetime]

    class Config:
        from_attributes = True


class ApprovalWorkflowBase(BaseModel):
    """Base approval workflow model."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    workflow_type: Optional[str] = None
    is_active: bool = True
    min_approvers: int = Field(1, ge=1, le=10)
    required_roles: Optional[List[str]] = []
    approval_timeout_hours: int = Field(72, ge=1, le=168)
    auto_approve_conditions: Optional[Dict[str, Any]] = {}


class ApprovalWorkflowCreate(ApprovalWorkflowBase):
    """Approval workflow creation model."""

    tenant_id: int


class ApprovalWorkflowUpdate(BaseModel):
    """Approval workflow update model."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    workflow_type: Optional[str] = None
    is_active: Optional[bool] = None
    min_approvers: Optional[int] = Field(None, ge=1, le=10)
    required_roles: Optional[List[str]] = None
    approval_timeout_hours: Optional[int] = Field(None, ge=1, le=168)
    auto_approve_conditions: Optional[Dict[str, Any]] = None


class ApprovalWorkflowInDB(ApprovalWorkflowBase):
    """Approval workflow model as stored in database."""

    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]

    class Config:
        from_attributes = True


class ApprovalStepBase(BaseModel):
    """Base approval step model."""

    step_order: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    approver_type: str = Field(..., min_length=1, max_length=50)
    approver_config: Dict[str, Any] = {}
    min_approvers: int = Field(1, ge=1, le=10)
    is_parallel: bool = False


class ApprovalStepCreate(ApprovalStepBase):
    """Approval step creation model."""

    workflow_id: int


class ApprovalStepInDB(ApprovalStepBase):
    """Approval step model as stored in database."""

    id: int
    workflow_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ApprovalBase(BaseModel):
    """Base approval model."""

    decision: Optional[str] = Field(None, regex="^(approve|reject|abstain)$")
    comments: Optional[str] = None


class ApprovalCreate(ApprovalBase):
    """Approval creation model."""

    evidence_id: int
    workflow_id: int
    step_id: int


class ApprovalUpdate(BaseModel):
    """Approval update model."""

    decision: str = Field(..., regex="^(approve|reject|abstain)$")
    comments: Optional[str] = None


class ApprovalInDB(ApprovalBase):
    """Approval model as stored in database."""

    id: int
    evidence_id: int
    workflow_id: int
    step_id: int
    approver_id: int
    status: ApprovalStatus
    created_at: datetime
    decided_at: Optional[datetime]

    class Config:
        from_attributes = True


class EvidenceAttachmentBase(BaseModel):
    """Base evidence attachment model."""

    filename: str = Field(..., min_length=1, max_length=255)
    original_filename: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    file_path: Optional[str] = None
    file_hash: Optional[str] = None


class EvidenceAttachmentCreate(EvidenceAttachmentBase):
    """Evidence attachment creation model."""

    evidence_id: int


class EvidenceAttachmentInDB(EvidenceAttachmentBase):
    """Evidence attachment model as stored in database."""

    id: int
    evidence_id: int
    uploaded_by: Optional[int]
    uploaded_at: datetime

    class Config:
        from_attributes = True


# Response Models
class EvidenceResponse(EvidenceInDB):
    """Evidence response model."""

    actor_username: Optional[str] = None
    approver_username: Optional[str] = None
    workflow_name: Optional[str] = None
    attachment_count: Optional[int] = 0
    approval_count: Optional[int] = 0


class ApprovalWorkflowResponse(ApprovalWorkflowInDB):
    """Approval workflow response model."""

    creator_username: Optional[str] = None
    step_count: Optional[int] = 0
    evidence_count: Optional[int] = 0


class ApprovalStepResponse(ApprovalStepInDB):
    """Approval step response model."""

    workflow_name: Optional[str] = None
    approval_count: Optional[int] = 0


class ApprovalResponse(ApprovalInDB):
    """Approval response model."""

    approver_username: Optional[str] = None
    evidence_title: Optional[str] = None
    workflow_name: Optional[str] = None
    step_name: Optional[str] = None


class EvidenceAttachmentResponse(EvidenceAttachmentInDB):
    """Evidence attachment response model."""

    uploader_username: Optional[str] = None
    evidence_title: Optional[str] = None


# Search and Filter Models
class EvidenceFilter(BaseModel):
    """Evidence filter model."""

    tenant_id: Optional[int] = None
    project_id: Optional[int] = None
    evidence_type: Optional[EvidenceType] = None
    status: Optional[EvidenceStatus] = None
    priority: Optional[Priority] = None
    category: Optional[str] = None
    actor_id: Optional[int] = None
    resource_type: Optional[str] = None
    action: Optional[str] = None
    tags: Optional[List[str]] = None
    requires_approval: Optional[bool] = None
    risk_score_min: Optional[int] = Field(None, ge=0, le=100)
    risk_score_max: Optional[int] = Field(None, ge=0, le=100)
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    approved_after: Optional[datetime] = None
    approved_before: Optional[datetime] = None


class EvidenceSearch(BaseModel):
    """Evidence search model."""

    query: Optional[str] = None
    filters: Optional[EvidenceFilter] = EvidenceFilter()
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=100)


class ComplianceReport(BaseModel):
    """Compliance report model."""

    tenant_id: int
    project_id: Optional[int] = None
    report_period: Dict[str, datetime]
    total_evidence: int
    approved_evidence: int
    rejected_evidence: int
    pending_evidence: int
    high_risk_evidence: int
    compliance_score: float  # 0-100
    violations: List[Dict[str, Any]]
    recommendations: List[str]


class AuditTrail(BaseModel):
    """Audit trail model."""

    evidence_id: int
    event_history: List[Dict[str, Any]]
    approval_history: List[Dict[str, Any]]
    attachment_history: List[Dict[str, Any]]
    compliance_checks: List[Dict[str, Any]]
