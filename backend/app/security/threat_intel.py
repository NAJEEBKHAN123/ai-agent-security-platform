import re
from typing import Dict, List, Optional
from pydantic import BaseModel


class ThreatIntelMatch(BaseModel):
    ioc_type: str  # "domain" | "ip" | "payload_signature"
    indicator: str
    threat_description: str
    severity: str  # "high" | "critical"


# Synthetic Local Threat Intelligence Feed of Known Indicators of Compromise (IOCs)
KNOWN_MALICIOUS_DOMAINS = {
    "c2-exfil.xyz": "Known Command & Control (C2) exfiltration domain",
    "darkweb-leak.net": "Known credential dump dropzone",
    "payload-delivery.top": "Malicious payload hosting infrastructure",
    "evil-attacker.org": "Adversarial prompt injection relay server",
}

KNOWN_MALICIOUS_IPS = {
    "198.51.100.23": "Attacker reconnaissance scanner (TOR exit node)",
    "203.0.113.88": "Active botnet proxy node",
    "192.0.2.144": "Known exfiltration target IP",
}

MALICIOUS_SIGNATURES = [
    (r"\bbase64\s*-d\b", "Base64 decode pipeline (Payload delivery signature)"),
    (r"\bcurl\s+-s\b.*\|\s*sh\b", "Remote script piped to shell (Stager signature)"),
    (r"\bpowershell\s+-enc\b", "Encoded PowerShell invocation (Living-off-the-land signature)"),
]


class ThreatIntelFeed:
    """Enterprise Threat Intelligence Scanner validating inputs and URLs against IOC feeds."""

    def __init__(self):
        self.domains = KNOWN_MALICIOUS_DOMAINS
        self.ips = KNOWN_MALICIOUS_IPS
        self.signatures = MALICIOUS_SIGNATURES

    def scan(self, text: str) -> List[ThreatIntelMatch]:
        """Scan input prompt or payload for matches against IOC database."""
        matches: List[ThreatIntelMatch] = []
        lower_text = text.lower()

        # 1. Domain IOCs
        for domain, desc in self.domains.items():
            if domain in lower_text:
                matches.append(
                    ThreatIntelMatch(
                        ioc_type="domain",
                        indicator=domain,
                        threat_description=desc,
                        severity="high",
                    )
                )

        # 2. IP IOCs
        for ip, desc in self.ips.items():
            if ip in text:
                matches.append(
                    ThreatIntelMatch(
                        ioc_type="ip",
                        indicator=ip,
                        threat_description=desc,
                        severity="critical",
                    )
                )

        # 3. Malicious Command Stagers
        for pattern, desc in self.signatures:
            if re.search(pattern, text, re.IGNORECASE):
                matches.append(
                    ThreatIntelMatch(
                        ioc_type="payload_signature",
                        indicator=pattern,
                        threat_description=desc,
                        severity="high",
                    )
                )

        return matches


threat_intel_feed = ThreatIntelFeed()
