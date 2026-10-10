import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base


class RiskLevel(str, enum.Enum):
    SAFE = "Safe"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class SecurityDecision(str, enum.Enum):
    ALLOWED = "Allowed"
    BLOCKED = "Blocked"
    PENDING_APPROVAL = "Pending Approval"
    REDACTED = "Redacted"


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)  # prompt_inspection, tool_access, output_scan
    risk_score = Column(Float, nullable=False, default=0.0)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.SAFE, nullable=False)
    decision = Column(Enum(SecurityDecision), default=SecurityDecision.ALLOWED, nullable=False)
    reason = Column(Text, nullable=False)
    input_snippet = Column(Text, nullable=True)   # Redacted/minimized input for auditing
    output_snippet = Column(Text, nullable=True)  # Redacted/minimized output
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="events")
    approvals = relationship("Approval", back_populates="event", cascade="all, delete-orphan")
