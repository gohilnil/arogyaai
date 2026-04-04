"""
app/api/chat.py — Main AI chat endpoint with full Clinical Intelligence Engine pipeline
"""
import time
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Depends

from app.core.security import get_current_user
from app.core.database import Database
from app.schemas import ChatRequest, ChatResponse, DoctorUpsell, RiskAssessment
from app.services.ai_service import ai_service
from app.services.health_engine import (
    detect_emergency, health_scorer, usage_tracker, upsell_engine
)
from app.services.memory_service import response_cache
from app.services.medical_service import medical_service
from app.services.risk_engine import risk_engine
from app.services.symptom_engine import symptom_engine
from app.services.personalization_engine import personalization_engine

logger = logging.getLogger("arogyaai.chat")
router = APIRouter(prefix="/api/chat", tags=["Chat"], redirect_slashes=False)

EMERGENCY_RESPONSE = """🚨 **EMERGENCY DETECTED — CALL 108 NOW** 🚨

Your symptoms may indicate a **life-threatening emergency**. Please act immediately:

1. **Call 108** right now (Indian ambulance — free, 24/7)
2. Do NOT wait for home remedies
3. Keep the person calm and lying down
4. Do NOT give food or water

**Emergency Numbers:**
- 🚑 Ambulance: **108**
- 👮 Police: **100**
- 🏥 AIIMS Helpline: **1800-11-7091**
- 👩 Women Helpline: **1091**
- 👶 Child Helpline: **1098**

---
*ArogyaAI is not a substitute for emergency medical care. When in doubt, call 108.*"""


