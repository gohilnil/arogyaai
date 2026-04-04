"""
app/services/feedback_service.py — User Feedback & Continuous Learning System
Stores thumbs up/down feedback and learning signals per conversation.
"""
import time
import logging
from typing import Optional
from collections import defaultdict

logger = logging.getLogger("arogyaai.feedback")


class FeedbackStore:
    """
    In-memory feedback store (replace with Supabase table at scale).
    Tracks user satisfaction signals for continuous improvement.
    """

    def __init__(self):
        # {feedback_id: FeedbackRecord}
        self._store: dict = {}
        # {body_system: [satisfaction_scores]} for analytics
        self._analytics: dict = defaultdict(list)
        self._counter = 0

    def record(
        self,
        user_id: Optional[str],
        message: str,
        ai_reply: str,
        rating: int,         # 1 = thumbs up, -1 = thumbs down
        issue_tag: Optional[str] = None,   # "wrong_info", "too_vague", "helpful", etc.
        severity: Optional[str] = None,
        body_system: Optional[str] = None,
    ) -> dict:
        """Record feedback. Returns the created record."""
        self._counter += 1
        fid = f"fb_{self._counter}_{int(time.time())}"

        record = {
            "id": fid,
            "user_id": user_id,
            "message_snippet": message[:100],
            "reply_snippet": ai_reply[:200],
            "rating": rating,
            "issue_tag": issue_tag,
            "severity": severity,
            "body_system": body_system,
            "timestamp": time.time(),
        }

        self._store[fid] = record

        # Update analytics
        if body_system:
            self._analytics[body_system].append(rating)

        logger.info(
            "[Feedback] %s rated=%s tag=%s system=%s user=%s",
            fid, rating, issue_tag, body_system, user_id or "guest"
        )
        return record

    def get_satisfaction_rate(self, body_system: Optional[str] = None) -> dict:
        """Returns overall and per-system satisfaction metrics."""
        if body_system and body_system in self._analytics:
            scores = self._analytics[body_system]
        else:
            scores = [r["rating"] for r in self._store.values()]

        if not scores:
            return {"total": 0, "positive": 0, "negative": 0, "rate": 0.0}

        positive = sum(1 for s in scores if s > 0)
        negative = sum(1 for s in scores if s < 0)
        return {
            "total": len(scores),
            "positive": positive,
            "negative": negative,
            "rate": round(positive / len(scores) * 100, 1),
        }

    def get_weak_areas(self) -> list:
        """Identify body systems with lowest satisfaction — for improvement focus."""
        weak = []
        for system, scores in self._analytics.items():
            if len(scores) >= 3:
                rate = sum(1 for s in scores if s > 0) / len(scores)
                if rate < 0.7:
                    weak.append({"body_system": system, "satisfaction_rate": rate, "samples": len(scores)})
        return sorted(weak, key=lambda x: x["satisfaction_rate"])

    def recent_feedback(self, limit: int = 20) -> list:
        """Return most recent feedback records."""
        records = sorted(self._store.values(), key=lambda r: r["timestamp"], reverse=True)
        return records[:limit]

    @property
    def total_count(self) -> int:
        return len(self._store)


# ── Singleton ─────────────────────────────────────────────────────
feedback_store = FeedbackStore()
