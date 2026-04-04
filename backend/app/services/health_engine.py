"""
app/services/health_engine.py — Health Score, Emergency Detection, Upsell Engine
FIXED: deterministic health scores (removed random variance)
FIXED: usage_tracker reads FREE_DAILY_QUERIES from settings at runtime
"""
from datetime import date
from typing import Optional

from app.core.config import settings


# ── Emergency Detection ──────────────────────────────────────────
EMERGENCY_KEYWORDS = {
    "en": [
        "chest pain", "heart attack", "cant breathe", "cannot breathe",
        "can't breathe", "stroke", "unconscious", "seizure", "fits",
        "heavy bleeding", "vomiting blood", "severe head injury", "paralysis",
        "face drooping", "arm weakness", "difficulty breathing",
        "swallowing problem", "not breathing", "stopped breathing",
        "choking", "overdose", "poison", "unresponsive", "anaphylaxis",
        "allergic reaction", "passed out", "fainted", "severe chest",
    ],
    "hi": [
        "सीने में दर्द", "बेहोश", "दौरा", "सांस नहीं", "खून आ रहा",
        "दिल का दौरा", "लकवा", "बेहोशी", "खून उल्टी", "साँस लेने में तकलीफ",
        "जहर खाया", "हार्ट अटैक", "बेहोशी आ रही", "गिर गए",
    ],
    "gu": [
        "છાતીમાં દુખાવો", "બેભાન", "હૃદય", "શ્વાસ ન", "લોહી ઉલ્ટી",
        "હૃદયઘાત", "લકવો", "ઝેર ખાધું",
    ],
    "mr": [
        "छातीत दुखणे", "बेशुद्ध", "झटका", "श्वास घेता येत नाही",
        "हृदयविकार", "अपघात",
    ],
}


def detect_emergency(message: str) -> bool:
    msg_lower = message.lower()
    for lang_keywords in EMERGENCY_KEYWORDS.values():
        for kw in lang_keywords:
            if kw.lower() in msg_lower:
                return True
    return False


# ── Health Score Engine ──────────────────────────────────────────
class HealthScoreEngine:
    """
    Computes a deterministic 0-100 Arogya Score from AI conversation metadata.
    FIXED: removed random.randint variance — scores are now reproducible and trustworthy.
    """

    @staticmethod
    def compute(severity: str, needs_doctor: bool, emergency: bool) -> int:
        if emergency:
            return 15
        base = 100
        deductions = {
            "serious": 35,
            "moderate": 18,
            "mild": 5,
        }
        base -= deductions.get(severity, 0)
        if needs_doctor:
            base -= 10
        return max(10, min(100, base))

    @staticmethod
    def get_status_label(score: int) -> str:
        if score >= 85:
            return "Excellent"
        elif score >= 65:
            return "Good"
        elif score >= 45:
            return "Fair"
        else:
            return "Poor"

    @staticmethod
    def get_status_color(score: int) -> str:
        if score >= 85:
            return "#22c55e"
        elif score >= 65:
            return "#84cc16"
        elif score >= 45:
            return "#f59e0b"
        else:
            return "#ef4444"

    @staticmethod
    def generate_share_message(score: int, streak: int) -> str:
        if score >= 85:
            emoji, status = "💪🌟", "Excellent health today!"
        elif score >= 65:
            emoji, status = "👍✅", "Good health today."
        elif score >= 45:
            emoji, status = "😐⚠️", "Needs a little attention."
        else:
            emoji, status = "🏥❗", "Please see a doctor soon."

        return (
            f"{emoji} My ArogyaAI Health Score: {score}/100\n"
            f"Status: {status}\n"
            f"🔥 {streak} day health streak!\n\n"
            f"Check your health free: https://arogyaai.in\n"
            f"#ArogyaAI #HealthIndia #स्वास्थ्य #HealthScore"
        )