@router.post("", response_model=ChatResponse, include_in_schema=False)
@router.post("/", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
):
    """
    Main AI health chat endpoint.
    - Guest users: 5 free queries/day (by IP)
    - Logged-in users: tracked by user ID
    - Premium users: unlimited
    """
    if not ai_service.available:
        raise HTTPException(
            status_code=503,
            detail="AI service unavailable. Please configure GROQ_API_KEY in your environment."
        )

    # ── Determine identity & premium status ─────────────────
    user_id = current_user["user_id"] if current_user else None
    is_premium = current_user.get("is_premium", False) if current_user else False
    client_ip = getattr(request.client, "host", "anonymous") or "anonymous"
    identifier = user_id or client_ip

    # ── Emergency fast-path ──────────────────────────────────
    if detect_emergency(req.message):
        logger.warning("[Chat] Emergency detected for user=%s", identifier)
        return ChatResponse(
            reply=EMERGENCY_RESPONSE,
            model="emergency-system",
            severity="serious",
            urgency_level=5,        # Always max urgency for emergency fast-path
            health_score=15,
            needs_doctor=True,
            emergency=True,
            free_queries_left=usage_tracker.get_remaining(identifier, is_premium),
        )

    # ── Rate / usage check ───────────────────────────────────
    if not usage_tracker.consume(identifier, is_premium):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Daily free limit reached (5 queries/day).",
                "upgrade_message": "Upgrade to ArogyaAI Premium for ₹99/month — unlimited queries, priority AI, and more!",
                "price_inr": 99,
                "queries_used": 5,
                "queries_limit": 5,
            },
        )

    # ── Check response cache ─────────────────────────────────
    cached_reply = response_cache.get(req.message)
    if cached_reply and not current_user:
        logger.info("[Chat] Cache hit for: %.50s", req.message)
        return ChatResponse(
            reply=cached_reply,
            model="groq-cached",
            severity="mild",
            health_score=80,
            cached=True,
            free_queries_left=usage_tracker.get_remaining(identifier, is_premium),
        )

    # ── Fetch user health profile for personalization ────────
    user_profile = None
    if user_id:
        user_profile = await Database.get_health_profile(user_id)

    # ── Clinical Intelligence Engine pipeline ────────────────
    history_raw = [msg.model_dump() for msg in req.history]
    clinical_analysis = symptom_engine.analyze(req.message, history_raw)
    personalized_context = personalization_engine.build_context(
        user_profile=user_profile,
        conversation_history=history_raw,
        language=req.language or "en",
    )

    # Build enriched message with clinical context hints
    enriched_message = req.message
    followup_hint = ""
    if clinical_analysis["followup_question"] and len(history_raw) == 0:
        # Only hint on first message — don't repeat
        followup_hint = clinical_analysis["followup_question"]

    # ── Optional Wikipedia medical context ──────────────────
    wiki_context = None
    try:
        if len(req.message) > 20:
            # Use most prominent symptom as search term for relevance
            symptoms = clinical_analysis.get("symptoms", [])
            search_term = symptoms[0].replace("_", " ") if symptoms else req.message.split()[0]
            if len(search_term) > 4:
                wiki_context = await medical_service.get_wikipedia_summary(search_term)
    except Exception:
        pass

    # ── AI call ──────────────────────────────────────────────
    start = time.time()
    try:
        result = await ai_service.chat(
            message=enriched_message,
            history=history_raw,
            user_profile=user_profile,
            wiki_context=wiki_context,
            language=req.language or "en",
            personalized_context=personalized_context,
            clinical_analysis=clinical_analysis,
            followup_hint=followup_hint,
        )
    except Exception as e:
        logger.error("[Chat] AI call failed: %s", e)
        raise HTTPException(status_code=503, detail="AI response failed. Please try again in a moment.")

    elapsed = int((time.time() - start) * 1000)
    reply = result["reply"]
    tokens = result["tokens"]
    meta = result["meta"]

    # ── Compute health score ─────────────────────────────────
    score = health_scorer.compute(
        severity=meta.get("severity", "mild"),
        needs_doctor=meta.get("needs_doctor", False),
        emergency=meta.get("emergency", False),
    )

    # ── Save to DB & update streak ────────────────────────────
    if user_id:
        await Database.save_conversation(
            user_id=user_id,
            message=req.message,
            reply=reply,
            severity=meta.get("severity", "mild"),
            health_score=score,
            needs_doctor=meta.get("needs_doctor", False),
        )
        await Database.update_streak(user_id)

    # ── Cache the response ───────────────────────────────────
    response_cache.set(req.message, reply)

    # ── Build upsell ─────────────────────────────────────────
    upsell_data = upsell_engine.generate(
        severity=meta.get("severity", "mild"),
        body_system=meta.get("body_system", ""),
        needs_doctor=meta.get("needs_doctor", False),
    )
    upsell = DoctorUpsell(**upsell_data) if upsell_data else None

    # ── Compute risk assessment (now duration-aware) ─────────
    risk_data = risk_engine.compute(
        message=req.message,
        severity=meta.get("severity", "mild"),
        emergency=meta.get("emergency", False),
        needs_doctor=meta.get("needs_doctor", False),
        duration_days=clinical_analysis.get("duration_days"),
        user_profile=user_profile,
    )
    risk_obj = RiskAssessment(**risk_data)

    # ── Confidence from meta + symptom count ─────────────────
    confidence_map = {"high": 90, "medium": 72, "low": 52}
    base_confidence = confidence_map.get(meta.get("confidence", "medium"), 72)
    # Boost confidence when we have clean symptom analysis
    symptom_boost = min(clinical_analysis.get("symptom_count", 0) * 3, 8)
    confidence_score = min(base_confidence + symptom_boost, 97)

    logger.info(
        "[Chat] %dms | %d tokens | severity=%s | score=%d | risk=%s | symptoms=%s | user=%s",
        elapsed, tokens, meta.get("severity"), score,
        risk_data["risk_level"], clinical_analysis.get("symptoms"),
        user_id or "guest"
    )

    # ── Build urgency_level (1‑5 numeric) ──────────────────────
    urgency_map = {
        "self_care": 1, "monitor": 2, "see_doctor": 3, "urgent": 4, "emergency": 5
    }
    urgency_level = urgency_map.get(meta.get("urgency", "self_care"), 1)
    if meta.get("emergency"):
        urgency_level = 5
    elif meta.get("needs_doctor") and urgency_level < 3:
        urgency_level = 3

    # ── Build suggested action buttons ──────────────────────────
    suggested_actions = _build_suggested_actions(
        severity=meta.get("severity", "mild"),
        urgency_level=urgency_level,
        needs_doctor=meta.get("needs_doctor", False),
        specialist=meta.get("specialist"),
        body_system=meta.get("body_system", ""),
        suggested_tests=meta.get("suggested_tests", []),
    )

    # ── Build contextual quick reply suggestions ─────────────────
    quick_replies = _build_quick_replies(
        intent=clinical_analysis.get("intent", ""),
        symptoms=clinical_analysis.get("symptoms", []),
        urgency_level=urgency_level,
        followup_questions=meta.get("followup_questions", []),
    )

    return ChatResponse(
        reply=reply,
        model="groq",
        tokens_used=tokens,
        response_ms=elapsed,
        wiki_context=wiki_context,
        severity=meta.get("severity", "mild"),
        urgency_level=urgency_level,
        health_score=score,
        needs_doctor=meta.get("needs_doctor", False),
        emergency=meta.get("emergency", False),
        doctor_upsell=upsell,
        risk_assessment=risk_obj,
        confidence_score=confidence_score,
        body_system=meta.get("body_system", ""),
        suggested_actions=suggested_actions,
        quick_replies=quick_replies,
        detected_symptoms=clinical_analysis.get("symptoms", []),
        followup_question=clinical_analysis.get("followup_question"),
        intent=clinical_analysis.get("intent"),
        free_queries_left=usage_tracker.get_remaining(identifier, is_premium),
        conversation_id=req.conversation_id,
    )


