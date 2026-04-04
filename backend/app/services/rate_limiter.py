"""
app/services/rate_limiter.py — Redis-ready rate limiter (Phase 1.6)
Uses Redis when REDIS_URL is set, falls back to in-memory dict (dev/single-process).
"""
import logging
import time
from collections import defaultdict
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("arogyaai.rate_limiter")


class RateLimiter:
    """
    Production-grade rate limiter with Redis backend.
    Falls back to in-memory dict when Redis is not available.
    Uses sliding window algorithm.
    """

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = window_seconds
        self._redis: Optional[object] = None
        self._memory: dict = defaultdict(list)  # {key: [timestamp, ...]}
        self._init_redis()

    def _init_redis(self) -> None:
        if not settings.REDIS_URL:
            logger.info("[RateLimiter] No REDIS_URL — using in-memory store (dev mode).")
            return
        try:
            import redis
            self._redis = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            self._redis.ping()
            logger.info("[RateLimiter] ✅ Redis connected: %s", settings.REDIS_URL[:30])
        except Exception as e:
            logger.warning("[RateLimiter] Redis unavailable (%s) — falling back to in-memory.", e)
            self._redis = None

    def is_allowed(self, key: str) -> bool:
        """Returns True if the request is allowed, False if rate-limited."""
        if self._redis:
            return self._redis_check(key)
        return self._memory_check(key)

    def get_remaining(self, key: str) -> int:
        """Returns how many requests are left in the current window."""
        if self._redis:
            try:
                count = int(self._redis.get(f"rl:{key}:count") or 0)
                return max(0, self.max_requests - count)
            except Exception:
                return self.max_requests
        # Memory fallback
        now = time.time()
        timestamps = [t for t in self._memory.get(key, []) if now - t < self.window]
        return max(0, self.max_requests - len(timestamps))

    def _redis_check(self, key: str) -> bool:
        """Sliding window via Redis INCR + EXPIRE."""
        try:
            rkey = f"rl:{key}:count"
            pipe = self._redis.pipeline()
            pipe.incr(rkey)
            pipe.expire(rkey, self.window)
            results = pipe.execute()
            count = results[0]
            if count > self.max_requests:
                logger.info("[RateLimiter] Redis rate-limited: %s (%d/%d)", key, count, self.max_requests)
                return False
            return True
        except Exception as e:
            logger.warning("[RateLimiter] Redis error (%s) — allowing request (fail-open).", e)
            return True

    def _memory_check(self, key: str) -> bool:
        """Sliding window via in-memory list of timestamps."""
        now = time.time()
        timestamps = self._memory[key]
        # Evict expired timestamps
        self._memory[key] = [t for t in timestamps if now - t < self.window]
        if len(self._memory[key]) >= self.max_requests:
            logger.info("[RateLimiter] Memory rate-limited: %s (%d/%d)", key, len(self._memory[key]), self.max_requests)
            return False
        self._memory[key].append(now)
        return True

    def reset(self, key: Optional[str] = None) -> None:
        """Dev/test helper: reset counters."""
        if self._redis:
            try:
                if key:
                    self._redis.delete(f"rl:{key}:count")
                else:
                    # Flush all rate limiter keys (dev only)
                    for k in self._redis.scan_iter("rl:*"):
                        self._redis.delete(k)
            except Exception:
                pass
        if key:
            self._memory.pop(key, None)
        else:
            self._memory.clear()


# ── Singleton instances ────────────────────────────────────────────────────────
# API-level rate limiter (per IP, per minute)
api_limiter = RateLimiter(
    max_requests=settings.RATE_LIMIT_REQUESTS,
    window_seconds=settings.RATE_LIMIT_WINDOW,
)
