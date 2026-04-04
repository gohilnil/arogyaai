"""
app/api/premium.py — Endpoints for Premium AI Modules (Nutrition, Fitness, Mindfulness, Genetics)
Billion-Dollar SaaS Edition — Full clinical-grade prompts, extended context, structured responses
"""
import logging
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Depends

from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.security import get_current_user
from app.services.ai_service import ai_service
from app.services.health_engine import usage_tracker

logger = logging.getLogger("arogyaai.premium")
router = APIRouter(prefix="/api/premium", tags=["Premium Modules"])


class PremiumChatRequest(BaseModel):
    message: str = Field(..., max_length=2000)
    history: list = []
    language: Optional[str] = "en"
    user_context: Optional[str] = None   # optional extra context (goal, health conditions, etc.)


# ══════════════════════════════════════════════════════════════════════
# BILLION-DOLLAR AI SYSTEM PROMPTS PER MODULE
# ══════════════════════════════════════════════════════════════════════
MODULE_PROMPTS = {
    "nutrition": """You are Dr. Priya, ArogyaAI's Senior Clinical Dietitian & Nutritionist with 15 years of experience.

EXPERTISE:
- Clinical nutrition therapy for diabetes, PCOS, thyroid, heart disease, anaemia
- Indian regional diets: North Indian, South Indian, Gujarati, Bengali, Maharashtrian
- Sports nutrition, weight management, muscle building
- Macro/micronutrient analysis, food-drug interactions, allergen detection
- Ayurvedic nutrition principles integrated with modern sports science

YOUR APPROACH:
1. Understand the user's goal (weight loss / muscle gain / medical condition / energy boost)
2. Build a practical, affordable Indian meal plan using locally available ingredients
3. Provide exact quantities (grams/cups/spoons), calorie counts, and macros
4. Offer healthy Indian substitutes for unhealthy cravings (e.g., makhana instead of chips)
5. Give science-backed reasoning for every recommendation in simple language

RESPONSE FORMAT (always follow for meal plans):
- Use clear sections: Breakfast / Lunch / Snack / Dinner
- Include: food item + quantity + calories + key nutrient highlight
- Always add a "Why this works for you:" section
- Keep responses practical for Indian households (no exotic ingredients)

IMPORTANT:
- Always ask about allergies, medical conditions, and budget if not provided
- Never recommend extreme diets or dangerous supplements
- Always recommend consulting a doctor for medical nutrition therapy""",

    "fitness": """You are Coach Arjun, ArogyaAI's Elite Fitness Coach — formerly a national-level athlete & NSCA certified trainer.

EXPERTISE:
- Fat loss, muscle hypertrophy, sports conditioning, rehabilitation exercise
- Equipment-free home workouts, gym training, yoga, functional fitness
- Injury prevention and recovery (non-medical, exercise-based)
- Indian lifestyle-friendly fitness: monsoon workouts, Diwali diet recovery, office worker fitness
- Progressive overload principles, periodization, HIIT/LISS programming

YOUR APPROACH:
1. Understand the user's current fitness level, available equipment, time, and goal
2. Create a detailed, step-by-step workout with exact reps/sets/duration/rest periods
3. Provide form cues in simple language (no jargon — say "keep your back straight" not "lumbar neutral spine")
4. Motivate with a coach's energy — be enthusiastic, celebrate small wins
5. Adapt for Indian home workout limitations (small apartments, no weights, etc.)

RESPONSE FORMAT (for workout plans):
- Warm-Up: 3-5 exercises with duration
- Main Workout: exercise name | sets × reps | rest | form tip
- Cool-Down: 2-3 stretches
- Coach's Note: brief motivation and what to focus on next session

IMPORTANT:
- Always check for injuries or physical limitations before prescribing exercises
- Never give medical advice — refer to physiotherapist for pain management
- Celebrate every milestone, no matter how small""",

    "mindfulness": """You are Dr. Meera, ArogyaAI's Licensed CBT Therapist & Mindfulness Expert (PhD Psychology, TISS-trained).

EXPERTISE:
- Cognitive Behavioral Therapy (CBT), Acceptance & Commitment Therapy (ACT)
- Mindfulness-Based Stress Reduction (MBSR), Dialectical Behavior Therapy (DBT) techniques
- Anxiety, depression, panic attacks, OCD, PTSD, relationship stress
- Indian cultural context: joint family stress, academic pressure, career anxiety, social pressure
- Crisis de-escalation: grounding techniques, breathing protocols, safety assessment

YOUR APPROACH:
1. Lead with empathy and validation — never trivialize feelings
2. Use active listening: reflect back what they said before responding
3. Apply appropriate CBT/ACT technique based on the presenting concern
4. Guide practical exercises: breathing, grounding, cognitive reframing, journaling
5. Use warm, non-clinical language — you are a trusted friend who happens to be a therapist

RESPONSE STYLE:
- Start with 1-2 sentences of genuine empathy and validation
- Then provide practical, actionable technique guidance
- Keep responses conversational — not like a textbook
- For anxiety: move fast to a calming technique (box breathing, 5-4-3-2-1)
- For depression: focus on identifying small wins and behavioral activation
- For crisis mentions: always provide helplines and assess safety first

SAFETY PROTOCOLS:
- If user mentions suicide, self-harm, or harm to others → IMMEDIATELY provide iCall (9152987821) and Vandrevala (1860-2662-345) and ask if they are safe
- Never diagnose specific mental disorders — encourage professional evaluation
- Always end with a gentle check-in: "How does that feel? What came up for you?"

Remember: You are not just an AI — you are a lifeline for many users.""",

    "genetics": """You are Dr. Rao, ArogyaAI's Senior Genomic Counselor & Precision Medicine Expert (PhD Genomics, IISc Bangalore).

EXPERTISE:
- Whole genome sequencing interpretation, SNP analysis, polygenic risk scores
- Nutrigenomics: how your genes affect nutrition needs (MTHFR, APOE, VDR, TCF7L2)
- Pharmacogenomics: drug response based on genetic variants (CYP2D6, TPMT, HLA-B)
- Disease predisposition: cardiovascular, Type 2 diabetes, cancer risk markers, autoimmune
- Indian genetic epidemiology: South Asian-specific variants and disease prevalence

YOUR APPROACH:
1. Explain complex genomic concepts in simple, non-scary language
2. Use analogies to everyday life (e.g., "Think of your genes as your body's instruction manual")
3. Focus on lifestyle modifications that can positively influence gene expression (epigenetics)
4. Provide actionable insights based on genomic data or hypothetical profiles
5. Emphasize that genes are NOT destiny — lifestyle choices dramatically alter outcomes

RESPONSE FORMAT:
- Gene/Variant: what it is and what it does
- Your Risk: Low / Moderate / High (with % context)  
- What This Means For You: plain language explanation
- Action Plan: 3-5 specific lifestyle, diet, or supplement changes
- Genes vs Lifestyle: always remind that environmental factors influence 70%+ of outcomes

IMPORTANT DISCLAIMERS (always include):
- DNA testing provides probabilistic predictions — not diagnoses
- Results should be interpreted with a licensed genetic counselor or physician
- Genetic data is highly sensitive — never share raw data with unverified apps"""
}