# ── Helper: Suggested Action Buttons ─────────────────────────────────────────
def _build_suggested_actions(
    severity: str,
    urgency_level: int,
    needs_doctor: bool,
    specialist,
    body_system: str,
    suggested_tests: list,
) -> list:
    """Generate 1-3 contextual action buttons based on clinical metadata."""
    actions = []
    if urgency_level >= 5:
        actions.append("📞 Call 108 — Emergency")
        actions.append("🗺️ Find Nearest Hospital")
        return actions
    if urgency_level == 4:
        actions.append("🏥 Find Urgent Care Nearby")
    if needs_doctor or urgency_level >= 3:
        spec = specialist or "General Physician"
        actions.append(f"🩺 Book a {spec}")
    if suggested_tests:
        actions.append(f"🧪 Order {suggested_tests[0]}")
    elif body_system in ("digestive", "metabolic"):
        actions.append("🧪 Check Blood Sugar & HbA1c")
    elif body_system == "cardiovascular":
        actions.append("🧪 Book ECG + Lipid Panel")
    elif body_system == "respiratory":
        actions.append("🧪 Arrange Chest X-Ray")
    if urgency_level <= 2:
        actions.append("💊 Check Drug Interactions")
    return actions[:3]


# ── Helper: Quick Reply Suggestions ──────────────────────────────────────────
def _build_quick_replies(
    intent: str,
    symptoms: list,
    urgency_level: int,
    followup_questions: list,
) -> list:
    """Generate 3-5 smart follow-up quick reply chips for the chat UI."""
    if followup_questions:
        return followup_questions[:4]
    all_symptoms = " ".join(symptoms).lower()
    if urgency_level >= 4:
        return ["Is this dangerous?", "Warning signs to watch?", "Should I go to ER now?"]
    elif "fever" in all_symptoms or "headache" in all_symptoms:
        return ["How long will this last?", "Which medicine is safe?", "When to see a doctor?", "Home remedies?"]
    elif "chest" in all_symptoms:
        return ["Is this a heart issue?", "What tests do I need?", "Safe to exercise?"]
    elif intent in ("mental_health", "anxiety", "depression"):
        return ["Help me calm down now", "Breathing exercise?", "Connect me to a counsellor", "What should I avoid?"]
    else:
        return ["Tell me more", "Safe medicines?", "Diet recommendations?", "When to see a doctor?"]
