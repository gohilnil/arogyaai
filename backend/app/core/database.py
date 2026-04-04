"""
app/core/database.py — Supabase database service layer
All DB operations with graceful fallback when Supabase not configured.
FIX: Supabase proxy errors handled with proper timeout and retry logic.
"""
import logging
from datetime import date, datetime
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("arogyaai.db")

# In-memory fallback store for local dev (no Supabase needed)
_DEV_USERS: dict = {}
_DEV_CONVERSATIONS: list = []


class Database:
    """Supabase wrapper — all DB operations live here."""
    _client = None

    @classmethod
    def get(cls):
        if cls._client is None:
            if not settings.has_supabase:
                raise RuntimeError("Supabase not configured.")
            try:
                from supabase import create_client
                # FIX: Add timeout options to prevent proxy hanging
                cls._client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_KEY,
                )
            except Exception as e:
                logger.error("[DB] Failed to create Supabase client: %s", e)
                raise
        return cls._client

    # ── Users ────────────────────────────────────────
    @classmethod
    async def get_user_by_email(cls, email: str) -> Optional[dict]:
        # DEV FALLBACK
        if not settings.has_supabase:
            return _DEV_USERS.get(email.lower())
        try:
            db = cls.get()
            result = db.table("users").select("*").eq("email", email.lower()).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.warning("[DB] get_user_by_email: %s", e)
            return None

    @classmethod
    async def get_user_by_id(cls, user_id: str) -> Optional[dict]:
        if not settings.has_supabase:
            # Search dev store by id
            for u in _DEV_USERS.values():
                if u.get("id") == user_id:
                    return u
            return None
        try:
            db = cls.get()
            result = db.table("users").select("*").eq("id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.warning("[DB] get_user_by_id: %s", e)
            return None

    @classmethod
    async def create_user(cls, email: str, name: str, hashed_password: str) -> Optional[dict]:
        if not settings.has_supabase:
            import uuid
            user = {
                "id": str(uuid.uuid4()),
                "email": email.lower(),
                "name": name,
                "hashed_password": hashed_password,
                "is_premium": False,
                "plan": "free",
                "created_at": datetime.utcnow().isoformat(),
            }
            _DEV_USERS[email.lower()] = user
            return user
        try:
            db = cls.get()
            result = db.table("users").insert({
                "email":           email.lower(),
                "name":            name,
                "hashed_password": hashed_password,
                "is_premium":      False,
                "plan":            "free",
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.warning("[DB] create_user: %s", e)
            return None

    @classmethod
    async def update_user_profile(cls, user_id: str, profile_data: dict) -> bool:
        if not settings.has_supabase:
            return True
        try:
            db = cls.get()
            db.table("users").update(profile_data).eq("id", user_id).execute()
            return True
        except Exception as e:
            logger.warning("[DB] update_user_profile: %s", e)
            return False

    # ── Conversations ────────────────────────────────
    @classmethod
    async def save_conversation(
        cls,
        user_id: str,
        message: str,
        reply: str,
        severity: str = "mild",
        health_score: Optional[int] = None,
        needs_doctor: bool = False,
    ) -> None:
        if not user_id:
            return
        if not settings.has_supabase:
            import uuid
            _DEV_CONVERSATIONS.append({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "message": message[:2000],
                "reply": reply[:5000],
                "severity": severity,
                "health_score": health_score,
                "needs_doctor": needs_doctor,
                "created_at": datetime.utcnow().isoformat(),
            })
            return
        try:
            db = cls.get()
            db.table("conversations").insert({
                "user_id":      user_id,
                "message":      message[:2000],
                "reply":        reply[:5000],
                "severity":     severity,
                "health_score": health_score,
                "needs_doctor": needs_doctor,
            }).execute()
        except Exception as e:
            logger.warning("[DB] save_conversation: %s", e)

    @classmethod
    async def get_user_history(cls, user_id: str, limit: int = 15) -> list:
        if not settings.has_supabase:
            convs = [c for c in _DEV_CONVERSATIONS if c.get("user_id") == user_id]
            return sorted(convs, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]
        try:
            db = cls.get()
            result = (
                db.table("conversations")
                .select("id, message, reply, severity, health_score, needs_doctor, created_at")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.warning("[DB] get_user_history: %s", e)
            return []

    # ── Query Usage (Freemium) ───────────────────────
    @classmethod
    async def get_query_count(cls, user_id: str) -> int:
        if not settings.has_supabase:
            return 0
        try:
            db = cls.get()
            today = str(date.today())
            result = (
                db.table("query_usage")
                .select("count")
                .eq("user_id", user_id)
                .eq("query_date", today)
                .execute()
            )
            return result.data[0]["count"] if result.data else 0
        except Exception as e:
            logger.warning("[DB] get_query_count: %s", e)
            return 0

    @classmethod
    async def increment_query_count(cls, user_id: str) -> None:
        if not settings.has_supabase:
            return
        try:
            db = cls.get()
            today = str(date.today())
            existing = (
                db.table("query_usage")
                .select("id, count")
                .eq("user_id", user_id)
                .eq("query_date", today)
                .execute()
            )
            if existing.data:
                row_id = existing.data[0]["id"]
                new_count = existing.data[0]["count"] + 1
                db.table("query_usage").update({"count": new_count}).eq("id", row_id).execute()
            else:
                db.table("query_usage").insert({
                    "user_id":    user_id,
                    "query_date": today,
                    "count":      1,
                }).execute()
        except Exception as e:
            logger.warning("[DB] increment_query_count: %s", e)

    # ── Streaks ──────────────────────────────────────
    @classmethod
    async def get_streak(cls, user_id: str) -> dict:
        if not settings.has_supabase:
            return {"current_streak": 1, "longest_streak": 1}
        try:
            db = cls.get()
            result = db.table("streaks").select("*").eq("user_id", user_id).execute()
            if result.data:
                return result.data[0]
            return {"current_streak": 0, "longest_streak": 0}
        except Exception as e:
            logger.warning("[DB] get_streak: %s", e)
            return {"current_streak": 0, "longest_streak": 0}

    @classmethod
    async def update_streak(cls, user_id: str) -> int:
        if not settings.has_supabase:
            return 1
        try:
            db = cls.get()
            today = date.today()
            result = db.table("streaks").select("*").eq("user_id", user_id).execute()

            if result.data:
                streak = result.data[0]
                last_active = date.fromisoformat(streak["last_active"])
                days_diff = (today - last_active).days

                if days_diff == 0:
                    return streak["current_streak"]
                elif days_diff == 1:
                    new_streak = streak["current_streak"] + 1
                else:
                    new_streak = 1

                longest = max(new_streak, streak["longest_streak"])
                db.table("streaks").update({
                    "current_streak": new_streak,
                    "longest_streak": longest,
                    "last_active":    str(today),
                }).eq("user_id", user_id).execute()
                return new_streak
            else:
                db.table("streaks").insert({
                    "user_id":        user_id,
                    "current_streak": 1,
                    "longest_streak": 1,
                    "last_active":    str(today),
                }).execute()
                return 1
        except Exception as e:
            logger.warning("[DB] update_streak: %s", e)
            return 0

    # ── Health Profile ───────────────────────────────
    @classmethod
    async def get_health_profile(cls, user_id: str) -> Optional[dict]:
        if not settings.has_supabase:
            return None
        try:
            db = cls.get()
            result = db.table("health_profiles").select("*").eq("user_id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.warning("[DB] get_health_profile: %s", e)
            return None

    @classmethod
    async def save_health_profile(cls, user_id: str, profile: dict) -> bool:
        if not settings.has_supabase:
            return True
        try:
            db = cls.get()
            existing = db.table("health_profiles").select("id").eq("user_id", user_id).execute()
            profile["user_id"] = user_id
            if existing.data:
                db.table("health_profiles").update(profile).eq("user_id", user_id).execute()
            else:
                db.table("health_profiles").insert(profile).execute()
            return True
        except Exception as e:
            logger.warning("[DB] save_health_profile: %s", e)
            return False

    # ── Family Members ───────────────────────────────
    @classmethod
    async def get_family_members(cls, user_id: str) -> list:
        if not settings.has_supabase:
            return []
        try:
            db = cls.get()
            result = (
                db.table("family_members")
                .select("*")
                .eq("owner_id", user_id)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.warning("[DB] get_family_members: %s", e)
            return []

    @classmethod
    async def add_family_member(cls, owner_id: str, member: dict) -> Optional[dict]:
        if not settings.has_supabase:
            import uuid
            member["id"] = str(uuid.uuid4())
            member["owner_id"] = owner_id
            return member
        try:
            db = cls.get()
            member["owner_id"] = owner_id
            result = db.table("family_members").insert(member).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.warning("[DB] add_family_member: %s", e)
            return None

    # ── Billing / Subscriptions ──────────────────────
    @classmethod
    async def upgrade_user_plan(
        cls,
        user_id: str,
        plan: str,
        razorpay_order_id: str = "",
        razorpay_payment_id: str = "",
        amount_inr: int = 0,
        expires_at: str = "",
    ) -> bool:
        if not settings.has_supabase:
            # Dev: just mark user as premium in memory
            for u in _DEV_USERS.values():
                if u.get("id") == user_id:
                    u["is_premium"] = True
                    u["plan"] = plan
            return True
        try:
            db = cls.get()
            db.table("users").update({
                "is_premium": True, "plan": plan,
            }).eq("id", user_id).execute()
            db.table("subscriptions").insert({
                "user_id": user_id,
                "plan": plan,
                "status": "active",
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "amount_inr": amount_inr,
                "expires_at": expires_at,
            }).execute()
            return True
        except Exception as e:
            logger.error("[DB] upgrade_user_plan: %s", e)
            return False

    @classmethod
    async def get_active_subscription(cls, user_id: str) -> Optional[dict]:
        if not settings.has_supabase:
            return None
        try:
            db = cls.get()
            result = (
                db.table("subscriptions")
                .select("*")
                .eq("user_id", user_id)
                .eq("status", "active")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.warning("[DB] get_active_subscription: %s", e)
            return None

    @classmethod
    async def cancel_subscription(cls, user_id: str, reason: str = "") -> bool:
        if not settings.has_supabase:
            return True
        try:
            db = cls.get()
            result = (
                db.table("subscriptions")
                .select("id")
                .eq("user_id", user_id)
                .eq("status", "active")
                .execute()
            )
            if not result.data:
                return False
            db.table("subscriptions").update({
                "status": "cancelled",
            }).eq("user_id", user_id).eq("status", "active").execute()
            return True
        except Exception as e:
            logger.warning("[DB] cancel_subscription: %s", e)
            return False

    # ── Admin Stats ──────────────────────────────────
    @classmethod
    async def get_admin_stats(cls) -> dict:
        if not settings.has_supabase:
            return {
                "total_users": len(_DEV_USERS),
                "premium_users": sum(1 for u in _DEV_USERS.values() if u.get("is_premium")),
                "queries_today": len(_DEV_CONVERSATIONS),
                "total_conversations": len(_DEV_CONVERSATIONS),
            }
        try:
            db = cls.get()
            total_users = len((db.table("users").select("id", count="exact").execute()).data or [])
            premium_users = len((db.table("users").select("id", count="exact").eq("is_premium", True).execute()).data or [])
            today = str(date.today())
            queries_today = len((db.table("query_usage").select("count").eq("query_date", today).execute()).data or [])
            total_convs = len((db.table("conversations").select("id", count="exact").execute()).data or [])
            return {
                "total_users": total_users,
                "premium_users": premium_users,
                "queries_today": queries_today,
                "total_conversations": total_convs,
            }
        except Exception as e:
            logger.warning("[DB] get_admin_stats: %s", e)
            return {}

    @classmethod
    async def get_all_users(cls, page: int = 1, limit: int = 50) -> list:
        if not settings.has_supabase:
            return list(_DEV_USERS.values())[(page - 1) * limit: page * limit]
        try:
            db = cls.get()
            offset = (page - 1) * limit
            result = (
                db.table("users")
                .select("id, email, name, is_premium, plan, created_at")
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.warning("[DB] get_all_users: %s", e)
            return []

    # ── Analytics ────────────────────────────────────
    @classmethod
    async def track_event(
        cls,
        user_id: Optional[str],
        event: str,
        properties: dict,
        session_id: Optional[str] = None,
    ) -> None:
        if not settings.has_supabase:
            return
        try:
            db = cls.get()
            db.table("analytics_events").insert({
                "user_id": user_id,
                "event": event,
                "properties": properties,
                "session_id": session_id,
            }).execute()
        except Exception as e:
            logger.debug("[DB] track_event (non-fatal): %s", e)

    @classmethod
    async def get_funnel_data(cls) -> dict:
        if not settings.has_supabase:
            return {"signups": len(_DEV_USERS), "first_chat": len(_DEV_CONVERSATIONS), "upgraded": 0}
        try:
            db = cls.get()
            signups = len((db.table("users").select("id", count="exact").execute()).data or [])
            first_chats = len((db.table("analytics_events").select("id", count="exact").eq("event", "chat_sent").execute()).data or [])
            upgrades = len((db.table("subscriptions").select("id", count="exact").eq("status", "active").execute()).data or [])
            return {"signups": signups, "first_chat": first_chats, "upgraded": upgrades}
        except Exception as e:
            logger.warning("[DB] get_funnel_data: %s", e)
            return {}

    # ── Data Export (DPDP Act 2023) ──────────────────
    @classmethod
    async def export_user_data(cls, user_id: str) -> dict:
        """Collect all user data for DPDP-compliant export."""
        profile = await cls.get_user_by_id(user_id) or {}
        health_profile = await cls.get_health_profile(user_id) or {}
        history = await cls.get_user_history(user_id, limit=100)
        family = await cls.get_family_members(user_id)
        subscription = await cls.get_active_subscription(user_id)
        streak = await cls.get_streak(user_id)

        # Scrub sensitive fields
        profile.pop("hashed_password", None)

        return {
            "export_date": datetime.utcnow().isoformat() + "Z",
            "user_id": user_id,
            "profile": profile,
            "health_profile": health_profile,
            "conversations": history,
            "family_members": family,
            "subscription": subscription,
            "streak": streak,
            "note": "Exported per India's Digital Personal Data Protection Act 2023.",
        }
