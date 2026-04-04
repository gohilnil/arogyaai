"""
app/api/billing.py — Razorpay subscription billing (Pro + Elite tiers)
Full payment lifecycle: create order → verify → upgrade → cancel
"""
import hmac
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import Database
from app.core.security import require_auth, create_access_token, create_refresh_token

logger = logging.getLogger("arogyaai.billing")
router = APIRouter(prefix="/api/billing", tags=["Billing"])

# ── Plan definitions ───────────────────────────────────────────────
PLANS = {
    "pro": {
        "name": "ArogyaAI Pro",
        "price_inr": settings.PLAN_PRO_PRICE_INR,
        "queries_per_day": 999,
        "features": [
            "Unlimited AI consultations",
            "All premium health modules",
            "Detailed health reports",
            "Drug interaction checker",
            "Priority AI responses",
            "Family health management",
            "Health score tracking",
            "Conversation history",
        ],
    },
    "elite": {
        "name": "ArogyaAI Elite",
        "price_inr": settings.PLAN_ELITE_PRICE_INR,
        "queries_per_day": 999,
        "features": [
            "Everything in Pro",
            "Online doctor consultations",
            "Lab report analysis",
            "Genetics & DNA insights",
            "Dedicated health coach",
            "Emergency doctor connect",
            "Priority 24/7 support",
            "Custom health plans",
        ],
    },
}


# ── Request/Response models ────────────────────────────────────────
class CreateOrderRequest(BaseModel):
    plan: str  # "pro" | "elite"


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan: str


class CancelRequest(BaseModel):
    reason: Optional[str] = None


# ── Helper ─────────────────────────────────────────────────────────
def _get_razorpay_client():
    if not settings.has_razorpay:
        return None
    try:
        import razorpay
        return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET))
    except ImportError:
        logger.warning("razorpay package not installed. Run: pip install razorpay")
        return None


def _verify_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verify Razorpay webhook signature using HMAC-SHA256."""
    message = f"{order_id}|{payment_id}"
    # FIX: hmac.new() uses positional args only (key, msg, digestmod)
    expected = hmac.new(
        settings.RAZORPAY_SECRET.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ── Endpoints ──────────────────────────────────────────────────────
@router.get("/plans")
async def get_plans():
    """Returns all available subscription plans (public endpoint)."""
    return {
        "plans": PLANS,
        "currency": "INR",
        "razorpay_configured": settings.has_razorpay,
    }


@router.post("/create-order")
async def create_order(
    req: CreateOrderRequest,
    current_user: dict = Depends(require_auth),
):
    """Create a Razorpay payment order for the selected plan."""
    if req.plan not in PLANS:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {req.plan}")

    plan_info = PLANS[req.plan]
    amount_paise = plan_info["price_inr"] * 100  # Razorpay uses paise

    client = _get_razorpay_client()
    if not client:
        # Dev mode: return a mock order for testing
        logger.info("Razorpay not configured — returning mock order for dev")
        return {
            "order_id": f"order_DEV_{current_user['user_id'][:8]}",
            "amount": amount_paise,
            "currency": "INR",
            "key_id": settings.RAZORPAY_KEY_ID or "rzp_test_demo",
            "plan": req.plan,
            "plan_name": plan_info["name"],
            "dev_mode": True,
        }

    try:
        order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"arogyaai_{current_user['user_id'][:16]}_{req.plan}",
            "notes": {
                "user_id": current_user["user_id"],
                "user_email": current_user["email"],
                "plan": req.plan,
            },
        })
        logger.info("Razorpay order created: %s for user %s", order["id"], current_user["email"])
        return {
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key_id": settings.RAZORPAY_KEY_ID,
            "plan": req.plan,
            "plan_name": plan_info["name"],
        }
    except Exception as e:
        logger.error("Razorpay order creation failed: %s", e)
        raise HTTPException(status_code=502, detail="Payment service unavailable. Please try again.")


@router.post("/verify-payment")
async def verify_payment(
    req: VerifyPaymentRequest,
    current_user: dict = Depends(require_auth),
):
    """
    Verify Razorpay payment signature. On success:
    - Updates user plan to pro/elite
    - Creates subscription record in DB
    - Returns new JWT with updated premium claims
    """
    if req.plan not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan.")

    # Dev mode bypass
    if req.razorpay_order_id.startswith("order_DEV_"):
        logger.info("DEV MODE: Skipping Razorpay signature verification")
    elif settings.has_razorpay:
        if not _verify_signature(req.razorpay_order_id, req.razorpay_payment_id, req.razorpay_signature):
            logger.warning("Payment signature verification FAILED for user %s", current_user["email"])
            raise HTTPException(status_code=400, detail="Payment verification failed. Please contact support.")

    # Upgrade user in database
    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    upgraded = await Database.upgrade_user_plan(
        user_id=current_user["user_id"],
        plan=req.plan,
        razorpay_order_id=req.razorpay_order_id,
        razorpay_payment_id=req.razorpay_payment_id,
        amount_inr=PLANS[req.plan]["price_inr"],
        expires_at=expires_at,
    )

    if not upgraded:
        logger.error("Failed to upgrade plan for user %s", current_user["user_id"])
        raise HTTPException(status_code=500, detail="Plan upgrade failed. Please contact support@arogyaai.in")

    # Issue new tokens with updated premium claims
    claims = {
        "sub": current_user["user_id"],
        "email": current_user["email"],
        "name": current_user.get("name", ""),
        "premium": True,
    }
    new_access = create_access_token(claims)
    new_refresh = create_refresh_token(claims)

    logger.info("User %s upgraded to %s plan", current_user["email"], req.plan)
    return {
        "success": True,
        "plan": req.plan,
        "plan_name": PLANS[req.plan]["name"],
        "access_token": new_access,
        "refresh_token": new_refresh,
        "expires_at": expires_at,
        "message": f"🎉 Welcome to {PLANS[req.plan]['name']}! All premium features are now unlocked.",
    }


@router.get("/subscription")
async def get_subscription(current_user: dict = Depends(require_auth)):
    """Returns the user's current subscription status."""
    user = await Database.get_user_by_id(current_user["user_id"])
    sub = await Database.get_active_subscription(current_user["user_id"])

    plan = user.get("plan", "free") if user else "free"
    is_premium = user.get("is_premium", False) if user else False

    return {
        "user_id": current_user["user_id"],
        "plan": plan,
        "is_premium": is_premium,
        "plan_info": PLANS.get(plan, {"name": "Free", "price_inr": 0}),
        "subscription": sub,
        "upgrades_available": [k for k in PLANS if k != plan],
    }


@router.post("/cancel")
async def cancel_subscription(
    req: CancelRequest,
    current_user: dict = Depends(require_auth),
):
    """Cancel subscription at end of billing period."""
    cancelled = await Database.cancel_subscription(
        user_id=current_user["user_id"],
        reason=req.reason,
    )
    if not cancelled:
        raise HTTPException(status_code=404, detail="No active subscription found.")

    logger.info("User %s cancelled subscription. Reason: %s", current_user["email"], req.reason)
    return {
        "success": True,
        "message": "Your subscription has been cancelled. You'll retain premium access until the end of your billing period.",
    }