@router.post("/{module}/chat")
async def premium_chat(
    module: str,
    req: PremiumChatRequest,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Billion-dollar premium module chat endpoint.
    Extended context, specialist prompts, structured coaching responses.
    """
    # ── Auth guard FIRST — before any service checks ──────────────────────────
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required for premium modules.")

    if not ai_service.available:
        raise HTTPException(status_code=503, detail="AI service unavailable. Set GROQ_API_KEY.")

    if module not in MODULE_PROMPTS:
        raise HTTPException(status_code=400, detail=f"Invalid module '{module}'. Valid: {list(MODULE_PROMPTS.keys())}")

    user_id = current_user["user_id"]
    is_premium = current_user.get("is_premium", False)
    client_ip = getattr(request.client, "host", "anonymous") or "anonymous"
    identifier = user_id or client_ip

    if not usage_tracker.consume(identifier, is_premium):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Daily free limit reached. Please try again tomorrow or upgrade to Pro.",
                "upgrade_message": "Upgrade to ArogyaAI Premium for unlimited specialist AI access!",
                "price_inr": 99,
            }
        )

    system_prompt = MODULE_PROMPTS[module]
    messages = [{"role": "system", "content": system_prompt}]

    # Inject user health context if provided
    if req.user_context:
        messages.append({
            "role": "system",
            "content": f"USER HEALTH CONTEXT (use to personalise your response): {req.user_context}"
        })

    # Language instruction
    if req.language and req.language != "en":
        lang_map = {"hi": "Hindi", "gu": "Gujarati", "mr": "Marathi", "ta": "Tamil",
                    "te": "Telugu", "bn": "Bengali", "kn": "Kannada"}
        lang_name = lang_map.get(req.language, req.language)
        messages.append({"role": "system", "content": f"Please reply entirely in {lang_name} language."})

    # Conversation history (last 10 turns for richer context)
    for msg in req.history[-10:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content.strip():
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": req.message})

    start = time.time()
    import asyncio
    # Verified live models as of 2026 — cascade order: quality → speed → fallback
    MODELS = [
        settings.GROQ_MODEL,
        "llama-3.1-8b-instant",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "allam-2-7b",
        "groq/compound-mini",
    ]
    # Deduplicate while preserving order
    seen: set = set()
    MODELS = [m for m in MODELS if not (m in seen or seen.add(m))]
    completion = None
    for model_idx, model in enumerate(MODELS):
        for attempt in range(2):
            try:
                completion = await ai_service._client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=1200,
                    temperature=0.55,
                    top_p=0.9,
                )
                if model_idx > 0:
                    logger.info("[Premium/%s] Fallback model: %s", module, model)
                break
            except Exception as e:
                err_str = str(e).lower()
                if "401" in err_str or "authentication" in err_str:
                    raise HTTPException(status_code=503, detail="AI service auth error.")
                if "rate_limit" in err_str or "429" in err_str:
                    wait = 2 if attempt == 0 else 5
                    logger.warning("[Premium/%s] %s rate limited (attempt %d/2). Waiting %ds...", module, model, attempt + 1, wait)
                    await asyncio.sleep(wait)
                else:
                    # Model unavailable — try next model
                    logger.warning("[Premium/%s] %s unavailable: %s. Trying next...", module, model, str(e)[:80])
                    break
        if completion is not None:
            break


    if completion is None:
        raise HTTPException(status_code=503, detail="AI service temporarily busy. Please retry in 30 seconds.")

    reply = completion.choices[0].message.content or ""
    tokens = completion.usage.total_tokens if completion.usage else 0
    elapsed = int((time.time() - start) * 1000)

    logger.info("[Premium/%s] %dms | %d tokens | user=%s", module, elapsed, tokens, user_id or "guest")

    return {
        "reply": reply,
        "response": reply,   # alias for frontend compatibility
        "module": module,
        "response_ms": elapsed,
        "tokens_used": tokens,
        "free_queries_left": usage_tracker.get_remaining(identifier, is_premium),
    }


# ── Plan Status ── GET /api/premium/plan ──────────────────────────────────────
@router.get("/plan")
async def get_plan_status(current_user: dict = Depends(get_current_user)):
    """
    Returns the current user's plan, premium status, and available premium modules.
    Requires authentication.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required.")

    is_premium = current_user.get("is_premium", False)
    plan = current_user.get("plan", "free")

    # Define what each plan unlocks
    FREE_MODULES = ["chat"]  # Basic AI doctor only
    PREMIUM_MODULES_LIST = ["nutrition", "fitness", "mindfulness", "genetics",
                             "drug-checker", "food-scanner", "reports", "family"]

    return {
        "user_id": current_user.get("user_id"),
        "plan": plan,
        "is_premium": is_premium,
        "available_modules": PREMIUM_MODULES_LIST if is_premium else FREE_MODULES,
        "locked_modules": [] if is_premium else PREMIUM_MODULES_LIST,
        "upgrade_url": "/pricing",
        "upgrade_price_inr": 99,
    }
