import ast
import operator
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]


class ToolExecutionResult(BaseModel):
    tool_name: str
    success: bool
    input_args: Dict[str, Any]
    output: Any
    error: Optional[str] = None


# Safe Math AST Evaluator (Prevents Remote Code Execution - Zero eval())
_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPERATORS:
            raise ValueError(f"Unsupported math operator: {op_type.__name__}")
        left = _safe_eval_node(node.left)
        right = _safe_eval_node(node.right)
        return _SAFE_OPERATORS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _safe_eval_node(node.operand)
        return _SAFE_OPERATORS[op_type](operand)
    else:
        raise ValueError(f"Unsafe expression component detected: {type(node).__name__}")


def safe_calculator(expression: str) -> str:
    """Evaluate a mathematical expression safely without using eval() or exec()."""
    clean_expr = expression.strip()
    try:
        parsed = ast.parse(clean_expr, mode='eval')
        result = _safe_eval_node(parsed.body)
        return f"Result: {round(result, 4) if isinstance(result, float) else result}"
    except Exception as e:
        return f"Calculator error: {str(e)}"


# Sample Synthetic Knowledge Base for Document Summarization
SAMPLE_DOCUMENTS: Dict[str, str] = {
    "remote_work_policy": (
        "Enterprise Remote Work Security Guidelines: All employees working remotely must connect "
        "via company VPN with Multi-Factor Authentication (MFA). Corporate laptops must maintain "
        "disk encryption (FileVault/BitLocker) enabled at all times. Personal USB drives are strictly "
        "prohibited on corporate assets. Suspicious phishing attempts must be reported to the SOC within 15 minutes."
    ),
    "incident_response_playbook": (
        "Cybersecurity Incident Response Playbook: Step 1 - Identification and triage. Step 2 - Isolation of "
        "affected endpoints from the internal network. Step 3 - Forensic evidence capture and memory imaging. "
        "Step 4 - Eradication and credential rotation. Step 5 - Recovery and post-incident lessons learned."
    ),
    "cloud_infrastructure_guide": (
        "Cloud Security Architecture Standards: Production databases must not have public IP addresses. "
        "All secrets must be retrieved at runtime from AWS Secrets Manager or HashiCorp Vault. TLS 1.3 is enforced "
        "across all external API gateways. Role-based least-privilege policies must be reviewed quarterly."
    ),
}


def document_summarizer(doc_key: str) -> str:
    """Retrieve and summarize an approved synthetic enterprise document."""
    key = doc_key.lower().strip().replace(" ", "_")
    for known_key, content in SAMPLE_DOCUMENTS.items():
        if key in known_key or known_key in key:
            summary = content[:200] + "..." if len(content) > 200 else content
            return f"Summary of '{known_key}': {summary}"
    
    available = ", ".join(SAMPLE_DOCUMENTS.keys())
    return f"Document '{doc_key}' not found. Available documents in library: [{available}]"


# Synthetic Employee & Asset Directory
SYNTHETIC_RECORDS: Dict[str, Dict[str, str]] = {
    "SEC-101": {"name": "Alice Chen", "role": "Senior Security Analyst", "department": "SOC Operations", "clearance": "Level 3"},
    "SEC-102": {"name": "Bob Vance", "role": "Cloud Security Architect", "department": "Infrastructure", "clearance": "Level 4"},
    "SEC-103": {"name": "Carol Danvers", "role": "Incident Commander", "department": "Threat Intelligence", "clearance": "Level 5"},
    "SEC-104": {"name": "David Miller", "role": "Compliance Officer", "department": "Governance & Risk", "clearance": "Level 2"},
}


def record_lookup(identifier: str) -> str:
    """Look up a synthetic employee or security asset record by ID or Name."""
    query = identifier.strip().upper()
    for rec_id, data in SYNTHETIC_RECORDS.items():
        if query == rec_id or query in data["name"].upper():
            return (
                f"Record Found [{rec_id}]: Name: {data['name']}, "
                f"Role: {data['role']}, Dept: {data['department']}, Clearance: {data['clearance']}"
            )
    return f"No record matching '{identifier}' was found in the directory."


def credential_rotation(service_name: str) -> str:
    """Rotate credentials for a specified service (High-Impact Operation - Requires Reviewer Approval)."""
    return f"Success: Security credentials for service '{service_name}' have been rotated successfully."


# Tool Registry
class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        self.register_tool(
            name="safe_calculator",
            description="Evaluates arithmetic expressions (addition, subtraction, multiplication, division, exponents).",
            parameters={"expression": "string"},
            handler=safe_calculator
        )
        self.register_tool(
            name="document_summarizer",
            description="Summarizes approved synthetic internal policies (remote_work_policy, incident_response_playbook, cloud_infrastructure_guide).",
            parameters={"doc_key": "string"},
            handler=document_summarizer
        )
        self.register_tool(
            name="record_lookup",
            description="Looks up employee or asset directory records by ID (e.g., SEC-101) or Name.",
            parameters={"identifier": "string"},
            handler=record_lookup
        )
        self.register_tool(
            name="credential_rotation",
            description="Rotates credentials for internal service (Sensitive - Requires Human Approval).",
            parameters={"service_name": "string"},
            handler=credential_rotation
        )

    def register_tool(self, name: str, description: str, parameters: Dict[str, Any], handler: Callable):
        self._tools[name] = {
            "definition": ToolDefinition(name=name, description=description, parameters=parameters),
            "handler": handler,
        }

    def get_definitions(self) -> List[ToolDefinition]:
        return [item["definition"] for item in self._tools.values()]

    def execute_tool(self, name: str, args: Dict[str, Any]) -> ToolExecutionResult:
        if name not in self._tools:
            return ToolExecutionResult(
                tool_name=name,
                success=False,
                input_args=args,
                output=None,
                error=f"Tool '{name}' is not registered."
            )
        handler = self._tools[name]["handler"]
        try:
            output = handler(**args)
            return ToolExecutionResult(
                tool_name=name,
                success=True,
                input_args=args,
                output=output,
                error=None
            )
        except Exception as e:
            return ToolExecutionResult(
                tool_name=name,
                success=False,
                input_args=args,
                output=None,
                error=str(e)
            )


# Global Tool Registry instance
tool_registry = ToolRegistry()
