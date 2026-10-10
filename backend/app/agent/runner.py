import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.core.config import settings
from app.agent.tools import tool_registry, ToolExecutionResult


class AgentActionLog(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    output: Any
    status: str  # "success" or "failed"


class AgentResponse(BaseModel):
    content: str
    actions_taken: List[AgentActionLog] = []
    mode: str = "mock"


class AgentRunner:
    """Core Agent Execution Engine with Mock Mode and Live LLM dispatching."""

    def __init__(self):
        self.registry = tool_registry

    def process_task(self, user_prompt: str) -> AgentResponse:
        """Process an incoming task, decide whether to call tools, and produce an answer."""
        if settings.MOCK_MODE:
            return self._run_mock_agent(user_prompt)
        else:
            return self._run_live_agent(user_prompt)

    def _run_mock_agent(self, prompt: str) -> AgentResponse:
        """Deterministic, reliable mock agent execution for development, tests, and offline demo."""
        text = prompt.strip()
        actions: List[AgentActionLog] = []

        # 1. Check for Math / Calculation Intent
        # Matches arithmetic patterns like "calculate 25 * 4", "(365*24 - 12)/(365*24) * 100", "what is 50 + 20"
        math_match = re.search(r'(?:calculate|compute|what is|solve)\s*([0-9\.\s\+\-\*\/\(\)\%\^]+)', text, re.IGNORECASE)
        pure_math = re.match(r'^[0-9\.\s\+\-\*\/\(\)\%\^]+$', text)
        
        if math_match or pure_math:
            expr = pure_math.group(0) if pure_math else math_match.group(1)
            # Clean expression
            expr = expr.strip()
            if any(char.isdigit() for char in expr):
                res: ToolExecutionResult = self.registry.execute_tool("safe_calculator", {"expression": expr})
                actions.append(AgentActionLog(
                    tool_name="safe_calculator",
                    arguments={"expression": expr},
                    output=res.output or res.error,
                    status="success" if res.success else "failed"
                ))
                return AgentResponse(
                    content=f"I have evaluated your expression using the Safe Calculator tool.\n\n{res.output or res.error}",
                    actions_taken=actions,
                    mode="mock"
                )

        # 2. Check for Document / Policy Summarization Intent
        # Matches "summarize remote work policy", "summary of incident response", etc.
        doc_patterns = [
            (r'remote\s*work', "remote_work_policy"),
            (r'incident\s*response', "incident_response_playbook"),
            (r'cloud\s*infrastructure|cloud\s*security', "cloud_infrastructure_guide"),
        ]
        for pattern, doc_key in doc_patterns:
            if re.search(pattern, text, re.IGNORECASE) and any(w in text.lower() for w in ["summarize", "summary", "explain", "policy", "guide"]):
                res = self.registry.execute_tool("document_summarizer", {"doc_key": doc_key})
                actions.append(AgentActionLog(
                    tool_name="document_summarizer",
                    arguments={"doc_key": doc_key},
                    output=res.output,
                    status="success" if res.success else "failed"
                ))
                return AgentResponse(
                    content=f"Here is the summary from internal documentation:\n\n{res.output}",
                    actions_taken=actions,
                    mode="mock"
                )

        # 3. Check for Employee / Security Asset Directory Lookup Intent
        # Matches "SEC-101", "lookup Alice", "find record SEC-104", etc.
        rec_match = re.search(r'\b(SEC-\d{3})\b', text, re.IGNORECASE)
        name_match = re.search(r'(?:lookup|find|search for|employee)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)', text, re.IGNORECASE)
        
        if rec_match or (name_match and "record" in text.lower()):
            identifier = rec_match.group(1) if rec_match else name_match.group(1)
            res = self.registry.execute_tool("record_lookup", {"identifier": identifier})
            actions.append(AgentActionLog(
                tool_name="record_lookup",
                arguments={"identifier": identifier},
                output=res.output,
                status="success" if res.success else "failed"
            ))
            return AgentResponse(
                content=f"Directory lookup complete:\n\n{res.output}",
                actions_taken=actions,
                mode="mock"
            )

        # 4. General / Conversational Response
        response_text = (
            f"I have received your request: \"{prompt}\"\n\n"
            "As a secure AI assistant, I operate under strict defensive guardrails. "
            "I can perform safe mathematical computations, summarize authorized enterprise security documents, "
            "or query the directory using controlled tools. How can I assist you with your security tasks today?"
        )
        return AgentResponse(
            content=response_text,
            actions_taken=[],
            mode="mock"
        )

    def _run_live_agent(self, prompt: str) -> AgentResponse:
        """Live LLM API dispatching (used when live LLM credentials are provided)."""
        # Fallback to mock if API key is not configured
        if not settings.OPENAI_API_KEY:
            resp = self._run_mock_agent(prompt)
            resp.content += "\n\n*(Note: Live LLM key not configured; executed in fallback mock mode)*"
            return resp
        
        # Here live API integration can be invoked via httpx/OpenAI
        return self._run_mock_agent(prompt)


# Global Agent Runner instance
agent_runner = AgentRunner()
