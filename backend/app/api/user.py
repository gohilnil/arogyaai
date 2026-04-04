"""
app/api/user.py — User profile, health profile, streaks, history, data export, referral
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.core.security import require_auth
from app.core.database import Database
from app.schemas import HealthProfileRequest, FamilyMemberRequest

logger = logging.getLogger("arogyaai.user")
router = APIRouter(prefix="/api/user", tags=["User"])


@router.get("/me")
async def get_me(current_user: dict = Depends(require_auth)):
    user = await Database.get_user_by_id(current_user["user_id"])
    if not user:
        return current_user
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user.get("name", ""),
        "is_premium": user.get("is_premium", False),
        "plan": user.get("plan", "free"),
        "created_at": user.get("created_at"),
    }


@router.get("/profile/health")
async def get_health_profile(current_user: dict = Depends(require_auth)):
    profile = await Database.get_health_profile(current_user["user_id"])
    return profile or {}


@router.put("/profile/health")
async def update_health_profile(
    profile: HealthProfileRequest,
    current_user: dict = Depends(require_auth),
):
    data = profile.model_dump(exclude_none=True)
    success = await Database.save_health_profile(current_user["user_id"], data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save health profile.")
    return {"message": "Health profile updated successfully.", "profile": data}


@router.get("/history")
async def get_history(
    limit: int = 15,
    current_user: dict = Depends(require_auth),
):
    if limit > 50:
        limit = 50
    history = await Database.get_user_history(current_user["user_id"], limit=limit)
    return {"history": history, "count": len(history)}


@router.get("/streak")
async def get_streak(current_user: dict = Depends(require_auth)):
    streak_data = await Database.get_streak(current_user["user_id"])
    current_streak = streak_data.get("current_streak", 0)
    longest = streak_data.get("longest_streak", 0)

    milestone_msg = ""
    if current_streak >= 100:
        milestone_msg = "🏆 100-day legend! You are a true health champion!"
    elif current_streak >= 30:
        milestone_msg = "🥇 30-day warrior! Amazing consistency!"
    elif current_streak >= 14:
        milestone_msg = f"🔥 {current_streak}-day streak! Two weeks strong!"
    elif current_streak >= 7:
        milestone_msg = "⭐ 7-day streak! You've built a real healthy habit!"
    elif current_streak >= 3:
        milestone_msg = f"✅ {current_streak}-day streak! Keep going!"
    elif current_streak == 1:
        milestone_msg = "🌱 Day 1 begins! Every health journey starts here."

    return {
        "current_streak": current_streak,
        "longest_streak": longest,
        "milestone_message": milestone_msg,
        "next_milestone": _next_milestone(current_streak),
        "badge": _get_badge(current_streak),
    }


def _next_milestone(streak: int) -> str:
    milestones = [3, 7, 14, 21, 30, 60, 100]
    for m in milestones:
        if streak < m:
            return f"{m - streak} more days to {m}-day badge!"
    return "You've unlocked all badges! 🎉"


def _get_badge(streak: int) -> dict:
    if streak >= 100:
        return {"emoji": "🏆", "name": "Health Legend", "color": "#FFD700"}
    elif streak >= 30:
        return {"emoji": "🥇", "name": "Health Warrior", "color": "#C0A060"}
    elif streak >= 14:
        return {"emoji": "🔥", "name": "On Fire", "color": "#FF6B35"}
    elif streak >= 7:
        return {"emoji": "⭐", "name": "Week Warrior", "color": "#4ECDC4"}
    elif streak >= 3:
        return {"emoji": "✅", "name": "Getting Started", "color": "#45B7D1"}
    return {"emoji": "🌱", "name": "Beginner", "color": "#96CEB4"}


@router.get("/family")
async def get_family(current_user: dict = Depends(require_auth)):
    members = await Database.get_family_members(current_user["user_id"])
    return {"family_members": members, "count": len(members)}


@router.post("/family")
async def add_family_member(
    member: FamilyMemberRequest,
    current_user: dict = Depends(require_auth),
):
    result = await Database.add_family_member(
        owner_id=current_user["user_id"],
        member=member.model_dump(),
    )
    if not result:
        raise HTTPException(status_code=500, detail="Failed to add family member.")
    return {"message": "Family member added successfully.", "member": result}


@router.get("/export-data")
async def export_user_data(current_user: dict = Depends(require_auth)):
    """
    DPDP Act 2023 compliant: export ALL data associated with this account.
    Returns a JSON file download containing every record we hold.
    """
    data = await Database.export_user_data(current_user["user_id"])
    return JSONResponse(
        content=data,
        headers={
            "Content-Disposition": f'attachment; filename="arogyaai-data-{current_user["user_id"][:8]}.json"',
        },
    )


@router.get("/referral")
async def get_referral_code(current_user: dict = Depends(require_auth)):
    """Returns the user's referral code and sharing link."""
    user = await Database.get_user_by_id(current_user["user_id"])
    referral_code = (user or {}).get("referral_code", "")

    if not referral_code:
        # Generate a simple referral code from user ID prefix
        import hashlib
        referral_code = "AROGYA" + hashlib.md5(current_user["user_id"].encode()).hexdigest()[:6].upper()

    share_url = f"https://arogyaai.in?ref={referral_code}"
    whatsapp_text = (
        f"🌿 I've been using ArogyaAI — India's AI doctor app! "
        f"Get personalized health advice in seconds.\n"
        f"Join free with my code: *{referral_code}*\n"
        f"👉 {share_url}\n#ArogyaAI #BharatKaDoctor"
    )
    import urllib.parse
    whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(whatsapp_text)}"

    return {
        "referral_code": referral_code,
        "share_url": share_url,
        "whatsapp_url": whatsapp_url,
        "message": "Share with friends and earn bonus queries!",
        "bonus_per_referral": 5,
    }
