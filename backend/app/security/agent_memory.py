from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
from app.security.detector import injection_detector


class MemoryItem(BaseModel):
    key: str
    content: str
    user_id: int
    created_at: datetime
    sanitized: bool
    risk_score: float


class AgentMemoryStore:
    """Secure Agent Memory with pre-persistence injection sanitization (Module 9).

    Prevents indirect / stored prompt injection where untrusted external text
    is stored into long-term or episodic memory to hijack future sessions.
    """

    def __init__(self):
        self._memory: Dict[str, MemoryItem] = {}

    def store(self, key: str, content: str, user_id: int) -> Dict[str, Any]:
        """Validate content before storing into agent memory.

        Rejects or sanitizes content if it contains prompt injection patterns.
        """
        detection = injection_detector.analyze(content)

        if detection.is_flagged and detection.total_threat_weight >= 40.0:
            categories = [ind.category.value for ind in detection.indicators]
            return {
                "success": False,
                "reason": (
                    f"Memory Poisoning Defense Triggered: Cannot store memory '{key}'. "
                    f"Detected injection patterns: {', '.join(set(categories))}"
                ),
                "risk_score": min(95.0, detection.total_threat_weight),
                "stored": False,
            }

        item = MemoryItem(
            key=key,
            content=content,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            sanitized=True,
            risk_score=20.0 if detection.is_flagged else 0.0,
        )
        self._memory[f"{user_id}:{key}"] = item

        return {
            "success": True,
            "reason": "Memory item validated clean and persisted.",
            "risk_score": item.risk_score,
            "stored": True,
        }

    def retrieve(self, key: str, user_id: int) -> Optional[str]:
        item = self._memory.get(f"{user_id}:{key}")
        return item.content if item else None

    def list_keys(self, user_id: int) -> List[str]:
        prefix = f"{user_id}:"
        return [k.replace(prefix, "") for k in self._memory.keys() if k.startswith(prefix)]

    def clear(self, user_id: int):
        keys_to_del = [k for k in self._memory.keys() if k.startswith(f"{user_id}:")]
        for k in keys_to_del:
            del self._memory[k]


agent_memory_store = AgentMemoryStore()
