"""
app/api/health.py — Drug search, medical info, health card, config
"""
import logging
import urllib.parse
from fastapi import APIRouter

from app.schemas import DrugSearchRequest, MedicalInfoRequest, HealthScoreCard
from app.services.medical_service import medical_service
from app.services.health_engine import health_scorer
from app.core.config import settings

logger = logging.getLogger("arogyaai.health")
router = APIRouter(prefix="/api", tags=["Health & Medical"])


@router.post("/drug/search")
async def search_drug(req: DrugSearchRequest):
    """Search FDA database for drug info and adverse events."""
    drug_info = await medical_service.search_drug_fda(req.drug_name)
    ae_data = await medical_service.get_adverse_events(req.drug_name)
    return {
        "drug_name": req.drug_name,
        "drug_info": drug_info,
        "adverse_events": ae_data,
        "disclaimer": "Data sourced from FDA. Always consult a licensed pharmacist or doctor before taking any medication.",
    }


@router.post("/medical/info")
async def medical_info(req: MedicalInfoRequest):
    """Fetch Wikipedia medical summary for educational context."""
    result = await medical_service.get_wikipedia_summary(req.query)
    return {
        "query": req.query,
        "result": result,
        "disclaimer": "Educational information only. Not a substitute for professional medical advice.",
    }


@router.post("/health-card/generate", response_model=HealthScoreCard)
async def generate_health_card(user_id: str, score: int, streak: int = 1):
    """
    🚀 VIRAL MECHANIC: Generate a shareable WhatsApp health card.
    User shares → friends see it → friends download → growth loop.
    """
    score = max(0, min(100, score))
    message = health_scorer.generate_share_message(score, streak)
    wa_url = f"https://wa.me/?text={urllib.parse.quote(message)}"

    return HealthScoreCard(
        user_id=user_id,
        score=score,
        streak_days=streak,
        consultations=0,
        top_concern=None,
        share_message=message,
        whatsapp_url=wa_url,
    )


@router.get("/config")
async def get_config():
    """Frontend app configuration."""
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "free_queries_per_day": settings.FREE_DAILY_QUERIES,
        "premium_price_inr": settings.PREMIUM_PRICE_INR,
        "doctor_price_inr": settings.DOCTOR_PRICE_INR,
        "features": {
            "voice_input": True,
            "multilingual": True,
            "health_score": True,
            "family_tracking": True,
            "drug_lookup": True,
            "emergency_detect": True,
            "whatsapp_share": True,
            "streak_system": True,
            "report_analyzer": True,
        },
        "supported_languages": [
            {"code": "en", "name": "English"},
            {"code": "hi", "name": "हिंदी"},
            {"code": "gu", "name": "ગુજરાતી"},
            {"code": "mr", "name": "मराठी"},
            {"code": "te", "name": "తెలుగు"},
            {"code": "ta", "name": "தமிழ்"},
            {"code": "bn", "name": "বাংলা"},
            {"code": "kn", "name": "ಕನ್ನಡ"},
        ],
        "emergency_numbers": {
            "ambulance": "108",
            "police": "100",
            "aiims_helpline": "1800-11-7091",
            "women_helpline": "1091",
            "child_helpline": "1098",
            "mental_health": "iCall: 9152987821",
        },
        "plans": {
            "free": {
                "name": "Free",
                "queries_per_day": settings.FREE_DAILY_QUERIES,
                "features": ["Basic AI chat", "Emergency detection", "5 queries/day"],
                "price_inr": 0,
            },
            "premium": {
                "name": "Premium",
                "queries_per_day": "unlimited",
                "features": [
                    "Unlimited AI queries",
                    "Voice input (8 languages)",
                    "Health score tracking",
                    "Family mode (5 members)",
                    "Medical report analysis",
                    "Streak & gamification",
                    "Priority AI responses",
                    "WhatsApp health card",
                ],
                "price_inr": settings.PREMIUM_PRICE_INR,
            },
        },
    }
