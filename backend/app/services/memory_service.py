"""
app/services/memory_service.py — LRU Response Cache + Conversation Memory
UPGRADED: proper LRU+TTL cache, per-user conversation summary engine
"""
import hashlib
import time
import logging
from collections import OrderedDict
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("arogyaai.memory")

PERSONAL_INDICATORS = [
    "my ", "i have", "i am", "i feel", "i've", "i'm", "iam", "my child",
    "मेरे", "मुझे", "मारे", "मुजे", "मने", "हमारे", "मेरा", "मेरी",
    "મારા", "મારી", "મને", "आमच्या",
]


class ResponseCache:
    """
    LRU cache with TTL for identical non-personalized queries.
    Saves Groq API costs for common generic health questions.
    Replace with Redis at scale.
    """

    def __init__(self, maxsize: int = 500, ttl_seconds: int = None):
        self._maxsize = maxsize
        self._ttl = ttl_seconds or settings.CACHE_TTL_SECONDS
        self._store: OrderedDict = OrderedDict()
        self._timestamps: dict = {}

    def _key(self, message: str) -> str:
        normalized = message.lower().strip()[:200]
        return hashlib.md5(normalized.encode()).hexdigest()

    def _is_personal(self, message: str) -> bool:
        msg_lower = message.lower()
        return any(ind in msg_lower for ind in PERSONAL_INDICATORS)

    def _evict_expired(self) -> None:
        now = time.time()
        expired = [k for k, ts in self._timestamps.items() if now - ts >= self._ttl]
        for k in expired:
            self._store.pop(k, None)
            self._timestamps.pop(k, None)

    def get(self, message: str) -> Optional[str]:
        key = self._key(message)
        if key not in self._store:
            return None
        ts = self._timestamps.get(key, 0)
        if time.time() - ts >= self._ttl:
            self._store.pop(key, None)
            self._timestamps.pop(key, None)
            return None
        # LRU: move to end
        self._store.move_to_end(key)
        return self._store[key]

    def set(self, message: str, reply: str) -> None:
        if self._is_personal(message):
            return  # Never cache personal health queries
        key = self._key(message)
        self._evict_expired()
        if len(self._store) >= self._maxsize:
            # Evict the oldest (LRU) entry
            oldest_key, _ = next(iter(self._store.items()))
            self._store.pop(oldest_key)
            self._timestamps.pop(oldest_key, None)
        self._store[key] = reply
        self._timestamps[key] = time.time()
        self._store.move_to_end(key)

    def clear_expired(self) -> int:
        before = len(self._store)
        self._evict_expired()
        return before - len(self._store)

    @property
    def size(self) -> int:
        return len(self._store)


class ConversationMemory:
    """
    Per-user rolling conversation summary for long-term AI context.
    Gives Dr. Arogya memory across sessions.
    Stores a 200-word health summary per user in memory (→ DB at scale).
    """

    def __init__(self):
        # {user_id: {"summary": str, "turn_count": int, "last_updated": float}}
        self._summaries: dict = {}

    def get_summary(self, user_id: str) -> str:
        """Returns a context string for the AI system prompt."""
        data = self._summaries.get(user_id)
        if not data or not data.get("summary"):
            return ""
        return f"\n\n[Patient History Summary]: {data['summary']}"

    def update(self, user_id: str, user_message: str, ai_reply: str) -> None:
        """Append to the user's health conversation summary."""
        if not user_id:
            return
        data = self._summaries.get(user_id, {"summary": "", "turn_count": 0})
        data["turn_count"] += 1

        # Extract key health facts from this turn (simple rule-based compression)
        key_points = self._extract_key_points(user_message, ai_reply)
        if key_points:
            existing = data["summary"]
            # Keep rolling summary under 300 words
            combined = f"{existing} {key_points}".strip()
            words = combined.split()
            if len(words) > 300:
                words = words[-300:]  # Keep most recent
            data["summary"] = " ".join(words)

        data["last_updated"] = time.time()
        self._summaries[user_id] = data
        logger.debug("Memory updated for user %s (turn %d)", user_id[:8], data["turn_count"])

    def _extract_key_points(self, user_message: str, ai_reply: str) -> str:
        """Simple heuristic extraction — at scale, use an LLM for this."""
        points = []
        msg_lower = user_message.lower()
        # Detect mentions of conditions / symptoms
        conditions = ["diabetes", "hypertension", "asthma", "thyroid", "heart", "bp",
                      "fever", "headache", "pain", "allergy", "cold", "cough"]
        for c in conditions:
            if c in msg_lower:
                points.append(c)
        # Detect severe AI replies
        if "consult a doctor" in ai_reply.lower() or "emergency" in ai_reply.lower():
            points.append("(doctor recommended)")
        return ", ".join(points) if points else ""

    def clear(self, user_id: str) -> None:
        self._summaries.pop(user_id, None)


# ── Singletons ────────────────────────────────────────────────────
response_cache = ResponseCache()
conversation_memory = ConversationMemory()
