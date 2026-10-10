from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000, description="The user task or query for the AI agent")
    session_id: Optional[str] = Field(default=None, description="Optional conversational session identifier")


class ToolInvocationSchema(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    output: Any
    status: str


class ChatResponse(BaseModel):
    response: str
    tools_invoked: List[ToolInvocationSchema] = []
    model_mode: str = "mock"
    user_email: str
    # Security Inspection & Risk Scoring Metadata (Modules 2 & 3)
    risk_score: float = 0.0
    risk_level: str = "Safe"
    decision: str = "Allowed"
    blocked: bool = False
    threat_reasons: List[str] = []
    score_breakdown: List[str] = []
    event_id: Optional[int] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
