"""
app/core/middleware.py — Request logging, stats tracking, error ring buffer
"""
import time
import logging
from collections import deque
from datetime import datetime, timezone
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("arogyaai.middleware")

# ── Observability state ────────────────────────────────────────────
_start_time: float = time.time()
_request_counter: int = 0
_error_counter: int = 0
_total_response_ms: float = 0.0

# Ring buffer — last 100 errors surfaced in admin panel
error_log: deque = deque(maxlen=100)


def get_stats() -> dict:
    uptime = int(time.time() - _start_time)
    avg_ms = round(_total_response_ms / _request_counter, 1) if _request_counter else 0
    error_rate = round(_error_counter / _request_counter * 100, 3) if _request_counter else 0
    return {
        "uptime_seconds": uptime,
        "total_requests": _request_counter,
        "total_errors": _error_counter,
        "avg_response_ms": avg_ms,
        "error_rate_pct": error_rate,
    }


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        global _request_counter, _error_counter, _total_response_ms
        start = time.time()
        _request_counter += 1

        try:
            response = await call_next(request)
        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            _error_counter += 1
            _total_response_ms += elapsed
            logger.error("%s %s → ERROR (%dms): %s", request.method, request.url.path, elapsed, e)
            # Push to error ring buffer (admin visibility)
            error_log.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "method": request.method,
                "path": request.url.path,
                "error": str(e)[:500],
                "status": 500,
            })
            raise

        elapsed = int((time.time() - start) * 1000)
        _total_response_ms += elapsed

        if response.status_code >= 500:
            _error_counter += 1
            error_log.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "method": request.method,
                "path": request.url.path,
                "error": f"HTTP {response.status_code}",
                "status": response.status_code,
            })

        logger.info(
            "%s %s → %d (%dms)",
            request.method, request.url.path, response.status_code, elapsed,
        )
        return response