# ── Query Usage Tracker (in-memory → Redis via RateLimiter at scale) ─
class QueryUsageTracker:
    """
    Tracks free-tier usage per IP/user.
    FIXED: reads FREE_DAILY_QUERIES from settings at runtime (not hardcoded).
    Replace _usage with Redis INCR + EXPIRE at scale via rate_limiter.py.
    """
    LOCALHOST_IPS = {"127.0.0.1", "::1", "localhost"}

    def __init__(self, free_limit: int):
        self._limit = free_limit
        self._usage: dict = {}  # {identifier: (count, "YYYY-MM-DD")}

    def reset(self):
        """Dev-only: reset all usage counters."""
        self._usage.clear()

    def _is_localhost(self, identifier: str) -> bool:
        return identifier in self.LOCALHOST_IPS

    def get_remaining(self, identifier: str, is_premium: bool = False) -> int:
        if is_premium or self._is_localhost(identifier):
            return 999
        today = str(date.today())
        if identifier in self._usage:
            count, recorded = self._usage[identifier]
            if recorded == today:
                return max(0, self._limit - count)
        return self._limit

    def consume(self, identifier: str, is_premium: bool = False) -> bool:
        if is_premium or self._is_localhost(identifier):
            return True
        today = str(date.today())
        if identifier in self._usage:
            count, recorded = self._usage[identifier]
            if recorded == today:
                if count >= self._limit:
                    return False
                self._usage[identifier] = (count + 1, today)
            else:
                self._usage[identifier] = (1, today)
        else:
            self._usage[identifier] = (1, today)
        return True


# ── Doctor Upsell Engine ─────────────────────────────────────────
UPSELL_SPECIALTIES = {
    "heart": "Cardiologist", "chest": "Cardiologist", "cardiac": "Cardiologist",
    "skin": "Dermatologist", "rash": "Dermatologist", "acne": "Dermatologist",
    "stomach": "Gastroenterologist", "digestion": "Gastroenterologist", "liver": "Gastroenterologist",
    "mental": "Psychiatrist", "anxiety": "Psychiatrist", "depression": "Psychiatrist",
    "bone": "Orthopedist", "joint": "Orthopedist", "spine": "Orthopedist",
    "eye": "Ophthalmologist", "vision": "Ophthalmologist",
    "breathing": "Pulmonologist", "lung": "Pulmonologist", "asthma": "Pulmonologist",
    "kidney": "Nephrologist", "urine": "Urologist",
    "diabetes": "Endocrinologist", "thyroid": "Endocrinologist",
    "child": "Pediatrician", "baby": "Pediatrician",
    "pregnancy": "Gynecologist", "women": "Gynecologist",
    "ear": "ENT Specialist", "nose": "ENT Specialist", "throat": "ENT Specialist",
    "teeth": "Dentist", "dental": "Dentist",
    "neuro": "Neurologist", "brain": "Neurologist", "headache": "Neurologist",
    "allergy": "Allergist", "immune": "Immunologist",
    "blood": "Hematologist",
}


class DoctorUpsellEngine:
    """
    Shows consultation upsell on serious/moderate conditions.
    Target: 2–5% conversion at ₹299/consult.
    """

    @staticmethod
    def generate(severity: str, body_system: str, needs_doctor: bool) -> Optional[dict]:
        if severity not in ("serious", "moderate") and not needs_doctor:
            return None

        specialty = "General Physician"
        body_lower = (body_system or "").lower()
        for keyword, spec in UPSELL_SPECIALTIES.items():
            if keyword in body_lower:
                specialty = spec
                break

        if severity == "serious":
            msg = (f"⚠️ Your symptoms suggest you should consult a **{specialty}** soon. "
                   f"Don't wait — book an online consultation from home.")
        else:
            msg = (f"💊 A **{specialty}** can give you a definitive diagnosis and treatment plan. "
                   f"Book an online consultation — no travel needed.")

        return {
            "show": True,
            "message": msg,
            "specialty": specialty,
            "price_inr": settings.PLAN_ELITE_PRICE_INR,
        }


# ── Singletons — reads FREE_DAILY_QUERIES from settings at module load ──
health_scorer = HealthScoreEngine()
usage_tracker = QueryUsageTracker(free_limit=settings.FREE_DAILY_QUERIES)
upsell_engine = DoctorUpsellEngine()
