"""
app/core/security_headers.py — Security headers middleware (OWASP hardening)
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to every response.
    Protects against XSS, clickjacking, MIME sniffing, and information leakage.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Legacy XSS protection (for old browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Don't leak referrer to external sites
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(self), geolocation=(), payment=(self)"
        )

        # FIX: MutableHeaders doesn't support .pop() — use del with try/except
        for h in ("server", "x-powered-by", "Server", "X-Powered-By"):
            try:
                del response.headers[h]
            except (KeyError, AttributeError):
                pass

        # HSTS — force HTTPS (only for API responses in production)
        if request.url.path.startswith("/api/"):
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response
