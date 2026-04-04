"""
app/api/analytics.py — Privacy-first analytics (own backend, not third-party)
Tracks user funnels and behavior without external data sharing.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.core.database import Database
from app.core.security import get_current_user

logger = logging.getLogger("arogyaai.analytics")
router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


class AnalyticsEvent(BaseModel):
    event: str
    properties: dict = {}
    session_id: Optional[str] = None


@router.post("/event")
async def track_event(
    req: AnalyticsEvent,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
):
    """
    Track a user event. No auth required — works for guests too.
    Events are stored in analytics_events table for funnel analysis.
    """
    # Sanitize: prevent massive property payloads
    properties = {str(k)[:50]: str(v)[:200] for k, v in (req.properties or {}).items()}
    properties["ip_country"] = request.headers.get("CF-IPCountry", "unknown")

    try:
        await Database.track_event(
            user_id=current_user["user_id"] if current_user else None,
            event=req.event[:100],
            properties=properties,
            session_id=req.session_id,
        )
    except Exception as e:
        # Never fail the user experience for analytics
        logger.debug("Analytics track error (non-fatal): %s", e)

    return {"ok": True}
