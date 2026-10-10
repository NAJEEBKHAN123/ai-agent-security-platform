import re
from typing import List, Tuple
from pydantic import BaseModel


class LeakIndicator(BaseModel):
    leak_type: str
    matched_pattern: str
    redacted_as: str
    severity: str


class OutputScanResult(BaseModel):
    has_leakage: bool
    redacted_text: str
    leaks_detected: List[LeakIndicator]
    summary: str


# RegEx Patterns for Sensitive Data Leakage & Synthetic Secrets
_SENSITIVE_PATTERNS = [
    # 1. Synthetic Demo Secrets (Mandatory Requirement from Project Guide)
    {
        "type": "Synthetic Secret",
        "pattern": r"\b(?:DEMO_SECRET_\w+|FAKE_KEY_\w+|TEST_API_KEY_\w+|TEST_SECRET_\w+)\b",
        "redacted_as": "[REDACTED_SECRET: Synthetic Key]",
        "severity": "High",
    },

    # 2. AWS Access Key Identifiers
    {
        "type": "Cloud Credential (AWS)",
        "pattern": r"\bAKIA[0-9A-Z]{16}\b",
        "redacted_as": "[REDACTED_CREDENTIAL: AWS Access Key]",
        "severity": "Critical",
    },

    # 3. Generic API Keys & Secret Tokens
    {
        "type": "API Token / Secret Key",
        "pattern": r"(?:api[_-]?key|secret[_-]?key|auth[_-]?token|bearer)\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{20,})['\"]?",
        "redacted_as": "[REDACTED_CREDENTIAL: API Token]",
        "severity": "High",
    },

    # 4. Cryptographic Private Keys
    {
        "type": "Cryptographic Private Key",
        "pattern": r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----(?:[\s\S]*?-----END (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----)?",
        "redacted_as": "[REDACTED_KEY: Private Key Block]",
        "severity": "Critical",
    },

    # 5. Simulated Credit Card Numbers
    {
        "type": "Payment Card Data (PCI-DSS)",
        "pattern": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b",
        "redacted_as": "[REDACTED_PII: Payment Card]",
        "severity": "High",
    },
]


class OutputSecurityScanner:
    """Detects and redacts synthetic secrets and sensitive credential patterns in agent output."""

    def __init__(self):
        self.rules = _SENSITIVE_PATTERNS

    def scan_and_sanitize(self, text: str) -> OutputScanResult:
        """Scan text for sensitive patterns and automatically redact any matches."""
        sanitized_text = text
        detected_leaks: List[LeakIndicator] = []

        for rule in self.rules:
            pattern = re.compile(rule["pattern"], re.IGNORECASE)
            matches = list(pattern.finditer(sanitized_text))
            
            if matches:
                for match in matches:
                    matched_str = match.group(0)
                    detected_leaks.append(
                        LeakIndicator(
                            leak_type=rule["type"],
                            matched_pattern=matched_str[:40],
                            redacted_as=rule["redacted_as"],
                            severity=rule["severity"],
                        )
                    )
                # Apply regex substitution to redact all occurrences
                sanitized_text = pattern.sub(rule["redacted_as"], sanitized_text)

        has_leakage = len(detected_leaks) > 0
        summary = (
            f"Detected and redacted {len(detected_leaks)} sensitive data pattern(s)"
            if has_leakage
            else "Output verified clean: No sensitive data leakage detected."
        )

        return OutputScanResult(
            has_leakage=has_leakage,
            redacted_text=sanitized_text,
            leaks_detected=detected_leaks,
            summary=summary,
        )


# Global Output Scanner instance
output_scanner = OutputSecurityScanner()
