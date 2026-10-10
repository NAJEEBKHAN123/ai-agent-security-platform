from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.security_event import SecurityEvent, RiskLevel, SecurityDecision
from app.security.detector import injection_detector, DetectionResult
from app.security.risk_scorer import risk_scorer, RiskEvaluation


class SecurityPipeline:
    """Unified security perimeter inspecting inputs, estimating risk, and auditing events."""

    def __init__(self):
        self.detector = injection_detector
        self.scorer = risk_scorer

    def inspect_and_evaluate(
        self,
        input_text: str,
        user: User,
        db: Session
    ) -> Tuple[RiskEvaluation, Optional[int]]:
        """Run complete input security inspection and record audit event to database."""
        # 1. Detect suspicious prompt injection patterns
        detection: DetectionResult = self.detector.inspect_input(input_text)

        # 2. Calculate transparent 0–100 risk score and policy decision
        evaluation: RiskEvaluation = self.scorer.evaluate_risk(detection, input_text)

        # 3. Create tamper-evident audit record in database
        event = SecurityEvent(
            user_id=user.id,
            event_type="prompt_inspection",
            risk_score=evaluation.score,
            risk_level=evaluation.level,
            decision=evaluation.decision,
            reason="; ".join(evaluation.reasons[:2]),
            input_snippet=input_text[:200],  # Minimized snippet for audit compliance
            output_snippet="BLOCKED_BY_GUARDRAIL" if evaluation.blocked else None,
        )
        try:
            db.add(event)
            db.commit()
            db.refresh(event)
            event_id = event.id
        except Exception:
            db.rollback()
            event_id = None

        return evaluation, event_id


# Global Security Pipeline instance
security_pipeline = SecurityPipeline()
