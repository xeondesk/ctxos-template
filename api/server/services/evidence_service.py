"""
Evidence logging and approval workflow service.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status, UploadFile, File
import hashlib
import json
import logging

from ..models.evidence import (
    Evidence, ApprovalWorkflow, ApprovalStep, Approval, EvidenceAttachment,
    EvidenceCreate, EvidenceUpdate, EvidenceFilter, EvidenceSearch,
    ApprovalWorkflowCreate, ApprovalWorkflowUpdate,
    ApprovalStepCreate, ApprovalUpdate,
    EvidenceAttachmentCreate,
    EvidenceResponse, ApprovalWorkflowResponse, ApprovalResponse,
    ComplianceReport, AuditTrail,
    EvidenceType, EvidenceStatus, ApprovalStatus, Priority
)
from ..models.user import User

logger = logging.getLogger(__name__)


class EvidenceService:
    """Service for managing evidence and approval workflows."""

    def __init__(self, db: Session):
        self.db = db

    # Evidence Management
    async def create_evidence(self, evidence_data: EvidenceCreate, actor_id: int, 
                           actor_ip: str = None, actor_user_agent: str = None) -> EvidenceResponse:
        """Create new evidence entry."""
        # Check tenant permissions
        await self._check_tenant_permission(evidence_data.tenant_id, actor_id, "evidence:create")

        # Check if approval is required
        approval_workflow_id = None
        if evidence_data.requires_approval:
            approval_workflow_id = await self._get_approval_workflow(
                evidence_data.tenant_id, evidence_data.evidence_type
            )

        # Create evidence
        evidence = Evidence(
            tenant_id=evidence_data.tenant_id,
            project_id=evidence_data.project_id,
            evidence_type=evidence_data.evidence_type,
            title=evidence_data.title,
            description=evidence_data.description,
            category=evidence_data.category,
            tags=evidence_data.tags,
            resource_type=evidence_data.resource_type,
            resource_id=evidence_data.resource_id,
            resource_data=evidence_data.resource_data,
            action=evidence_data.action,
            action_result=evidence_data.action_result,
            action_details=evidence_data.action_details,
            compliance_rules=evidence_data.compliance_rules,
            security_flags=evidence_data.security_flags,
            risk_score=evidence_data.risk_score,
            priority=evidence_data.priority,
            requires_approval=evidence_data.requires_approval,
            approval_workflow_id=approval_workflow_id,
            actor_id=actor_id,
            actor_ip=actor_ip,
            actor_user_agent=actor_user_agent,
            status=EvidenceStatus.PENDING if evidence_data.requires_approval else EvidenceStatus.APPROVED
        )
        
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)

        # Auto-approve if no workflow required
        if evidence_data.requires_approval and not approval_workflow_id:
            evidence.status = EvidenceStatus.APPROVED
            evidence.approved_by = actor_id
            evidence.approved_at = datetime.utcnow()
            self.db.commit()

        return await self.get_evidence(evidence.id)

    async def get_evidence(self, evidence_id: int) -> EvidenceResponse:
        """Get evidence by ID."""
        evidence = self.db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence not found"
            )

        # Get related data
        actor = self.db.query(User).filter(User.id == evidence.actor_id).first()
        approver = None
        if evidence.approved_by:
            approver = self.db.query(User).filter(User.id == evidence.approved_by).first()
        
        workflow = None
        if evidence.approval_workflow_id:
            workflow = self.db.query(ApprovalWorkflow).filter(
                ApprovalWorkflow.id == evidence.approval_workflow_id
            ).first()

        attachment_count = self.db.query(EvidenceAttachment).filter(
            EvidenceAttachment.evidence_id == evidence_id
        ).count()
        
        approval_count = self.db.query(Approval).filter(
            Approval.evidence_id == evidence_id
        ).count()

        return EvidenceResponse(
            id=evidence.id,
            evidence_type=evidence.evidence_type,
            tenant_id=evidence.tenant_id,
            project_id=evidence.project_id,
            title=evidence.title,
            description=evidence.description,
            category=evidence.category,
            tags=evidence.tags,
            resource_type=evidence.resource_type,
            resource_id=evidence.resource_id,
            resource_data=evidence.resource_data,
            action=evidence.action,
            action_result=evidence.action_result,
            action_details=evidence.action_details,
            compliance_rules=evidence.compliance_rules,
            security_flags=evidence.security_flags,
            risk_score=evidence.risk_score,
            priority=evidence.priority,
            status=evidence.status,
            actor_id=evidence.actor_id,
            actor_role=evidence.actor_role,
            actor_ip=evidence.actor_ip,
            actor_user_agent=evidence.actor_user_agent,
            requires_approval=evidence.requires_approval,
            approval_workflow_id=evidence.approval_workflow_id,
            approved_by=evidence.approved_by,
            approved_at=evidence.approved_at,
            approval_notes=evidence.approval_notes,
            created_at=evidence.created_at,
            updated_at=evidence.updated_at,
            expires_at=evidence.expires_at,
            archived_at=evidence.archived_at,
            actor_username=actor.username if actor else None,
            approver_username=approver.username if approver else None,
            workflow_name=workflow.name if workflow else None,
            attachment_count=attachment_count,
            approval_count=approval_count
        )

    async def update_evidence(self, evidence_id: int, evidence_data: EvidenceUpdate, 
                            user_id: int) -> EvidenceResponse:
        """Update evidence."""
        evidence = self.db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence not found"
            )

        # Check permissions
        await self._check_evidence_permission(evidence_id, user_id, "evidence:update")

        # Update fields
        update_data = evidence_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(evidence, field, value)
        
        evidence.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(evidence)

        return await self.get_evidence(evidence_id)

    async def search_evidence(self, search_params: EvidenceSearch, user_id: int) -> List[EvidenceResponse]:
        """Search evidence with filters."""
        # Build query
        query = self.db.query(Evidence)
        
        # Apply tenant filter based on user access
        accessible_tenants = await self._get_user_accessible_tenants(user_id)
        query = query.filter(Evidence.tenant_id.in_(accessible_tenants))

        # Apply search filters
        filters = search_params.filters or EvidenceFilter()
        
        if filters.tenant_id:
            query = query.filter(Evidence.tenant_id == filters.tenant_id)
        
        if filters.project_id:
            query = query.filter(Evidence.project_id == filters.project_id)
        
        if filters.evidence_type:
            query = query.filter(Evidence.evidence_type == filters.evidence_type)
        
        if filters.status:
            query = query.filter(Evidence.status == filters.status)
        
        if filters.priority:
            query = query.filter(Evidence.priority == filters.priority)
        
        if filters.category:
            query = query.filter(Evidence.category == filters.category)
        
        if filters.actor_id:
            query = query.filter(Evidence.actor_id == filters.actor_id)
        
        if filters.resource_type:
            query = query.filter(Evidence.resource_type == filters.resource_type)
        
        if filters.action:
            query = query.filter(Evidence.action == filters.action)
        
        if filters.tags:
            # JSON array search for tags
            for tag in filters.tags:
                query = query.filter(Evidence.tags.contains([tag]))
        
        if filters.requires_approval is not None:
            query = query.filter(Evidence.requires_approval == filters.requires_approval)
        
        if filters.risk_score_min is not None:
            query = query.filter(Evidence.risk_score >= filters.risk_score_min)
        
        if filters.risk_score_max is not None:
            query = query.filter(Evidence.risk_score <= filters.risk_score_max)
        
        if filters.created_after:
            query = query.filter(Evidence.created_at >= filters.created_after)
        
        if filters.created_before:
            query = query.filter(Evidence.created_at <= filters.created_before)
        
        if filters.approved_after:
            query = query.filter(Evidence.approved_at >= filters.approved_after)
        
        if filters.approved_before:
            query = query.filter(Evidence.approved_at <= filters.approved_before)
        
        # Text search
        if search_params.query:
            search_term = f"%{search_params.query}%"
            query = query.filter(
                or_(
                    Evidence.title.ilike(search_term),
                    Evidence.description.ilike(search_term),
                    Evidence.action.ilike(search_term)
                )
            )
        
        # Apply sorting
        sort_column = getattr(Evidence, search_params.sort_by, Evidence.created_at)
        if search_params.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Apply pagination
        offset = (search_params.page - 1) * search_params.page_size
        query = query.offset(offset).limit(search_params.page_size)
        
        # Execute query
        evidence_list = query.all()
        
        # Convert to response models
        result = []
        for evidence in evidence_list:
            result.append(await self.get_evidence(evidence.id))
        
        return result

    async def delete_evidence(self, evidence_id: int, user_id: int) -> bool:
        """Delete evidence (soft delete by archiving)."""
        evidence = self.db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence not found"
            )

        # Check permissions
        await self._check_evidence_permission(evidence_id, user_id, "evidence:delete")

        evidence.status = EvidenceStatus.ARCHIVED
        evidence.archived_at = datetime.utcnow()
        evidence.updated_at = datetime.utcnow()
        self.db.commit()

        return True

    # Approval Workflow Management
    async def create_approval_workflow(self, workflow_data: ApprovalWorkflowCreate, 
                                     creator_id: int) -> ApprovalWorkflowResponse:
        """Create approval workflow."""
        await self._check_tenant_permission(workflow_data.tenant_id, creator_id, "workflow:create")

        workflow = ApprovalWorkflow(
            tenant_id=workflow_data.tenant_id,
            name=workflow_data.name,
            description=workflow_data.description,
            workflow_type=workflow_data.workflow_type,
            is_active=workflow_data.is_active,
            min_approvers=workflow_data.min_approvers,
            required_roles=workflow_data.required_roles,
            approval_timeout_hours=workflow_data.approval_timeout_hours,
            auto_approve_conditions=workflow_data.auto_approve_conditions,
            created_by=creator_id
        )
        
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)

        return await self.get_approval_workflow(workflow.id)

    async def get_approval_workflow(self, workflow_id: int) -> ApprovalWorkflowResponse:
        """Get approval workflow by ID."""
        workflow = self.db.query(ApprovalWorkflow).filter(ApprovalWorkflow.id == workflow_id).first()
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Approval workflow not found"
            )

        # Get related data
        creator = self.db.query(User).filter(User.id == workflow.created_by).first()
        step_count = self.db.query(ApprovalStep).filter(
            ApprovalStep.workflow_id == workflow_id
        ).count()
        
        evidence_count = self.db.query(Evidence).filter(
            Evidence.approval_workflow_id == workflow_id
        ).count()

        return ApprovalWorkflowResponse(
            id=workflow.id,
            tenant_id=workflow.tenant_id,
            name=workflow.name,
            description=workflow.description,
            workflow_type=workflow.workflow_type,
            is_active=workflow.is_active,
            min_approvers=workflow.min_approvers,
            required_roles=workflow.required_roles,
            approval_timeout_hours=workflow.approval_timeout_hours,
            auto_approve_conditions=workflow.auto_approve_conditions,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
            created_by=workflow.created_by,
            creator_username=creator.username if creator else None,
            step_count=step_count,
            evidence_count=evidence_count
        )

    async def create_approval_step(self, step_data: ApprovalStepCreate, creator_id: int) -> bool:
        """Create approval step."""
        # Check workflow permissions
        workflow = self.db.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.id == step_data.workflow_id
        ).first()
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Approval workflow not found"
            )

        await self._check_tenant_permission(workflow.tenant_id, creator_id, "workflow:update")

        step = ApprovalStep(
            workflow_id=step_data.workflow_id,
            step_order=step_data.step_order,
            name=step_data.name,
            description=step_data.description,
            approver_type=step_data.approver_type,
            approver_config=step_data.approver_config,
            min_approvers=step_data.min_approvers,
            is_parallel=step_data.is_parallel
        )
        
        self.db.add(step)
        self.db.commit()

        return True

    # Approval Management
    async def create_approval(self, evidence_id: int, workflow_id: int, 
                            step_id: int, approver_id: int) -> ApprovalResponse:
        """Create approval request."""
        # Check if evidence exists and requires approval
        evidence = self.db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence not found"
            )

        if not evidence.requires_approval:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Evidence does not require approval"
            )

        # Check if user can approve
        await self._check_approval_permission(evidence_id, step_id, approver_id)

        # Check if approval already exists
        existing = self.db.query(Approval).filter(
            and_(
                Approval.evidence_id == evidence_id,
                Approval.step_id == step_id,
                Approval.approver_id == approver_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Approval already exists"
            )

        approval = Approval(
            evidence_id=evidence_id,
            workflow_id=workflow_id,
            step_id=step_id,
            approver_id=approver_id,
            status=ApprovalStatus.PENDING
        )
        
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)

        return await self.get_approval(approval.id)

    async def update_approval(self, approval_id: int, approval_data: ApprovalUpdate, 
                            user_id: int) -> ApprovalResponse:
        """Update approval decision."""
        approval = self.db.query(Approval).filter(Approval.id == approval_id).first()
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Approval not found"
            )

        # Check if user is the approver
        if approval.approver_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the assigned approver can update this approval"
            )

        # Update approval
        approval.decision = approval_data.decision
        approval.comments = approval_data.comments
        approval.status = ApprovalStatus.APPROVED if approval_data.decision == "approve" else ApprovalStatus.REJECTED
        approval.decided_at = datetime.utcnow()
        
        self.db.commit()

        # Check if evidence can be auto-approved/rejected
        await self._process_evidence_approval(approval.evidence_id)

        return await self.get_approval(approval_id)

    async def get_approval(self, approval_id: int) -> ApprovalResponse:
        """Get approval by ID."""
        approval = self.db.query(Approval).filter(Approval.id == approval_id).first()
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Approval not found"
            )

        # Get related data
        approver = self.db.query(User).filter(User.id == approval.approver_id).first()
        evidence = self.db.query(Evidence).filter(Evidence.id == approval.evidence_id).first()
        workflow = self.db.query(ApprovalWorkflow).filter(ApprovalWorkflow.id == approval.workflow_id).first()
        step = self.db.query(ApprovalStep).filter(ApprovalStep.id == approval.step_id).first()

        return ApprovalResponse(
            id=approval.id,
            evidence_id=approval.evidence_id,
            workflow_id=approval.workflow_id,
            step_id=approval.step_id,
            approver_id=approval.approver_id,
            status=approval.status,
            decision=approval.decision,
            comments=approval.comments,
            created_at=approval.created_at,
            decided_at=approval.decided_at,
            approver_username=approver.username if approver else None,
            evidence_title=evidence.title if evidence else None,
            workflow_name=workflow.name if workflow else None,
            step_name=step.name if step else None
        )

    # Attachment Management
    async def upload_attachment(self, evidence_id: int, file: UploadFile, 
                              user_id: int) -> EvidenceAttachmentResponse:
        """Upload attachment to evidence."""
        # Check evidence permissions
        await self._check_evidence_permission(evidence_id, user_id, "evidence:update")

        # Generate file hash
        file_content = await file.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Reset file pointer
        await file.seek(0)

        # Create attachment record
        attachment = EvidenceAttachment(
            evidence_id=evidence_id,
            filename=f"{evidence_id}_{file.filename}",
            original_filename=file.filename,
            file_type=file.content_type,
            file_size=len(file_content),
            file_hash=file_hash,
            uploaded_by=user_id
        )
        
        self.db.add(attachment)
        self.db.commit()
        self.db.refresh(attachment)

        # TODO: Save file to storage (S3, local filesystem, etc.)
        # For now, just store the metadata

        return await self.get_attachment(attachment.id)

    async def get_attachment(self, attachment_id: int) -> EvidenceAttachmentResponse:
        """Get attachment by ID."""
        attachment = self.db.query(EvidenceAttachment).filter(
            EvidenceAttachment.id == attachment_id
        ).first()
        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )

        # Get related data
        uploader = self.db.query(User).filter(User.id == attachment.uploaded_by).first()
        evidence = self.db.query(Evidence).filter(Evidence.id == attachment.evidence_id).first()

        return EvidenceAttachmentResponse(
            id=attachment.id,
            evidence_id=attachment.evidence_id,
            filename=attachment.filename,
            original_filename=attachment.original_filename,
            file_type=attachment.file_type,
            file_size=attachment.file_size,
            file_path=attachment.file_path,
            file_hash=attachment.file_hash,
            uploaded_by=attachment.uploaded_by,
            uploaded_at=attachment.uploaded_at,
            uploader_username=uploader.username if uploader else None,
            evidence_title=evidence.title if evidence else None
        )

    # Compliance and Reporting
    async def generate_compliance_report(self, tenant_id: int, project_id: Optional[int] = None,
                                      start_date: datetime = None, end_date: datetime = None) -> ComplianceReport:
        """Generate compliance report."""
        # Set default date range
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Get evidence statistics
        query = self.db.query(Evidence).filter(
            and_(
                Evidence.tenant_id == tenant_id,
                Evidence.created_at >= start_date,
                Evidence.created_at <= end_date
            )
        )

        if project_id:
            query = query.filter(Evidence.project_id == project_id)

        total_evidence = query.count()
        approved_evidence = query.filter(Evidence.status == EvidenceStatus.APPROVED).count()
        rejected_evidence = query.filter(Evidence.status == EvidenceStatus.REJECTED).count()
        pending_evidence = query.filter(Evidence.status == EvidenceStatus.PENDING).count()
        high_risk_evidence = query.filter(Evidence.risk_score >= 80).count()

        # Calculate compliance score
        if total_evidence > 0:
            compliance_score = (approved_evidence / total_evidence) * 100
        else:
            compliance_score = 100.0

        # Find violations (high risk, rejected, etc.)
        violations = []
        high_risk_items = query.filter(Evidence.risk_score >= 80).all()
        for item in high_risk_items:
            violations.append({
                "evidence_id": item.id,
                "title": item.title,
                "risk_score": item.risk_score,
                "violation_type": "high_risk",
                "description": f"High risk evidence with score {item.risk_score}"
            })

        rejected_items = query.filter(Evidence.status == EvidenceStatus.REJECTED).all()
        for item in rejected_items:
            violations.append({
                "evidence_id": item.id,
                "title": item.title,
                "risk_score": item.risk_score,
                "violation_type": "rejected",
                "description": "Evidence was rejected during approval"
            })

        # Generate recommendations
        recommendations = []
        if pending_evidence > 10:
            recommendations.append("Consider automating approval for low-risk items")
        if high_risk_evidence > 5:
            recommendations.append("Review high-risk evidence handling procedures")
        if compliance_score < 80:
            recommendations.append("Improve approval process efficiency")

        return ComplianceReport(
            tenant_id=tenant_id,
            project_id=project_id,
            report_period={"start": start_date, "end": end_date},
            total_evidence=total_evidence,
            approved_evidence=approved_evidence,
            rejected_evidence=rejected_evidence,
            pending_evidence=pending_evidence,
            high_risk_evidence=high_risk_evidence,
            compliance_score=compliance_score,
            violations=violations,
            recommendations=recommendations
        )

    async def get_audit_trail(self, evidence_id: int) -> AuditTrail:
        """Get complete audit trail for evidence."""
        evidence = self.db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence not found"
            )

        # Get event history
        event_history = [{
            "event": "created",
            "timestamp": evidence.created_at,
            "actor_id": evidence.actor_id,
            "details": {
                "title": evidence.title,
                "evidence_type": evidence.evidence_type,
                "risk_score": evidence.risk_score
            }
        }]

        if evidence.updated_at != evidence.created_at:
            event_history.append({
                "event": "updated",
                "timestamp": evidence.updated_at,
                "details": "Evidence was updated"
            })

        if evidence.approved_at:
            event_history.append({
                "event": "approved",
                "timestamp": evidence.approved_at,
                "actor_id": evidence.approved_by,
                "details": {
                    "notes": evidence.approval_notes
                }
            })

        if evidence.archived_at:
            event_history.append({
                "event": "archived",
                "timestamp": evidence.archived_at,
                "details": "Evidence was archived"
            })

        # Get approval history
        approvals = self.db.query(Approval).filter(
            Approval.evidence_id == evidence_id
        ).all()
        
        approval_history = []
        for approval in approvals:
            approval_history.append({
                "approval_id": approval.id,
                "step_id": approval.step_id,
                "approver_id": approval.approver_id,
                "status": approval.status,
                "decision": approval.decision,
                "comments": approval.comments,
                "created_at": approval.created_at,
                "decided_at": approval.decided_at
            })

        # Get attachment history
        attachments = self.db.query(EvidenceAttachment).filter(
            EvidenceAttachment.evidence_id == evidence_id
        ).all()
        
        attachment_history = []
        for attachment in attachments:
            attachment_history.append({
                "attachment_id": attachment.id,
                "filename": attachment.original_filename,
                "file_size": attachment.file_size,
                "uploaded_by": attachment.uploaded_by,
                "uploaded_at": attachment.uploaded_at
            })

        # Get compliance checks
        compliance_checks = []
        if evidence.compliance_rules:
            for rule in evidence.compliance_rules:
                compliance_checks.append({
                    "rule": rule,
                    "status": "passed" if evidence.status == EvidenceStatus.APPROVED else "failed",
                    "checked_at": evidence.created_at
                })

        return AuditTrail(
            evidence_id=evidence_id,
            event_history=event_history,
            approval_history=approval_history,
            attachment_history=attachment_history,
            compliance_checks=compliance_checks
        )

    # Helper Methods
    async def _check_tenant_permission(self, tenant_id: int, user_id: int, permission: str):
        """Check if user has tenant permission."""
        # This would integrate with the RBAC system
        # For now, just check if user is tenant member
        from ..models.tenant import TenantMember
        member = self.db.query(TenantMember).filter(
            and_(
                TenantMember.tenant_id == tenant_id,
                TenantMember.user_id == user_id
            )
        ).first()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to tenant"
            )

    async def _check_evidence_permission(self, evidence_id: int, user_id: int, permission: str):
        """Check if user has evidence permission."""
        evidence = self.db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence not found"
            )

        await self._check_tenant_permission(evidence.tenant_id, user_id, permission)

    async def _check_approval_permission(self, evidence_id: int, step_id: int, user_id: int):
        """Check if user can approve evidence."""
        evidence = self.db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence not found"
            )

        step = self.db.query(ApprovalStep).filter(ApprovalStep.id == step_id).first()
        if not step:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Approval step not found"
            )

        # Check if user is in approver configuration
        # This would need more sophisticated logic based on approver_type
        await self._check_tenant_permission(evidence.tenant_id, user_id, "approval:create")

    async def _get_approval_workflow(self, tenant_id: int, evidence_type: EvidenceType) -> Optional[int]:
        """Get approval workflow for evidence type."""
        workflow = self.db.query(ApprovalWorkflow).filter(
            and_(
                ApprovalWorkflow.tenant_id == tenant_id,
                ApprovalWorkflow.workflow_type == evidence_type,
                ApprovalWorkflow.is_active == True
            )
        ).first()
        
        return workflow.id if workflow else None

    async def _get_user_accessible_tenants(self, user_id: int) -> List[int]:
        """Get list of tenant IDs accessible to user."""
        from ..models.tenant import TenantMember
        members = self.db.query(TenantMember).filter(
            TenantMember.user_id == user_id
        ).all()
        
        return [member.tenant_id for member in members]

    async def _process_evidence_approval(self, evidence_id: int):
        """Process evidence approval after all approvals are complete."""
        evidence = self.db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            return

        # Get all required approvals
        approvals = self.db.query(Approval).filter(
            Approval.evidence_id == evidence_id
        ).all()

        if not approvals:
            return

        # Check if all approvals are complete
        completed_approvals = [a for a in approvals if a.status in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]]
        
        if len(completed_approvals) != len(approvals):
            return

        # Check if any rejections
        if any(a.status == ApprovalStatus.REJECTED for a in completed_approvals):
            evidence.status = EvidenceStatus.REJECTED
        else:
            evidence.status = EvidenceStatus.APPROVED
            evidence.approved_at = datetime.utcnow()

        self.db.commit()
