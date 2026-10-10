import re
import enum
from typing import List
from pydantic import BaseModel


class ThreatCategory(str, enum.Enum):
    DIRECT_INJECTION = "Direct Instruction Override"
    JAILBREAK_OVERRIDE = "Jailbreak & Persona Hijack"
    SECRET_EXTRACTION = "Confidential & System Prompt Extraction"
    DELIMITER_MANIPULATION = "Indirect Delimiter & System Tag Injection"
    UNSAFE_TOOL_COERCION = "Unsafe Tool Coercion & Probing"


class IndicatorMatch(BaseModel):
    category: ThreatCategory
    pattern_name: str
    matched_text: str
    weight: float
    description: str


class DetectionResult(BaseModel):
    is_flagged: bool
    indicators: List[IndicatorMatch]
    total_threat_weight: float
    summary: str


# Documented Regex Heuristics for Prompt Injection Detection
_DETECTION_RULES = [
    # 1. Direct Instruction Overrides (Highest Severity)
    {
        "category": ThreatCategory.DIRECT_INJECTION,
        "name": "instruction_override_disregard",
        "pattern": r"(?:ignore|disregard|forget|override|bypass|neglect)\s+(?:all\s+)?(?:previous|prior|above|former|initial|system)\s+(?:instructions|prompts|rules|directives|guidelines|orders)",
        "weight": 55.0,
        "description": "Detected explicit command instructing agent to ignore system directives.",
    },
    {
        "category": ThreatCategory.DIRECT_INJECTION,
        "name": "new_instruction_imposition",
        "pattern": r"(?:from\s+now\s+on|starting\s+now|new\s+rule|your\s+new\s+task\s+is\s+to)\s+(?:ignore|disregard|do\s+not\s+follow|bypass)",
        "weight": 50.0,
        "description": "Detected attempt to overwrite foundational agent instructions.",
    },

    # 2. Jailbreak & Persona Hijacks
    {
        "category": ThreatCategory.JAILBREAK_OVERRIDE,
        "name": "jailbreak_dan_developer_mode",
        "pattern": r"\b(?:DAN\s+mode|Developer\s+Mode|God\s+Mode|Jailbreak(?:ed)?|unfiltered\s+mode|unrestricted\s+mode)\b",
        "weight": 60.0,
        "description": "Detected known adversarial jailbreak persona (DAN / Developer Mode).",
    },
    {
        "category": ThreatCategory.JAILBREAK_OVERRIDE,
        "name": "safety_filter_disable_coercion",
        "pattern": r"(?:disable|deactivate|turn\s+off|bypass)\s+(?:all\s+)?(?:your\s+)?(?:safety|content|security|ethics)\s+(?:filters|protocols|rules|guidelines)",
        "weight": 50.0,
        "description": "Detected coercion attempting to disable AI security guardrails.",
    },

    # 3. Confidential & System Prompt Extraction
    {
        "category": ThreatCategory.SECRET_EXTRACTION,
        "name": "system_prompt_leak_request",
        "pattern": r"(?:reveal|show|print|display|tell\s+me|output|repeat|disclose)\s+(?:all\s+)?(?:your\s+)?(?:(?:hidden|internal|system|developer|confidential|secret)\s*){1,3}(?:prompt|instructions|rules|guidelines|directives)",
        "weight": 45.0,
        "description": "Detected request attempting to leak internal system prompt or instructions.",
    },
    {
        "category": ThreatCategory.SECRET_EXTRACTION,
        "name": "secret_credentials_extraction",
        "pattern": r"(?:reveal|disclose|show|leak|output)\s+(?:all\s+)?(?:secret|credentials|api\s*key|access\s*token|password|confidential\s+data)",
        "weight": 50.0,
        "description": "Detected attempt to extract credentials, API keys, or confidential secrets.",
    },

    # 4. Delimiter & Indirect System Tag Manipulation
    {
        "category": ThreatCategory.DELIMITER_MANIPULATION,
        "name": "fake_system_delimiter_tag",
        "pattern": r"(?:###\s*(?:system|instruction|admin)|<system>|\[SYSTEM\s+INSTRUCTION\]|role:\s*system|\"role\":\s*\"system\")",
        "weight": 40.0,
        "description": "Detected adversarial structural markup masquerading as authoritative system role.",
    },
    {
        "category": ThreatCategory.DELIMITER_MANIPULATION,
        "name": "hidden_markdown_injection",
        "pattern": r"<!--\s*(?:ignore|system|instruction|bypass).*?-->",
        "weight": 35.0,
        "description": "Detected hidden comment injection attempting indirect prompt manipulation.",
    },

    # 5. Unsafe Tool Coercion & Probing
    {
        "category": ThreatCategory.UNSAFE_TOOL_COERCION,
        "name": "arbitrary_code_injection_probing",
        "pattern": r"(?:__import__|eval\(|exec\(|os\.system|subprocess|shutil|cat\s+/etc/passwd|DROP\s+TABLE)",
        "weight": 65.0,
        "description": "Detected code injection or arbitrary shell command payload.",
    },
]


class PromptInjectionDetector:
    """Security inspection engine identifying direct and indirect prompt injection attempts."""

    def __init__(self):
        self.rules = _DETECTION_RULES

    def inspect_input(self, text: str) -> DetectionResult:
        """Analyze text against adversarial heuristics and return structured threat indicators."""
        clean_text = text.strip()
        matched_indicators: List[IndicatorMatch] = []
        total_weight = 0.0

        for rule in self.rules:
            pattern = re.compile(rule["pattern"], re.IGNORECASE | re.MULTILINE)
            match = pattern.search(clean_text)
            if match:
                matched_snippet = match.group(0)[:60]
                matched_indicators.append(
                    IndicatorMatch(
                        category=rule["category"],
                        pattern_name=rule["name"],
                        matched_text=matched_snippet,
                        weight=rule["weight"],
                        description=rule["description"],
                    )
                )
                total_weight += rule["weight"]

        # Flagged if any threat indicator matched
        is_flagged = len(matched_indicators) > 0

        summary = (
            f"Flagged {len(matched_indicators)} threat indicator(s)"
            if is_flagged
            else "No suspicious prompt injection patterns detected"
        )

        return DetectionResult(
            is_flagged=is_flagged,
            indicators=matched_indicators,
            total_threat_weight=total_weight,
            summary=summary,
        )


# Global Detector Instance
injection_detector = PromptInjectionDetector()
