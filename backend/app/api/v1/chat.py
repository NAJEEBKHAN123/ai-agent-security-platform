from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, ToolInvocationSchema
from app.agent.runner import agent_runner
from app.agent.tools import tool_registry, ToolDefinition

router = APIRouter(prefix="/chat", tags=["Agent Chat"])


@router.post("", response_model=ChatResponse)
def execute_agent_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Execute an AI agent task with controlled safe tools."""
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
    )


@router.get("/tools", response_model=List[ToolDefinition])
def list_available_agent_tools(
    current_user: User = Depends(get_current_user)
) -> Any:
    """List all safe tools available to the controlled AI agent."""
    return tool_registry.get_definitions()
