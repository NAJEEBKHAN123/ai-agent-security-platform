import csv
import io
from datetime import datetime, timezone
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role, get_current_user
from app.models.approval import Approval, ApprovalStatus
from app.models.security_event import SecurityEvent, SecurityDecision, RiskLevel
from app.models.user import User, UserRole

router = APIRouter(prefix="/dashboard", tags=["SOC Security Dashboard & Analytics"])


class DashboardStatsResponse(BaseModel):
    total_events: int
    blocked_events: int
    allowed_events: int
    pending_approvals: int
    approved_actions: int
    rejected_actions: int
    block_rate_pct: float
    avg_risk_score: float
    risk_distribution: List[Dict[str, Any]]
    threat_breakdown: List[Dict[str, Any]]
    event_timeline: List[Dict[str, Any]]


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Compute aggregate security telemetry, threat metrics, and SOC risk distributions."""
    # Scope for user: if standard user, compute for user; reviewers/admins see global SOC metrics
    base_query = db.query(SecurityEvent)
    if current_user.role == UserRole.USER:
        base_query = base_query.filter(SecurityEvent.user_id == current_user.id)

    total_events = base_query.count()
    blocked_events = base_query.filter(SecurityEvent.decision == SecurityDecision.BLOCKED).count()
    allowed_events = base_query.filter(SecurityEvent.decision == SecurityDecision.ALLOWED).count()

    # Approvals counts
    pending_approvals = db.query(Approval).filter(Approval.status == ApprovalStatus.PENDING).count()
    approved_actions = db.query(Approval).filter(Approval.status == ApprovalStatus.APPROVED).count()
    rejected_actions = db.query(Approval).filter(Approval.status == ApprovalStatus.REJECTED).count()

    block_rate_pct = round((blocked_events / total_events * 100), 1) if total_events > 0 else 0.0

    # Average risk score
    avg_score_raw = base_query.with_entities(func.avg(SecurityEvent.risk_score)).scalar()
    avg_risk_score = round(float(avg_score_raw), 1) if avg_score_raw is not None else 0.0

    # Risk distribution brackets
    risk_safe = base_query.filter(SecurityEvent.risk_score < 20).count()
    risk_low = base_query.filter(SecurityEvent.risk_score >= 20, SecurityEvent.risk_score < 40).count()
    risk_med = base_query.filter(SecurityEvent.risk_score >= 40, SecurityEvent.risk_score < 70).count()
    risk_high = base_query.filter(SecurityEvent.risk_score >= 70, SecurityEvent.risk_score < 90).count()
    risk_crit = base_query.filter(SecurityEvent.risk_score >= 90).count()

    risk_distribution = [
        {"name": "Safe (0-19)", "count": risk_safe, "color": "#10b981"},
        {"name": "Low (20-39)", "count": risk_low, "color": "#06b6d4"},
        {"name": "Medium (40-69)", "count": risk_med, "color": "#f59e0b"},
        {"name": "High (70-89)", "count": risk_high, "color": "#f97316"},
        {"name": "Critical (90-100)", "count": risk_crit, "color": "#ef4444"},
    ]

    # Threat Categories Breakdown
    prompt_inj_count = base_query.filter(
        SecurityEvent.event_type.like("%prompt_injection%")
    ).count()
    policy_viol_count = base_query.filter(
        SecurityEvent.event_type.like("%tool_policy%")
    ).count()
    data_leak_count = base_query.filter(
        SecurityEvent.event_type.like("%leakage%")
    ).count()
    hitl_count = base_query.filter(
        SecurityEvent.event_type.like("%approval%")
    ).count()

    threat_breakdown = [
        {"category": "Prompt Injection Attacks", "count": prompt_inj_count, "color": "#ef4444"},
        {"category": "Policy Violations (RBAC)", "count": policy_viol_count, "color": "#f97316"},
        {"category": "Data Leakage Redactions", "count": data_leak_count, "color": "#a855f7"},
        {"category": "HITL Approvals Paused", "count": hitl_count, "color": "#eab308"},
    ]

    # Timeline of recent events (last 10 events)
    recent_events = base_query.order_by(SecurityEvent.created_at.asc()).limit(15).all()
    event_timeline = []
    for idx, ev in enumerate(recent_events, 1):
        event_timeline.append({
            "index": idx,
            "id": ev.id,
            "time": ev.created_at.strftime("%H:%M:%S") if ev.created_at else "",
            "risk_score": ev.risk_score,
            "event_type": ev.event_type,
            "decision": ev.decision.value,
        })

    return DashboardStatsResponse(
        total_events=total_events,
        blocked_events=blocked_events,
        allowed_events=allowed_events,
        pending_approvals=pending_approvals,
        approved_actions=approved_actions,
        rejected_actions=rejected_actions,
        block_rate_pct=block_rate_pct,
        avg_risk_score=avg_risk_score,
        risk_distribution=risk_distribution,
        threat_breakdown=threat_breakdown,
        event_timeline=event_timeline,
    )


@router.get("/export")
def export_audit_events_csv(
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_role([UserRole.REVIEWER, UserRole.ADMIN])),
) -> Any:
    """Export platform security audit logs into downloadable CSV format (Reviewers & Admins only)."""
    events = (
        db.query(SecurityEvent, User.email)
        .join(User, SecurityEvent.user_id == User.id)
        .order_by(SecurityEvent.created_at.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Event ID",
        "Timestamp (UTC)",
        "User Email",
        "Event Type",
        "Risk Score",
        "Risk Level",
        "Decision",
        "Reason",
        "Input Snippet",
        "Output Snippet",
    ])

    for ev, user_email in events:
        writer.writerow([
            ev.id,
            ev.created_at.isoformat() if ev.created_at else "",
            user_email,
            ev.event_type,
            ev.risk_score,
            ev.risk_level.value if hasattr(ev.risk_level, "value") else str(ev.risk_level),
            ev.decision.value if hasattr(ev.decision, "value") else str(ev.decision),
            ev.reason,
            ev.input_snippet or "",
            ev.output_snippet or "",
        ])

    output.seek(0)
    filename = f"soc_security_audit_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
