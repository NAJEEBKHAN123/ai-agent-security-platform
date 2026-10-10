from typing import List, Tuple
from pydantic import BaseModel
from app.models.security_event import RiskLevel, SecurityDecision
from app.security.detector import DetectionResult, IndicatorMatch


class RiskEvaluation(BaseModel):
    score: float  # 0.0 to 100.0
    level: RiskLevel
    decision: SecurityDecision
    blocked: bool
    reasons: List[str]
    score_breakdown: List[str]


class RiskScoringEngine:
    """Transparent 0–100 mathematical risk scoring and policy decision engine."""

    # Prototype Thresholds (Documented & auditable)
    SAFE_THRESHOLD = 20.0
    LOW_THRESHOLD = 50.0
    MEDIUM_THRESHOLD = 75.0  # Above this, automated blocking occurs
    HIGH_THRESHOLD = 90.0

    def evaluate_risk(self, detection: DetectionResult, input_text: str = "") -> RiskEvaluation:
        """Compute transparent 0–100 score, classify threat level, and make policy decision."""
        reasons: List[str] = []
        breakdown: List[str] = []

        # If clean and unflagged
        if not detection.is_flagged:
            return RiskEvaluation(
                score=0.0,
                level=RiskLevel.SAFE,
                decision=SecurityDecision.ALLOWED,
                blocked=False,
                reasons=["Input verified clean: No adversarial indicators identified."],
                score_breakdown=["Baseline clean score: 0.0 pts"],
            )

        # 1. Accumulate threat indicator weights
        calculated_score = 0.0
        categories_seen = set()

        for ind in detection.indicators:
            calculated_score += ind.weight
            categories_seen.add(ind.category)
            breakdown.append(f"+{ind.weight:.1f} pts: [{ind.category.value}] - '{ind.matched_text}'")
            reasons.append(ind.description)

        # 2. Multi-Vector Attack Synergy Multiplier
        # If an attacker combines multiple attack vectors simultaneously (e.g. override + secret extraction)
        if len(categories_seen) > 1:
            synergy_bonus = (len(categories_seen) - 1) * 10.0
            calculated_score += synergy_bonus
            breakdown.append(f"+{synergy_bonus:.1f} pts: Compound attack penalty ({len(categories_seen)} threat vectors combined)")
            reasons.append(f"Compound attack detected combining {len(categories_seen)} distinct threat vectors.")

        # 3. Normalization (Clamp strictly between 0.0 and 100.0)
        final_score = round(min(100.0, max(0.0, calculated_score)), 1)

        # 4. Map to Standard Prototype Risk Categories
        if final_score < self.SAFE_THRESHOLD:
            level = RiskLevel.SAFE
            decision = SecurityDecision.ALLOWED
            blocked = False
        elif final_score < self.LOW_THRESHOLD:
            level = RiskLevel.LOW
            decision = SecurityDecision.ALLOWED
            blocked = False
        elif final_score < self.MEDIUM_THRESHOLD:
            level = RiskLevel.MEDIUM
            decision = SecurityDecision.ALLOWED
            blocked = False
        elif final_score < self.HIGH_THRESHOLD:
            level = RiskLevel.HIGH
            decision = SecurityDecision.BLOCKED
            blocked = True
            reasons.insert(0, f"BLOCKED: High-risk prompt injection attempt detected (Score: {final_score}/100).")
        else:
            level = RiskLevel.CRITICAL
            decision = SecurityDecision.BLOCKED
            blocked = True
            reasons.insert(0, f"BLOCKED: Critical security threat detected (Score: {final_score}/100).")

        return RiskEvaluation(
            score=final_score,
            level=level,
            decision=decision,
            blocked=blocked,
            reasons=reasons,
            score_breakdown=breakdown,
        )


# Global Risk Scorer instance
risk_scorer = RiskScoringEngine()
