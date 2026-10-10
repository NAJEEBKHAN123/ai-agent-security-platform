import re
import json
from typing import Any, Dict, List, Optional
import httpx
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
    mode: str = "groq"


class AgentRunner:
    """Core Agent Execution Engine with Groq LLM integration and deterministic fallback."""

    def __init__(self):
        self.registry = tool_registry

    def process_task(self, user_prompt: str) -> AgentResponse:
        """Process an incoming task, decide whether to call tools, and generate an LLM response."""
        # 1. Inspect for tool invocation intent
        tool_action = self._detect_and_execute_tool(user_prompt)
        actions = [tool_action] if tool_action else []

        # 2. Check if Groq API is available and enabled
        if settings.GROQ_API_KEY and not settings.MOCK_MODE:
            try:
                llm_response = self._call_groq_llm(user_prompt, tool_action)
                return AgentResponse(
                    content=llm_response,
                    actions_taken=actions,
                    mode=f"groq ({settings.GROQ_MODEL})"
                )
            except Exception as e:
                # Graceful fallback to deterministic engine on network/quota exception
                fallback_resp = self._run_mock_agent(user_prompt, tool_action)
                fallback_resp.content += f"\n\n*(Note: Groq LLM fallback activated: {str(e)})*"
                return fallback_resp

        # 3. Default to deterministic mock engine
        return self._run_mock_agent(user_prompt, tool_action)

    def _detect_and_execute_tool(self, text: str) -> Optional[AgentActionLog]:
        """Detect intent and execute controlled safe tool."""
        # Math / Calculation intent
        math_match = re.search(r'(?:calculate|compute|what is|solve)\s*([0-9\.\s\+\-\*\/\(\)\%\^]+)', text, re.IGNORECASE)
        pure_math = re.match(r'^[0-9\.\s\+\-\*\/\(\)\%\^]+$', text.strip())
        if math_match or pure_math:
            expr = (pure_math.group(0) if pure_math else math_match.group(1)).strip()
            if any(char.isdigit() for char in expr):
                res: ToolExecutionResult = self.registry.execute_tool("safe_calculator", {"expression": expr})
                return AgentActionLog(
                    tool_name="safe_calculator",
                    arguments={"expression": expr},
                    output=res.output or res.error,
                    status="success" if res.success else "failed"
                )

        # Document / Policy Summarization intent
        doc_patterns = [
            (r'remote\s*work', "remote_work_policy"),
            (r'incident\s*response', "incident_response_playbook"),
            (r'cloud\s*infrastructure|cloud\s*security', "cloud_infrastructure_guide"),
        ]
        for pattern, doc_key in doc_patterns:
            if re.search(pattern, text, re.IGNORECASE) and any(w in text.lower() for w in ["summarize", "summary", "explain", "policy", "guide"]):
                res = self.registry.execute_tool("document_summarizer", {"doc_key": doc_key})
                return AgentActionLog(
                    tool_name="document_summarizer",
                    arguments={"doc_key": doc_key},
                    output=res.output,
                    status="success" if res.success else "failed"
                )

        # Employee / Security Asset Directory Lookup intent
        rec_match = re.search(r'\b(SEC-\d{3})\b', text, re.IGNORECASE)
        name_match = re.search(r'(?:lookup|find|search for|employee)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)', text, re.IGNORECASE)
        if rec_match or (name_match and "record" in text.lower()):
            identifier = rec_match.group(1) if rec_match else name_match.group(1)
            res = self.registry.execute_tool("record_lookup", {"identifier": identifier})
            return AgentActionLog(
                tool_name="record_lookup",
                arguments={"identifier": identifier},
                output=res.output,
                status="success" if res.success else "failed"
            )

        return None

    def _call_groq_llm(self, user_prompt: str, tool_action: Optional[AgentActionLog]) -> str:
        """Call Groq API using OpenAI-compatible endpoint."""
        system_instruction = (
            "You are an AI Agent running inside the AI Agent Security Platform. "
            "You operate under strict defensive guardrails. Provide concise, professional, "
            "and accurate answers. If a tool was executed, incorporate its findings seamlessly."
        )

        messages = [
            {"role": "system", "content": system_instruction},
        ]

        if tool_action:
            messages.append({
                "role": "system",
                "content": f"[Tool Execution Result] Tool: {tool_action.tool_name}, Arguments: {tool_action.arguments}, Output: {tool_action.output}"
            })

        messages.append({"role": "user", "content": user_prompt})

        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.GROQ_MODEL,
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.2
        }

        with httpx.Client(timeout=15.0) as client:
            resp = client.post(settings.GROQ_API_URL, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                raise RuntimeError(f"Groq API returned {resp.status_code}: {resp.text}")

    def _run_mock_agent(self, prompt: str, tool_action: Optional[AgentActionLog]) -> AgentResponse:
        """Deterministic fallback responses for local offline evaluation."""
        actions = [tool_action] if tool_action else []
        if tool_action:
            if tool_action.tool_name == "safe_calculator":
                return AgentResponse(
                    content=f"I evaluated your expression using the Safe Calculator tool.\n\n{tool_action.output}",
                    actions_taken=actions,
                    mode="mock"
                )
            elif tool_action.tool_name == "document_summarizer":
                return AgentResponse(
                    content=f"Here is the summary from internal documentation:\n\n{tool_action.output}",
                    actions_taken=actions,
                    mode="mock"
                )
            elif tool_action.tool_name == "record_lookup":
                return AgentResponse(
                    content=f"Directory lookup complete:\n\n{tool_action.output}",
                    actions_taken=actions,
                    mode="mock"
                )

        response_text = (
            f"I have received your request: \"{prompt}\"\n\n"
            "As a secure AI assistant, I operate under strict defensive guardrails. "
            "I can perform safe mathematical computations, summarize authorized enterprise security documents, "
            "or query the directory using controlled tools. How can I assist you with your security tasks today?"
        )
        return AgentResponse(content=response_text, actions_taken=[], mode="mock")


# Global Agent Runner instance
agent_runner = AgentRunner()
