"""
app/api/feedback.py — Feedback API endpoint (thumbs up/down + continuous learning)
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.core.security import get_current_user
from app.services.feedback_service import feedback_store

logger = logging.getLogger("arogyaai.feedback")
router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


class FeedbackRequest(BaseModel):
    message: str = Field(..., max_length=500)
    ai_reply: str = Field(..., max_length=2000)
    rating: int = Field(..., ge=-1, le=1, description="1=helpful, -1=not helpful, 0=neutral")
    issue_tag: Optional[str] = Field(None, max_length=50)
    severity: Optional[str] = None
    body_system: Optional[str] = None


class FeedbackResponse(BaseModel):
    success: bool
    feedback_id: str
    message: str


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(
    req: FeedbackRequest,
    current_user: Optional[dict] = Depends(get_current_user),
):
    """Submit feedback for an AI response. Used for continuous learning."""
    user_id = current_user["user_id"] if current_user else None
    record = feedback_store.record(
        user_id=user_id,
        message=req.message,
        ai_reply=req.ai_reply,
        rating=req.rating,
        issue_tag=req.issue_tag,
        severity=req.severity,
        body_system=req.body_system,
    )
    msg = "Thank you for your feedback! 🙏" if req.rating == 1 else "We'll improve — thanks for letting us know! 💪"
    return FeedbackResponse(success=True, feedback_id=record["id"], message=msg)


@router.get("/stats")
async def get_feedback_stats(current_user: Optional[dict] = Depends(get_current_user)):
    """Returns overall satisfaction metrics."""
    stats = feedback_store.get_satisfaction_rate()
    weak = feedback_store.get_weak_areas()
    return {"stats": stats, "weak_areas": weak, "total_feedback": feedback_store.total_count}
