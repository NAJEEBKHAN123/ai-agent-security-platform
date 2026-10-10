import re
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.agent.tools import tool_registry, ToolExecutionResult
from app.security.policy_engine import policy_engine, PolicyDecision
from app.security.output_scanner import output_scanner, OutputScanResult, LeakIndicator


class AgentActionLog(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    output: Any
    status: str  # "success", "failed", "blocked_by_policy"
    policy_reason: Optional[str] = None


class AgentResponse(BaseModel):
    content: str
    actions_taken: List[AgentActionLog] = []
    mode: str = "groq"
    output_redacted: bool = False
    leaks_detected: List[LeakIndicator] = []


class AgentRunner:
    """Core Agent Execution Engine with Policy Enforcement, Output Sanitization, and LLM dispatching."""

    def __init__(self):
        self.registry = tool_registry

    def process_task(
        self,
        user_prompt: str,
        user: Optional[User] = None,
        db: Optional[Session] = None
    ) -> AgentResponse:
        """Process an incoming task through backend tool policies, LLM generation, and output scanning."""
        # 1. Inspect for tool invocation intent and enforce RBAC policies
        tool_action = self._detect_and_execute_tool(user_prompt, user, db)
        actions = [tool_action] if tool_action else []

        raw_content = ""

        # 2. Generate response via Groq or fallback to deterministic engine
        if settings.GROQ_API_KEY and not settings.MOCK_MODE:
            try:
                raw_content = self._call_groq_llm(user_prompt, tool_action)
                mode_str = f"groq ({settings.GROQ_MODEL})"
            except Exception as e:
                mock_resp = self._run_mock_agent(user_prompt, tool_action)
                raw_content = mock_resp.content + f"\n\n*(Note: Groq LLM fallback activated: {str(e)})*"
                mode_str = "mock_fallback"
        else:
            mock_resp = self._run_mock_agent(user_prompt, tool_action)
            raw_content = mock_resp.content
            mode_str = "mock"

        # 3. Output Security Scanning & Synthetic Secret Redaction (Module 6)
        scan_res: OutputScanResult = output_scanner.scan_and_sanitize(raw_content)

        return AgentResponse(
            content=scan_res.redacted_text,
            actions_taken=actions,
            mode=mode_str,
            output_redacted=scan_res.has_leakage,
            leaks_detected=scan_res.leaks_detected,
        )

    def _detect_and_execute_tool(
        self,
        text: str,
        user: Optional[User],
        db: Optional[Session]
    ) -> Optional[AgentActionLog]:
        """Detect intent, check backend policy permissions, and execute safe tool if authorized."""
        tool_name = None
        args = {}

        # Math / Calculation intent
        math_match = re.search(r'(?:calculate|compute|what is|solve)\s*([0-9\.\s\+\-\*\/\(\)\%\^]+)', text, re.IGNORECASE)
        pure_math = re.match(r'^[0-9\.\s\+\-\*\/\(\)\%\^]+$', text.strip())
        if math_match or pure_math:
            expr = (pure_math.group(0) if pure_math else math_match.group(1)).strip()
            if any(char.isdigit() for char in expr):
                tool_name = "safe_calculator"
                args = {"expression": expr}

        # Document / Policy Summarization intent
        if not tool_name:
            doc_patterns = [
                (r'remote\s*work', "remote_work_policy"),
                (r'incident\s*response', "incident_response_playbook"),
                (r'cloud\s*infrastructure|cloud\s*security', "cloud_infrastructure_guide"),
            ]
            for pattern, doc_key in doc_patterns:
                if re.search(pattern, text, re.IGNORECASE) and any(w in text.lower() for w in ["summarize", "summary", "explain", "policy", "guide"]):
                    tool_name = "document_summarizer"
                    args = {"doc_key": doc_key}
                    break

        # Directory Lookup intent
        if not tool_name:
            rec_match = re.search(r'\b(SEC-\d{3})\b', text, re.IGNORECASE)
            name_match = re.search(r'(?:lookup|find|search for|employee)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)', text, re.IGNORECASE)
            if rec_match or (name_match and "record" in text.lower()):
                identifier = rec_match.group(1) if rec_match else name_match.group(1)
                tool_name = "record_lookup"
                args = {"identifier": identifier}

        if not tool_name:
            return None

        # Backend Policy Permission Check (Module 4)
        if user and db:
            policy_check: PolicyDecision = policy_engine.check_tool_permission(tool_name, user, db)
            if not policy_check.allowed:
                return AgentActionLog(
                    tool_name=tool_name,
                    arguments=args,
                    output=f"🛡️ Action Intercepted: {policy_check.reason}",
                    status="blocked_by_policy",
                    policy_reason=policy_check.reason,
                )

        # Authorized: Execute Tool
        res: ToolExecutionResult = self.registry.execute_tool(tool_name, args)
        return AgentActionLog(
            tool_name=tool_name,
            arguments=args,
            output=res.output or res.error,
            status="success" if res.success else "failed",
            policy_reason="Permitted by RBAC policy",
        )

    def _call_groq_llm(self, user_prompt: str, tool_action: Optional[AgentActionLog]) -> str:
        """Call Groq API using OpenAI-compatible endpoint."""
        system_instruction = (
            "You are an AI Agent running inside the AI Agent Security Platform. "
            "You operate under strict defensive guardrails. Provide concise, professional, "
            "and accurate answers. If a tool was executed or blocked by policy, incorporate the status seamlessly."
        )

        messages = [{"role": "system", "content": system_instruction}]

        if tool_action:
            status_desc = "BLOCKED BY SECURITY POLICY" if tool_action.status == "blocked_by_policy" else "SUCCESS"
            messages.append({
                "role": "system",
                "content": f"[Tool Execution Event] Tool: {tool_action.tool_name}, Status: {status_desc}, Arguments: {tool_action.arguments}, Output: {tool_action.output}"
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
        """Deterministic responses for local offline evaluation."""
        actions = [tool_action] if tool_action else []
        if tool_action:
            if tool_action.status == "blocked_by_policy":
                return AgentResponse(
                    content=(
                        f"🛡️ Action Intercepted by Policy Engine\n\n"
                        f"{tool_action.output}\n\n"
                        f"The requested tool '{tool_action.tool_name}' requires elevated privileges that your role does not possess."
                    ),
                    actions_taken=actions,
                    mode="mock"
                )
            elif tool_action.tool_name == "safe_calculator":
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
