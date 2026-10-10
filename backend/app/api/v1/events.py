from datetime import datetime
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.security_event import SecurityEvent, RiskLevel, SecurityDecision
from app.models.user import User

router = APIRouter(prefix="/events", tags=["Security Events & Audit Logs"])


class SecurityEventResponse(BaseModel):
    id: int
    user_id: int
    user_email: Optional[str] = None
    event_type: str
    risk_score: float
    risk_level: RiskLevel
    decision: SecurityDecision
    reason: str
    input_snippet: Optional[str] = None
    output_snippet: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


@router.get("", response_model=List[SecurityEventResponse])
def get_security_audit_events(
    limit: int = Query(default=50, le=200),
    risk_level: Optional[str] = Query(default=None),
    decision: Optional[str] = Query(default=None),
    event_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve filtered security events and audit log history."""
    query = db.query(SecurityEvent, User.email).join(User, SecurityEvent.user_id == User.id)

    # If regular user, only view own audit records; Reviewers and Admins see all
    if current_user.role.value == "user":
        query = query.filter(SecurityEvent.user_id == current_user.id)

    if risk_level:
        query = query.filter(SecurityEvent.risk_level == risk_level)
    if decision:
        query = query.filter(SecurityEvent.decision == decision)
    if event_type:
        query = query.filter(SecurityEvent.event_type == event_type)

    results = query.order_by(SecurityEvent.created_at.desc()).limit(limit).all()

    formatted = []
    for event, user_email in results:
        formatted.append(
            SecurityEventResponse(
                id=event.id,
                user_id=event.user_id,
                user_email=user_email,
                event_type=event.event_type,
                risk_score=event.risk_score,
                risk_level=event.risk_level,
                decision=event.decision,
                reason=event.reason,
                input_snippet=event.input_snippet,
                output_snippet=event.output_snippet,
                created_at=event.created_at,
            )
        )
    return formatted
