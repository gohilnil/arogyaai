"""
app/api/admin.py — Admin panel API (protected by X-Admin-Secret header)
Stats, user management, error log, analytics
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Query

from app.core.config import settings
from app.core.database import Database
from app.core.middleware import error_log, get_stats

logger = logging.getLogger("arogyaai.admin")
router = APIRouter(prefix="/api/admin", tags=["Admin"])


def _require_admin(x_admin_secret: Optional[str] = Header(default=None)):
    """Dependency that validates the admin secret header."""
    if not settings.ADMIN_SECRET:
        raise HTTPException(status_code=503, detail="Admin panel not configured.")
    if x_admin_secret != settings.ADMIN_SECRET:
        logger.warning("Unauthorized admin access attempt.")
        raise HTTPException(status_code=403, detail="Forbidden.")


@router.get("/stats")
async def admin_stats(x_admin_secret: Optional[str] = Header(default=None)):
    """Overview statistics for the admin dashboard."""
    _require_admin(x_admin_secret)
    try:
        db_stats = await Database.get_admin_stats()
        perf = get_stats()
        return {
            "users": db_stats.get("total_users", 0),
            "premium_users": db_stats.get("premium_users", 0),
            "queries_today": db_stats.get("queries_today", 0),
            "total_conversations": db_stats.get("total_conversations", 0),
            "performance": perf,
            "recent_errors": list(error_log)[-10:],  # Last 10 errors
        }
    except Exception as e:
        logger.error("Admin stats error: %s", e)
        return {
            "users": 0,
            "premium_users": 0,
            "queries_today": 0,
            "performance": get_stats(),
            "recent_errors": list(error_log)[-10:],
        }


@router.get("/users")
async def admin_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, le=200),
    x_admin_secret: Optional[str] = Header(default=None),
):
    """Paginated user list for the admin panel."""
    _require_admin(x_admin_secret)
    try:
        users = await Database.get_all_users(page=page, limit=limit)
        return {
            "users": users,
            "page": page,
            "limit": limit,
            "count": len(users),
        }
    except Exception as e:
        logger.error("Admin users error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch users.")


@router.get("/errors")
async def admin_errors(x_admin_secret: Optional[str] = Header(default=None)):
    """Last 100 backend errors from the in-memory ring buffer."""
    _require_admin(x_admin_secret)
    return {
        "errors": list(reversed(list(error_log))),  # Most recent first
        "total": len(error_log),
    }


@router.get("/analytics/funnels")
async def admin_funnels(x_admin_secret: Optional[str] = Header(default=None)):
    """Conversion funnel: signup → first chat → upgrade."""
    _require_admin(x_admin_secret)
    try:
        funnel = await Database.get_funnel_data()
        return {"funnel": funnel}
    except Exception as e:
        logger.error("Funnel data error: %s", e)
        return {"funnel": {"signups": 0, "first_chat": 0, "upgraded": 0}}
