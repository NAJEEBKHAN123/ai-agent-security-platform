import json
from datetime import datetime, timezone
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role
from app.models.approval import Approval, ApprovalStatus
from app.models.security_event import SecurityEvent, SecurityDecision
from app.models.user import User, UserRole
from app.agent.tools import tool_registry

router = APIRouter(prefix="/approvals", tags=["Human Approvals"])


class ApprovalDecisionRequest(BaseModel):
    decision: str  # "approved" or "rejected"
    review_note: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: int
    event_id: int
    action_name: str
    action_payload: Optional[str] = None
    status: ApprovalStatus
    reviewer_id: Optional[int] = None
    review_note: Optional[str] = None
    created_at: datetime
    decided_at: Optional[datetime] = None
    execution_result: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


@router.get("", response_model=List[ApprovalResponse])
def list_approvals(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_role([UserRole.REVIEWER, UserRole.ADMIN]))
) -> Any:
    """List pending or historical human review items (Reviewers & Admins only)."""
    query = db.query(Approval).order_by(Approval.created_at.desc())
    if status_filter:
        query = query.filter(Approval.status == status_filter)
    return query.all()


@router.post("/{approval_id}/decision", response_model=ApprovalResponse)
def submit_approval_decision(
    approval_id: int,
    decision_in: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_role([UserRole.REVIEWER, UserRole.ADMIN]))
) -> Any:
    """Submit approval or rejection decision for a paused sensitive action (Reviewers & Admins only)."""
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval ticket #{approval_id} not found."
        )

    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Approval ticket #{approval_id} has already been decided ({approval.status.value})."
        )

    decision_clean = decision_in.decision.strip().lower()
    if decision_clean not in ["approved", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be either 'approved' or 'rejected'."
        )

    execution_result = None
    approval.reviewer_id = reviewer.id
    approval.review_note = decision_in.review_note or (f"Decision submitted by {reviewer.email}")
    approval.decided_at = datetime.now(timezone.utc)

    # Associated security audit event
    event = db.query(SecurityEvent).filter(SecurityEvent.id == approval.event_id).first()

    if decision_clean == "approved":
        approval.status = ApprovalStatus.APPROVED
        if event:
            event.decision = SecurityDecision.ALLOWED
            event.reason += f" | Approved by Reviewer {reviewer.email}: {approval.review_note}"

        # Execute the approved action safely
        try:
            args = json.loads(approval.action_payload) if approval.action_payload else {}
            res = tool_registry.execute_tool(approval.action_name, args)
            execution_result = str(res.output if res.success else res.error)
        except Exception as e:
            execution_result = f"Error during post-approval execution: {str(e)}"

    else:  # rejected
        approval.status = ApprovalStatus.REJECTED
        if event:
            event.decision = SecurityDecision.BLOCKED
            event.reason += f" | Rejected by Reviewer {reviewer.email}: {approval.review_note}"
        execution_result = "Action denied by security reviewer. Execution permanently blocked."

    db.commit()
    db.refresh(approval)

    return ApprovalResponse(
        id=approval.id,
        event_id=approval.event_id,
        action_name=approval.action_name,
        action_payload=approval.action_payload,
        status=approval.status,
        reviewer_id=approval.reviewer_id,
        review_note=approval.review_note,
        created_at=approval.created_at,
        decided_at=approval.decided_at,
        execution_result=execution_result,
    )
