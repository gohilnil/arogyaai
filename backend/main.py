"""
ArogyaAI — Production FastAPI Application v3.0
backend/main.py
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.middleware import RequestLogMiddleware, error_log, get_stats
from app.core.security_headers import SecurityHeadersMiddleware
from app.api import auth, chat, user, health, voice, premium, feedback, drugs
from app.api import billing, admin, analytics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("arogyaai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Production safety validation
    settings.validate()

    logger.info("🌿 ArogyaAI v%s starting — env=%s", settings.APP_VERSION, settings.APP_ENV)
    logger.info("🤖 Groq AI:   %s", "✅ configured" if settings.has_groq else "❌ missing GROQ_API_KEY")
    logger.info("🗄️  Supabase:  %s", "✅ configured" if settings.has_supabase else "⚠️  dev mode (in-memory)")
    logger.info("💳 Razorpay:  %s", "✅ configured" if settings.has_razorpay else "⚠️  dev mock mode")
    logger.info("🔴 Redis:     %s", "✅ configured" if settings.has_redis else "⚠️  using in-memory rate limiter")
    logger.info("🛡️  CORS allowed: %s", settings.CORS_ORIGINS)
    yield
    logger.info("👋 ArogyaAI shutting down gracefully.")


app = FastAPI(
    title="ArogyaAI",
    description="India's AI Health Companion — Bharat ka apna doctor",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    # Disable interactive docs in production (security best practice)
    docs_url="/api/docs" if not settings.is_production else None,
    redoc_url=None,
)

# ── Security headers (must be first) ─────────────────────────────
app.add_middleware(SecurityHeadersMiddleware)

# ── CORS — environment-aware, never wildcard ──────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Admin-Secret"],
)

# ── Request logging + observability ──────────────────────────────
app.add_middleware(RequestLogMiddleware)


# ── Global error handler ──────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s %s — %s", request.method, request.url.path, exc)
    # Append to admin-visible error ring buffer
    from datetime import datetime, timezone
    error_log.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "method": request.method,
        "path": request.url.path,
        "error": str(exc)[:500],
        "status": 500,
    })
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again."},
    )


# ── API Routers ───────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(user.router)
app.include_router(health.router)
app.include_router(voice.router)
app.include_router(premium.router)
app.include_router(feedback.router)
app.include_router(drugs.router)
app.include_router(billing.router)
app.include_router(admin.router)
app.include_router(analytics.router)


# ── Serve frontend static files ───────────────────────────────────
FRONTEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
)

if os.path.exists(FRONTEND_DIR):
    # Static asset directories (css, js, components via StaticFiles)
    for subdir in ["css", "js", "components"]:
        path = os.path.join(FRONTEND_DIR, subdir)
        if os.path.exists(path):
            app.mount(f"/{subdir}", StaticFiles(directory=path), name=subdir)

    # Assets served via dynamic route so new files are always visible
    assets_dir = os.path.join(FRONTEND_DIR, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    @app.get("/assets/{asset_path:path}", include_in_schema=False)
    async def serve_asset(asset_path: str):
        fp = os.path.join(assets_dir, asset_path)
        if os.path.isfile(fp):
            return FileResponse(fp)
        return JSONResponse({"detail": "Not Found"}, status_code=404)

    # Mount manifest.json directly from frontend root
    manifest_path = os.path.join(FRONTEND_DIR, "manifest.json")
    if os.path.exists(manifest_path):
        @app.get("/manifest.json", include_in_schema=False)
        async def serve_manifest():
            return FileResponse(manifest_path, media_type="application/manifest+json")

    # Page routes
    PAGES = {
        "/": "index.html",
        "/login": "pages/login.html",
        "/signup": "pages/signup.html",
        "/dashboard": "pages/dashboard.html",
        "/chat": "pages/chat.html",
        "/profile": "pages/profile.html",
        "/family": "pages/family.html",
        "/reports": "pages/reports.html",
        "/nutrition": "pages/nutrition.html",
        "/fitness": "pages/fitness.html",
        "/mindfulness": "pages/mindfulness.html",
        "/genetics": "pages/genetics.html",
        "/food-scanner": "pages/food-scanner.html",
        "/drug-checker": "pages/drug-checker.html",
        "/emergency": "pages/emergency.html",
        # New pages
        "/onboarding": "pages/onboarding.html",
        "/pricing": "pages/pricing.html",
        "/admin": "pages/admin.html",
    }

    for route, filename in PAGES.items():
        filepath = os.path.join(FRONTEND_DIR, filename)

        def make_handler(fp, route_name):
            async def generated_handler():
                if os.path.exists(fp):
                    return FileResponse(fp)
                return JSONResponse({"detail": "Page not found"}, status_code=404)
            generated_handler.__name__ = (
                f"handler_{route_name.strip('/').replace('/', '_') or 'index'}"
            )
            return generated_handler

        app.get(route, include_in_schema=False)(make_handler(filepath, route))


# ── System health check ───────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    """Detailed system health status for monitoring and admin."""
    perf = get_stats()
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "services": {
            "groq_ai": "connected" if settings.has_groq else "not_configured",
            "supabase": "connected" if settings.has_supabase else "dev_mode",
            "razorpay": "connected" if settings.has_razorpay else "dev_mode",
            "redis": "connected" if settings.has_redis else "not_configured",
        },
        "performance": perf,
        "config": {
            "free_daily_queries": settings.FREE_DAILY_QUERIES,
            "cors_origins_count": len(settings.CORS_ORIGINS),
        },
    }


# ── Dev utilities (never in production) ──────────────────────────
if not settings.is_production:
    @app.post("/api/dev/reset-limits", tags=["Dev"], include_in_schema=False)
    async def reset_rate_limits():
        """Dev-only: reset in-memory rate limit counters."""
        from app.services.health_engine import usage_tracker
        usage_tracker.reset()
        return {"status": "reset", "message": "All rate limit counters cleared."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=not settings.is_production,
        log_level="info",
    )
