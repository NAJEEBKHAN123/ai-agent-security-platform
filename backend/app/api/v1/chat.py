from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.security_event import SecurityEvent, RiskLevel, SecurityDecision
from app.schemas.chat import ChatRequest, ChatResponse, ToolInvocationSchema
from app.agent.runner import agent_runner
from app.agent.tools import tool_registry, ToolDefinition
from app.security.pipeline import security_pipeline

router = APIRouter(prefix="/chat", tags=["Agent Chat"])


@router.post("", response_model=ChatResponse)
def execute_agent_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Execute an AI agent task through the defensive security perimeter."""
    # 1. Defensively inspect input and calculate transparent risk score
    evaluation, event_id = security_pipeline.inspect_and_evaluate(
        input_text=request.message,
        user=current_user,
        db=db
    )

    # 2. Enforce automated blocking policy on high/critical threats (Module 2 & 3)
    if evaluation.blocked:
        defensive_warning = (
            f"🛡️ SECURITY GUARDRAIL TRIGGERED\n\n"
            f"Your request was intercepted and BLOCKED by the security perimeter before reaching the agent.\n\n"
            f"• Threat Classification: {evaluation.level.value} (Risk Score: {evaluation.score}/100)\n"
            f"• Primary Reason: {evaluation.reasons[0] if evaluation.reasons else 'Malicious payload signature'}\n\n"
            f"Audit Event ID #{event_id} has been logged in the security operations database."
        )

        return ChatResponse(
            response=defensive_warning,
            tools_invoked=[],
            model_mode="security_guardrail_intercept",
            user_email=current_user.email,
            risk_score=evaluation.score,
            risk_level=evaluation.level.value,
            decision=evaluation.decision.value,
            blocked=True,
            output_redacted=False,
            threat_reasons=evaluation.reasons,
            score_breakdown=evaluation.score_breakdown,
            event_id=event_id,
        )

    # 3. Clean / Permitted request: Dispatch to Agent Runner with Policy Enforcement & Output Scanner
    agent_output = agent_runner.process_task(request.message, user=current_user, db=db)

    # Check if any tool action was blocked by policy (Module 4)
    tool_blocked = False
    policy_violation_reason = ""
    tool_invocations = []

    for action in agent_output.actions_taken:
        tool_invocations.append(
            ToolInvocationSchema(
                tool_name=action.tool_name,
                arguments=action.arguments,
                output=action.output,
                status=action.status,
            )
        )
        if action.status == "blocked_by_policy":
            tool_blocked = True
            policy_violation_reason = action.policy_reason or "Unauthorized tool execution attempt"

    # If tool was blocked by policy, record a policy violation event in audit database
    if tool_blocked:
        policy_event = SecurityEvent(
            user_id=current_user.id,
            event_type="tool_policy_violation",
            risk_score=75.0,
            risk_level=RiskLevel.HIGH,
            decision=SecurityDecision.BLOCKED,
            reason=f"Blocked unauthorized tool execution: {policy_violation_reason}",
            input_snippet=request.message[:200],
            output_snippet="TOOL_EXECUTION_DENIED",
        )
        try:
            db.add(policy_event)
            db.commit()
            db.refresh(policy_event)
            event_id = policy_event.id
        except Exception:
            db.rollback()

    # If sensitive data was redacted in output (Module 6), record data leakage audit event
    if agent_output.output_redacted:
        leak_event = SecurityEvent(
            user_id=current_user.id,
            event_type="output_data_leakage_redacted",
            risk_score=60.0,
            risk_level=RiskLevel.MEDIUM,
            decision=SecurityDecision.REDACTED,
            reason=f"Output Security Scanner intercepted and redacted sensitive data: {[l.leak_type for l in agent_output.leaks_detected]}",
            input_snippet=request.message[:200],
            output_snippet=agent_output.content[:200],
        )
        try:
            db.add(leak_event)
            db.commit()
            db.refresh(leak_event)
            event_id = leak_event.id
        except Exception:
            db.rollback()

    final_decision = "Blocked" if tool_blocked else ("Redacted" if agent_output.output_redacted else evaluation.decision.value)
    final_reasons = list(evaluation.reasons)
    if tool_blocked:
        final_reasons.insert(0, f"TOOL POLICY BLOCK: {policy_violation_reason}")
    if agent_output.output_redacted:
        final_reasons.insert(0, f"DATA LEAKAGE PREVENTION: Redacted {len(agent_output.leaks_detected)} sensitive pattern(s).")

    return ChatResponse(
        response=agent_output.content,
        tools_invoked=tool_invocations,
        model_mode=agent_output.mode,
        user_email=current_user.email,
        risk_score=75.0 if tool_blocked else evaluation.score,
        risk_level=RiskLevel.HIGH.value if tool_blocked else evaluation.level.value,
        decision=final_decision,
        blocked=tool_blocked,
        output_redacted=agent_output.output_redacted,
        threat_reasons=final_reasons,
        score_breakdown=evaluation.score_breakdown,
        event_id=event_id,
    )


@router.get("/tools", response_model=List[ToolDefinition])
def list_available_agent_tools(
    current_user: User = Depends(get_current_user)
) -> Any:
    """List all safe tools available to the controlled AI agent."""
    return tool_registry.get_definitions()
