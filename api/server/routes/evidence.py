"""
Evidence logging and approval workflow API routes.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    UploadFile,
    File,
    Form,
    Request,
)
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.evidence import (
    EvidenceCreate,
    EvidenceUpdate,
    EvidenceResponse,
    EvidenceSearch,
    EvidenceFilter,
    ApprovalWorkflowCreate,
    ApprovalWorkflowUpdate,
    ApprovalWorkflowResponse,
    ApprovalStepCreate,
    ApprovalUpdate,
    ApprovalResponse,
    EvidenceAttachmentResponse,
    ComplianceReport,
    AuditTrail,
)
from ..services.evidence_service import EvidenceService
from ..middleware.auth import get_current_user
from ..models.user import User

router = APIRouter(prefix="/evidence", tags=["evidence"])
security = HTTPBearer()


def get_evidence_service(db: Session = Depends(get_db)) -> EvidenceService:
    """Get evidence service instance."""
    return EvidenceService(db)


# Evidence Routes
@router.post("/", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def create_evidence(
    evidence_data: EvidenceCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    evidence_service: EvidenceService = Depends(get_evidence_service),
):
    """Create new evidence entry."""
    # Get client information
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent")

    return await evidence_service.create_evidence(
        evidence_data, current_user.id, client_ip, user_agent
    )


@router.get("/", response_model=List[EvidenceResponse])
async def search_evidence(
    tenant_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    evidence_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    actor_id: Optional[int] = Query(None),
    resource_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    requires_approval: Optional[bool] = Query(None),
    risk_score_min: Optional[int] = Query(None, ge=0, le=100),
    risk_score_max: Optional[int] = Query(None, ge=0, le=100),
    created_after: Optional[datetime] = Query(None),
    created_before: Optional[datetime] = Query(None),
    approved_after: Optional[datetime] = Query(None),
    approved_before: Optional[datetime] = Query(None),
    query: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    evidence_service: EvidenceService = Depends(get_evidence_service),
):
    """Search evidence with filters."""
    # Build search parameters
    filters = EvidenceFilter(
        tenant_id=tenant_id,
        project_id=project_id,
        evidence_type=evidence_type,
        status=status,
        priority=priority,
        category=category,
        actor_id=actor_id,
        resource_type=resource_type,
        action=action,
        tags=tags,
        requires_approval=requires_approval,
        risk_score_min=risk_score_min,
        risk_score_max=risk_score_max,
        created_after=created_after,
        created_before=created_before,
        approved_after=approved_after,
        approved_before=approved_before,
    )

    search_params = EvidenceSearch(
        query=query,
        filters=filters,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    return await evidence_service.search_evidence(search_params, current_user.id)


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: int,
    current_user: User = Depends(get_current_user),
    evidence_service: EvidenceService = Depends(get_evidence_service),
):
    """Get evidence by ID."""
    return await evidence_service.get_evidence(evidence_id)


@router.put("/{evidence_id}", response_model=EvidenceResponse)
async def update_evidence(
    evidence_id: int,
    evidence_data: EvidenceUpdate,
    current_user: User = Depends(get_current_user),
    evidence_service: EvidenceService = Depends(get_evidence_service),
):
    """Update evidence."""
    return await evidence_service.update_evidence(evidence_id, evidence_data, current_user.id)


@router.delete("/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evidence(
    evidence_id: int,
    current_user: User = Depends(get_current_user),
    evidence_service: EvidenceService = Depends(get_evidence_service),
):
    """Delete evidence (soft delete by archiving)."""
    await evidence_service.delete_evidence(evidence_id, current_user.id)


# Approval Workflow Routes
@router.post(
    "/workflows", response_model=ApprovalWorkflowResponse, status_code=status.HTTP_201_CREATED
)
async def create_approval_workflow(
    workflow_data: ApprovalWorkflowCreate,
    current_user: User = Depends(get_current_user),
    evidence_service: EvidenceService = Depends(get_evidence_service),
):
    """Create approval workflow."""
    return await evidence_service.create_approval_workflow(workflow_data, current_user.id)


@router.get("/workflows/{workflow_id}", response_model=ApprovalWorkflowResponse)
async def get_approval_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    evidence_service: EvidenceService = Depends(get_evidence_service),
):
    """Get approval workflow by ID."""
    return await evidence_service.get_approval_workflow(workflow_id)


@router.post("/workflows/{workflow_id}/steps", status_code=status.HTTP_201_CREATED)
async def create_approval_step(
    workflow_id: int,
    step_data: ApprovalStepCreate,
    current_user: User = Depends(get_current_user),
    evidence_service: EvidenceService = Depends(get_evidence_service),
):
    """Create approval step."""
    step_data.workflow_id = workflow_id
    await evidence_service.create_approval_step(step_data, current_user.id)
    return {"message": "Approval step created successfully"}


# Approval Routes
@router.post(
    "/{evidence_id}/approvals", response_model=ApprovalResponse, status_code=status.HTTP_201_CREATED
)
async def create_approval(
    evidence_id: int,
    workflow_id: int,
    step_id: int,
    current_user: User = Depends(get_current_user),
    evidence_service: EvidenceService = Depends(get_evidence_service),
):
    """Create approval request."""
    return await evidence_service.create_approval(
        evidence_id, workflow_id, step_id, current_user.id
    )


@router.put("/approvals/{approval_id}", response_model=ApprovalResponse)
async def update_approval(
    approval_id: int,
    approval_data: ApprovalUpdate,
    current_user: User = Depends(get_current_user),
    evidence_service: EvidenceService = Depends(get_evidence_service),
):
    """Update approval decision."""
    return await evidence_service.update_approval(approval_id, approval_data, current_user.id)


@router.get("/approvals/{approval_id}", response_model=ApprovalResponse)
async def get_approval(
    approval_id: int,
    current_user: User = Depends(get_current_user),
    evidence_service: EvidenceService = Depends(get_evidence_service),
):
    """Get approval by ID."""
    return await evidence_service.get_approval(approval_id)


# Attachment Routes
@router.post(
    "/{evidence_id}/attachments",
    response_model=EvidenceAttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    evidence_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    evidence_service: EvidenceService = Depends(get_evidence_service),
):
    """Upload attachment to evidence."""
    return await evidence_service.upload_attachment(evidence_id, file, current_user.id)


@router.get("/attachments/{attachment_id}", response_model=EvidenceAttachmentResponse)
async def get_attachment(
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    evidence_service: EvidenceService = Depends(get_evidence_service),
):
    """Get attachment by ID."""
    return await evidence_service.get_attachment(attachment_id)


# Compliance and Reporting Routes
@router.get("/reports/compliance", response_model=ComplianceReport)
async def generate_compliance_report(
    tenant_id: int = Query(...),
    project_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    evidence_service: EvidenceService = Depends(get_evidence_service),
):
    """Generate compliance report."""
    return await evidence_service.generate_compliance_report(
        tenant_id, project_id, start_date, end_date
    )


@router.get("/{evidence_id}/audit-trail", response_model=AuditTrail)
async def get_audit_trail(
    evidence_id: int,
    current_user: User = Depends(get_current_user),
    evidence_service: EvidenceService = Depends(get_evidence_service),
):
    """Get complete audit trail for evidence."""
    return await evidence_service.get_audit_trail(evidence_id)
