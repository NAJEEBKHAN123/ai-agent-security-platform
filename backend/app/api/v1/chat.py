from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
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

    # 2. Enforce automated blocking policy on high/critical threats
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
            threat_reasons=evaluation.reasons,
            score_breakdown=evaluation.score_breakdown,
            event_id=event_id,
        )

    # 3. Clean / Permitted request: Dispatch to Agent Runner with Safe Tools
    agent_output = agent_runner.process_task(request.message)

    tool_invocations = [
        ToolInvocationSchema(
            tool_name=action.tool_name,
            arguments=action.arguments,
            output=action.output,
            status=action.status,
        )
        for action in agent_output.actions_taken
    ]

    return ChatResponse(
        response=agent_output.content,
        tools_invoked=tool_invocations,
        model_mode=agent_output.mode,
        user_email=current_user.email,
        risk_score=evaluation.score,
        risk_level=evaluation.level.value,
        decision=evaluation.decision.value,
        blocked=False,
        threat_reasons=evaluation.reasons,
        score_breakdown=evaluation.score_breakdown,
        event_id=event_id,
    )


@router.get("/tools", response_model=List[ToolDefinition])
def list_available_agent_tools(
    current_user: User = Depends(get_current_user)
) -> Any:
    """List all safe tools available to the controlled AI agent."""
    return tool_registry.get_definitions()
