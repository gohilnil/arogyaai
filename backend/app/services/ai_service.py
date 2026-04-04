"""
app/services/ai_service.py — World-Class Clinical AI Engine
Dr. Arogya: Billion-dollar tier clinical intelligence with 6-step medical reasoning.
"""
import json
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("arogyaai.ai")

# ══════════════════════════════════════════════════════════════════════════════
# CLINICAL SYSTEM PROMPT — World's Best AI Doctor
# ══════════════════════════════════════════════════════════════════════════════
CLINICAL_SYSTEM_PROMPT = """You are **Dr. Arogya** — the world's most advanced AI physician and the clinical intelligence engine behind ArogyaAI, India's billion-dollar health platform.

You possess the combined knowledge and clinical judgment of:
- Board-certified Internal Medicine specialist (20+ years Indian practice)
- Senior Emergency Medicine physician trained at AIIMS
- Expert in Ayurveda, integrative medicine & preventive health
- Clinical Pharmacologist with deep drug interaction expertise
- Certified nutritionist and sports medicine physiologist
- Mental health counselor with trauma-informed, culturally-sensitive care training
- Pediatric specialist with additional geriatric care training

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CLINICAL REASONING PROTOCOL (Execute before every response)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1 — INTAKE ASSESSMENT:
  - Classify: What body system? What symptom pattern?
  - Note: Onset, location, severity (1-10), character (constant/intermittent)
  - Identify: Modifying factors (better with? worse with?)
  - Gather: Associated symptoms (what else is happening?)

STEP 2 — HISTORY INTEGRATION:
  - Pull from user's stored health profile: age, gender, conditions, medications, allergies
  - Adjust differential probability based on demographics and Indian epidemiology
  - Consider comorbidities, polypharmacy in elderly, pediatric caution for under-18

STEP 3 — DIFFERENTIAL DIAGNOSIS:
  - Rank 3-5 most likely causes by probability for Indian population
  - For each: explain WHY it fits the symptom picture
  - Flag RED FLAG symptoms requiring immediate escalation

STEP 4 — CLINICAL IMPRESSION (SOAP format internally):
  - S: Subjective — what the patient reports
  - O: Objective — what we know from their profile + vitals
  - A: Assessment — your clinical impression
  - P: Plan — recommended action

STEP 5 — PERSONALIZED ACTION PLAN:
  - Immediate safe home care (Indian home remedies FIRST)
  - Safe OTC suggestions (paracetamol, ORS, antacids, antihistamines ONLY)
  - Dietary adjustments for Indian cuisine context
  - Urgency triage: SELF-CARE / MONITOR 48H / SEE DOCTOR / URGENT / EMERGENCY

STEP 6 — SAFETY NET:
  - Red flags to watch for
  - Specialist type if referral needed
  - Always include medical disclaimer
  - Never replace emergency services

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
URGENCY TRIAGE SYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 SELF-CARE — Manage at home safely
🟡 MONITOR — Watch closely for 24-48 hours
🟠 SEE A DOCTOR — Schedule within a week
🔴 URGENT — Go today (same-day consultation)
🚨 EMERGENCY — Call 108 IMMEDIATELY

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ABSOLUTE SAFETY RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMMEDIATELY escalate to 108 / 112 for:
• Chest pain radiating to arm/jaw/shoulder (cardiac)
• Stroke signs — FAST: Face drooping, Arm weakness, Speech slurred, Time to call
• Severe difficulty breathing / choking / airways compromised
• Infant under 3 months with fever >100.4°F
• Seizures / fits / loss of consciousness / unresponsiveness
• Severe uncontrolled bleeding
• Suspected poisoning / overdose / anaphylaxis
• Signs of severe dehydration in child (sunken eyes, no urine, lethargic)
• Suicidal ideation with intent or plan

For these: START response with EMERGENCY WARNING heading and 108 number. Do NOT give home remedies first.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BEDSIDE MANNER & COMMUNICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Open with warm, empathetic acknowledgment — never clinical or cold
• NEVER give a single definitive diagnosis without enough history
• ALWAYS ask 1-2 clarifying follow-up questions when critical info is missing
• Use "this may be" / "could indicate" — never definitive "you have X"
• Culturally sensitive to Indian/South Asian health context and lifestyle
• Multilingual: Hindi (Devanagari) → full Hindi reply | Gujarati → Gujarati | English/mixed → English
• Respect economic diversity: affordable options first, home remedies before hospital
• For geriatric (65+): flag polypharmacy risks, fall risks, cognitive symptoms
• For pediatric (under 18): extra caution, always recommend seeing pediatrician
• For mental health: active listening, never minimize, always provide crisis resources (iCall: 9152987821)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INDIAN MEDICAL INTELLIGENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
India-prevalent diseases: dengue, typhoid, malaria, chikungunya, TB, enteric fever,
viral fever, leptospirosis, hepatitis A/B/E, H1N1, Japanese Encephalitis in monsoon
Indian medicinal foods: turmeric (haldi), ginger (adrak), tulsi, neem, amla,
ashwagandha, triphala, giloy, methi, jeera, ajwain, saunf, kadha, mulethi, raw honey
Seasonal alerts: heat stroke/dehydration May-June | Dengue/malaria Aug-Oct | Respiratory Nov-Jan
OTC approved: paracetamol 500mg, ORS, antacids (gelusil/eno), cetirizine, B-complex
NEVER recommend: prescription antibiotics, steroids, opioids, insulin dosing, antiretrovirals

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY RESPONSE FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Warm empathetic opening — 1-2 sentences connecting with how the user feels]

**URGENCY:** [🟢 SELF-CARE / 🟡 MONITOR / 🟠 SEE A DOCTOR / 🔴 URGENT / 🚨 EMERGENCY]
[One clear sentence explaining why this urgency level]

**🔍 What This Could Be**
[2-4 probable causes in plain, non-scary language. No medical jargon. Each with brief reasoning.]

**✅ What You Can Do Right Now**
[Immediate actionable steps. Indian home remedies first, then safe OTC if appropriate. Practical and affordable.]

**🍽️ Diet & Lifestyle**
[What to eat/avoid. Indian-context foods. 1-2 practical lifestyle adjustments.]

**⚠️ Watch For These Warning Signs**
[3-4 specific red flags that mean they must seek immediate or urgent care]

**🏥 When to See a Doctor**
[Clear, specific guidance on whether/when to see a real doctor + what type of specialist if needed]

*💙 ArogyaAI provides clinical guidance, not a medical diagnosis. For serious symptoms, always consult a licensed physician.*

HEALTH_META:{"severity":"mild|moderate|serious","urgency":"self_care|monitor|see_doctor|urgent|emergency","body_system":"string","confidence":"high|medium|low","needs_doctor":true|false,"emergency":false,"specialist":"string|null","suggested_tests":[],"followup_questions":[],"home_care_steps":[]}
"""

# ══════════════════════════════════════════════════════════════════════════════
# DRUG INTERACTION SYSTEM PROMPT
# ══════════════════════════════════════════════════════════════════════════════
DRUG_INTERACTION_PROMPT = """You are a senior clinical pharmacologist with deep expertise in drug-drug and drug-food interactions.

Analyze the provided list of medications and return a comprehensive interaction report.

For each interaction pair:
- Classify severity: SAFE (green) | CAUTION (yellow) | DANGEROUS (red) | CRITICAL (black/emergency)
- Explain mechanism briefly in plain language
- Provide clinical recommendation

Also analyze:
- Drug-food interactions (especially common Indian foods: grapefruit, pomelo, high-potassium foods, dairy)
- Timing recommendations (which drugs to take with/without food)
- Common side effects to watch for with this combination

Format your response as structured markdown with clear sections.
Always recommend consulting a pharmacist or doctor before changing any medication.

End with: DRUG_META:{"total_interactions":N,"critical":N,"dangerous":N,"caution":N,"safe":N}"""

# ══════════════════════════════════════════════════════════════════════════════
# LAB REPORT ANALYSIS PROMPT
# ══════════════════════════════════════════════════════════════════════════════
LAB_ANALYSIS_PROMPT = """You are a senior pathologist and clinical biochemist explaining lab results to a patient in plain language.

Analyze the provided lab report values and:
1. For each abnormal value: explain what it means in plain English (no jargon)
2. Classify: ✅ NORMAL | ⚠️ BORDERLINE | 🔴 ABNORMAL (needs attention) | 🚨 CRITICAL (seek immediate care)
3. Explain possible causes for any abnormal values
4. Suggest lifestyle modifications where applicable
5. Recommend specialist consultation type if needed
6. Flag any critical combinations (e.g., high glucose + high HbA1c = likely diabetes)

Be warm, clear, and reassuring. Never cause unnecessary alarm.
Always remind: "These results should be discussed with your doctor who knows your full medical history."

Format with clear sections and use emojis for visual clarity."""

# ══════════════════════════════════════════════════════════════════════════════
# HEALTH REPORT GENERATION PROMPT
# ══════════════════════════════════════════════════════════════════════════════
HEALTH_REPORT_PROMPT = """You are generating a comprehensive, physician-quality health summary report for a patient.

Create a structured weekly/monthly health report that includes:
1. **Executive Health Summary** — overall health status in 2-3 sentences
2. **Health Score Analysis** — current score, trend, contributing factors
3. **Symptom Patterns** — recurring symptoms, improvements, concerns
4. **Vitals Trends** — highlight any concerning changes
5. **Medication Adherence** — based on logged data
6. **Lifestyle Assessment** — sleep, exercise, nutrition summary
7. **AI Recommendations** — top 3 personalized actionable items for next week
8. **Doctor Visit Recommendation** — should they see a doctor? What type?

Write in the tone of a caring, respected physician. Warm but professional.
Use clear formatting with headers and bullet points."""


class AIService:
    """World-class Clinical AI Service — Dr. Arogya engine."""

    def __init__(self):
        self._client = None
        if settings.has_groq:
            try:
                from groq import AsyncGroq
                self._client = AsyncGroq(api_key=settings.GROQ_API_KEY)
                logger.info("[AI] ✅ Groq client initialized — model: %s", settings.GROQ_MODEL)
            except ImportError:
                logger.error("[AI] groq package not installed. Run: pip install groq")
            except Exception as e:
                logger.error("[AI] Failed to initialize Groq client: %s", e)
        else:
            logger.warning("[AI] GROQ_API_KEY not set — AI features disabled.")

    @property
    def available(self) -> bool:
        return self._client is not None

    async def _cascade_completion(
        self,
        messages: list,
        max_tokens: int = 1400,
        temperature: float | None = None,
        label: str = "AI",
    ) -> tuple[str, int]:
        """
        Unified 5-model cascade with exponential backoff.
        Returns (reply_text, total_tokens). Raises last exception if ALL models fail.

        Cascade order (all verified live as of 2026):
          1. llama-3.3-70b-versatile    — Primary (highest quality)
          2. llama-3.1-8b-instant       — Fast & reliable fallback
          3. meta-llama/llama-4-scout-17b-16e-instruct — Smart mid-tier
          4. allam-2-7b                 — Lightweight emergency fallback
          5. groq/compound-mini         — Last-resort fallback

        FIX: ALL errors (not just rate limits) now continue to next model.
        Only auth errors (401) and truly fatal errors abort the cascade.
        """
        import asyncio
        if temperature is None:
            temperature = settings.TEMPERATURE

        MODELS = [
            settings.GROQ_MODEL,                            # Primary (llama-3.3-70b-versatile)
            "llama-3.1-8b-instant",                        # Fast fallback
            "meta-llama/llama-4-scout-17b-16e-instruct",   # Smart mid-tier
            "allam-2-7b",                                  # Lightweight fallback
            "groq/compound-mini",                          # Last resort
        ]
        # Deduplicate while preserving order (in case GROQ_MODEL matches a fallback)
        seen = set()
        MODELS = [m for m in MODELS if not (m in seen or seen.add(m))]

        last_error: Exception | None = None

        for model_idx, model in enumerate(MODELS):
            for attempt in range(2):
                try:
                    completion = await self._client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    if model_idx > 0:
                        logger.info("[%s] Fallback model used: %s (primary failed)", label, model)
                    reply = completion.choices[0].message.content or ""
                    tokens = completion.usage.total_tokens if completion.usage else 0
                    return reply, tokens
                except Exception as e:
                    last_error = e
                    err_str = str(e).lower()

                    # Only abort entire cascade for auth errors — never for model errors
                    if "401" in err_str or "authentication" in err_str or "api key" in err_str:
                        logger.error("[%s] Auth error — aborting cascade: %s", label, e)
                        raise

                    if "rate_limit" in err_str or "429" in err_str:
                        wait = 3 if attempt == 0 else 8
                        logger.warning(
                            "[%s] %s rate limited (attempt %d/2). Waiting %ds...",
                            label, model, attempt + 1, wait,
                        )
                        await asyncio.sleep(wait)
                    else:
                        # Model unavailable / decommissioned / other error → try next model
                        logger.warning(
                            "[%s] %s failed (attempt %d/2): %s. Trying next model...",
                            label, model, attempt + 1, str(e)[:100],
                        )
                        break  # Don't retry same model for non-rate-limit errors

        logger.error("[%s] All %d models in cascade failed. Last error: %s", label, len(MODELS), last_error)
        raise last_error  # type: ignore[misc]

    async def chat(
        self,
        message: str,
        history: list,
        user_profile: Optional[dict] = None,
        wiki_context: Optional[str] = None,
        language: str = "en",
        personalized_context: Optional[str] = None,
        clinical_analysis: Optional[dict] = None,
        followup_hint: Optional[str] = None,
    ) -> dict:
        """
        Primary clinical consultation — 6-step clinical reasoning.
        Returns: {reply, tokens, meta}
        """
        if not self._client:
            raise RuntimeError("AI service not configured. Set GROQ_API_KEY.")

        messages = [{"role": "system", "content": CLINICAL_SYSTEM_PROMPT}]

        # Inject rich personalized patient context
        if personalized_context:
            messages.append({"role": "system", "content": personalized_context})
        elif user_profile:
            profile_ctx = self._build_profile_context(user_profile)
            if profile_ctx:
                messages.append({"role": "system", "content": profile_ctx})

        # Inject clinical analysis
        if clinical_analysis:
            ca = clinical_analysis
            ca_parts = []
            if ca.get("symptoms"):
                ca_parts.append(f"Detected symptoms: {', '.join(ca['symptoms'])}")
            if ca.get("intent"):
                ca_parts.append(f"User intent: {ca['intent']}")
            if ca.get("duration_raw"):
                ca_parts.append(f"Duration: {ca['duration_raw']}")
            if ca.get("differentials"):
                diffs = ca["differentials"][:3]
                diff_str = " | ".join(
                    f"{d['condition']} ({d['probability']:.0%})" for d in diffs
                )
                ca_parts.append(f"Clinical differential: {diff_str}")
            if ca_parts:
                messages.append({
                    "role": "system",
                    "content": "CLINICAL INTELLIGENCE (use to inform your reasoning, do not mention this directly):\n"
                    + "\n".join(ca_parts),
                })

        # Language hint
        if language and language != "en":
            lang_names = {
                "hi": "Hindi", "gu": "Gujarati", "mr": "Marathi",
                "ta": "Tamil", "te": "Telugu", "bn": "Bengali", "kn": "Kannada",
            }
            lang_name = lang_names.get(language, language)
            messages.append({
                "role": "system",
                "content": f"LANGUAGE: Respond entirely in {lang_name} as user is communicating in that language.",
            })

        # Follow-up hint
        if followup_hint:
            messages.append({
                "role": "system",
                "content": f"CLINICAL FOLLOW-UP: After your main response, ask this critical clarifying question: '{followup_hint}'",
            })

        # Wikipedia medical context
        if wiki_context:
            messages.append({
                "role": "system",
                "content": f"MEDICAL REFERENCE (use if clinically relevant, do not quote directly): {wiki_context[:600]}",
            })

        # Conversation history (last 12 turns)
        for msg in history[-12:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": message})

        # Use unified cascade — handles all error types, tries 5 models automatically
        try:
            raw_reply, tokens = await self._cascade_completion(
                messages=messages,
                max_tokens=min(settings.MAX_TOKENS, 1400),
                temperature=settings.TEMPERATURE,
                label="Chat",
            )
        except Exception as e:
            logger.error("[Chat] All models failed: %s", e)
            raise

        clean_reply, meta = self._parse_health_meta(raw_reply)
        return {"reply": clean_reply, "tokens": tokens, "meta": meta}

    async def check_drug_interactions(self, medications: list, user_profile: Optional[dict] = None) -> dict:
        """
        Clinical pharmacology AI with model-cascade retry.
        Returns structured interaction report with severity counts.
        """
        if not self._client:
            return {
                "error": "AI service not available.",
                "analysis": "Drug interaction checking requires AI configuration.",
                "meta": {"total_interactions": 0, "critical": 0, "dangerous": 0, "caution": 0, "safe": 0},
            }

        import asyncio
        import re
        med_list = ", ".join(medications)
        age_ctx = f"Patient age: {user_profile.get('age', 'unknown')}" if user_profile else ""
        conditions_ctx = f"Conditions: {', '.join(user_profile.get('conditions', []))}" if user_profile else ""

        system_prompt = """You are a Senior Clinical Pharmacologist with 20+ years Indian practice.

For each drug pair, assess:
- Severity: CRITICAL / DANGEROUS / CAUTION / SAFE
- Mechanism and clinical risk
- Management recommendation
- Indian brand names where relevant

FORMAT:
## Drug Interaction Analysis

### Interaction: [Drug A] + [Drug B]
**Severity:** CRITICAL/DANGEROUS/CAUTION/SAFE
**Risk:** [what happens]
**Recommendation:** [action required]

[For each pair]

## Summary
**Total:** [N] | **Critical:** [N] | **Dangerous:** [N] | **Caution:** [N] | **Safe:** [N]

## Clinical Recommendation
[One paragraph]

## Food & Lifestyle Interactions
[List important food-drug interactions]

⚠️ Always consult a pharmacist or physician before changing medications."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze interactions for: {med_list}\n{age_ctx}\n{conditions_ctx}"},
        ]

        # Use unified 5-model cascade — handles decommissioned models gracefully
        try:
            analysis, tokens = await self._cascade_completion(
                messages=messages,
                max_tokens=1200,
                temperature=0.2,
                label="DrugChecker",
            )
        except Exception as last_error:
            logger.error("[DrugChecker] All models exhausted: %s", last_error)
            return {
                "error": str(last_error),
                "analysis": "AI drug analysis temporarily unavailable. Please try again in 60 seconds.",
                "meta": {"total_interactions": 0, "critical": 0, "dangerous": 0, "caution": 0, "safe": 0},
            }


        analysis_text = analysis
        tokens_used = tokens

        critical_count = len(re.findall(r'\*\*Severity:\*\*\s*CRITICAL', analysis_text, re.IGNORECASE))
        dangerous_count = len(re.findall(r'\*\*Severity:\*\*\s*DANGEROUS', analysis_text, re.IGNORECASE))
        caution_count = len(re.findall(r'\*\*Severity:\*\*\s*CAUTION', analysis_text, re.IGNORECASE))
        safe_count = len(re.findall(r'\*\*Severity:\*\*\s*SAFE', analysis_text, re.IGNORECASE))
        total = critical_count + dangerous_count + caution_count + safe_count

        overall_risk = "CRITICAL" if critical_count > 0 else "DANGEROUS" if dangerous_count > 0 else "CAUTION" if caution_count > 0 else "SAFE"
        risk_color = {"CRITICAL": "#DC2626", "DANGEROUS": "#EA580C", "CAUTION": "#D97706", "SAFE": "#16A34A"}[overall_risk]

        logger.info("[DrugChecker] %d meds | c=%d d=%d ca=%d s=%d | %dt",
                    len(medications), critical_count, dangerous_count, caution_count, safe_count, tokens_used)

        return {
            "analysis": analysis_text,
            "medications_checked": medications,
            "tokens_used": tokens_used,
            "meta": {
                "total_interactions": total,
                "critical": critical_count,
                "dangerous": dangerous_count,
                "caution": caution_count,
                "safe": safe_count,
                "overall_risk": overall_risk,
                "risk_color": risk_color,
            },
        }

    async def analyze_lab_report(self, report_text: str, user_profile: Optional[dict] = None) -> dict:
        """Extract, interpret, and explain lab report values in plain language.
        FIXED: Uses 3-model cascade with exponential backoff (Bug #8).
        """
        if not self._client:
            raise RuntimeError("AI service not configured.")

        import asyncio
        patient_info = ""
        if user_profile:
            parts = []
            if user_profile.get("age"):
                parts.append(f"Age: {user_profile['age']}")
            if user_profile.get("gender"):
                parts.append(f"Gender: {user_profile['gender']}")
            if user_profile.get("conditions"):
                parts.append(f"Known conditions: {', '.join(user_profile['conditions'])}")
            if parts:
                patient_info = f"\nPatient: {' | '.join(parts)}"

        messages = [
            {"role": "system", "content": LAB_ANALYSIS_PROMPT},
            {"role": "user", "content": f"Lab report to analyze:{patient_info}\n\n{report_text}"},
        ]

        MODELS = [settings.GROQ_MODEL, "llama-3.1-8b-instant", "gemma2-9b-it"]
        last_error = None
        for model_idx, model in enumerate(MODELS):
            for attempt in range(2):
                try:
                    completion = await self._client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=2500,
                        temperature=0.2,
                    )
                    if model_idx > 0:
                        logger.info("[LabReport] Fallback model used: %s", model)
                    reply = completion.choices[0].message.content or ""
                    tokens = completion.usage.total_tokens if completion.usage else 0
                    return {"analysis": reply, "tokens": tokens}
                except Exception as e:
                    last_error = e
                    err_str = str(e).lower()
                    if "rate_limit" in err_str or "429" in err_str:
                        wait = 3 * (attempt + 1)
                        logger.warning("[LabReport] %s rate limited (attempt %d/2). Waiting %ds...", model, attempt + 1, wait)
                        await asyncio.sleep(wait)
                    else:
                        raise
        logger.error("[LabReport] All models exhausted: %s", last_error)
        raise last_error

    async def generate_health_report(
        self,
        user_profile: Optional[dict],
        conversation_history: list,
        period: str = "weekly",
    ) -> dict:
        """Generate comprehensive AI health summary report.
        FIXED: Uses 3-model cascade with exponential backoff (Bug #8).
        """
        if not self._client:
            raise RuntimeError("AI service not configured.")

        import asyncio
        # Build context
        health_data = f"Report period: {period.capitalize()}\n"
        if user_profile:
            health_data += self._build_profile_context(user_profile) + "\n"

        recent_consultations = conversation_history[-10:]
        if recent_consultations:
            health_data += "\nRecent health consultations:\n"
            for i, msg in enumerate(recent_consultations):
                if msg.get("role") == "user":
                    health_data += f"- {msg['content'][:100]}\n"

        messages = [
            {"role": "system", "content": HEALTH_REPORT_PROMPT},
            {"role": "user", "content": health_data},
        ]

        MODELS = [settings.GROQ_MODEL, "llama-3.1-8b-instant", "gemma2-9b-it"]
        last_error = None
        for model_idx, model in enumerate(MODELS):
            for attempt in range(2):
                try:
                    completion = await self._client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=2000,
                        temperature=0.3,
                    )
                    if model_idx > 0:
                        logger.info("[HealthReport] Fallback model used: %s", model)
                    reply = completion.choices[0].message.content or ""
                    tokens = completion.usage.total_tokens if completion.usage else 0
                    return {"report": reply, "tokens": tokens, "period": period}
                except Exception as e:
                    last_error = e
                    err_str = str(e).lower()
                    if "rate_limit" in err_str or "429" in err_str:
                        wait = 3 * (attempt + 1)
                        logger.warning("[HealthReport] %s rate limited (attempt %d/2). Waiting %ds...", model, attempt + 1, wait)
                        await asyncio.sleep(wait)
                    else:
                        raise
        logger.error("[HealthReport] All models exhausted: %s", last_error)
        raise last_error

    async def transcribe_audio(self, content: bytes, filename: str, language: str = "hi") -> str:
        """Whisper transcription — voice-first for Indian users."""
        if not self._client:
            raise RuntimeError("AI service not configured.")

        from io import BytesIO
        audio_file = BytesIO(content)
        audio_file.name = filename

        result = await self._client.audio.transcriptions.create(
            model=settings.GROQ_WHISPER_MODEL,
            file=audio_file,
            language=language,
            response_format="text",
        )
        return str(result).strip()

    @staticmethod
    def _build_profile_context(profile: dict) -> str:
        parts = []
        if profile.get("age"):
            parts.append(f"Age: {profile['age']} years")
        if profile.get("gender"):
            parts.append(f"Gender: {profile['gender']}")
        if profile.get("blood_group"):
            parts.append(f"Blood group: {profile['blood_group']}")
        if profile.get("weight_kg") and profile.get("height_cm"):
            bmi = profile["weight_kg"] / ((profile["height_cm"] / 100) ** 2)
            parts.append(f"BMI: {bmi:.1f} (wt: {profile['weight_kg']}kg, ht: {profile['height_cm']}cm)")
        if profile.get("conditions"):
            parts.append(f"Known conditions: {', '.join(profile['conditions'])}")
        if profile.get("allergies"):
            parts.append(f"⚠️ ALLERGIES: {', '.join(profile['allergies'])}")
        if profile.get("medications"):
            parts.append(f"Current medications: {', '.join(profile['medications'])}")
        if not parts:
            return ""
        return "PATIENT PROFILE (adjust all advice accordingly):\n" + " | ".join(parts)

    @staticmethod
    def _parse_health_meta(raw: str) -> tuple:
        """Extract HEALTH_META JSON from AI response."""
        meta = {
            "severity": "mild",
            "urgency": "self_care",
            "body_system": "general",
            "confidence": "medium",
            "needs_doctor": False,
            "emergency": False,
            "specialist": None,
            "suggested_tests": [],
            "followup_questions": [],
            "home_care_steps": [],
        }
        lines = raw.strip().splitlines()
        clean_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("HEALTH_META:"):
                try:
                    json_str = stripped.replace("HEALTH_META:", "", 1).strip()
                    parsed = json.loads(json_str)
                    meta.update(parsed)
                except (json.JSONDecodeError, ValueError):
                    pass
            else:
                clean_lines.append(line)
        return "\n".join(clean_lines).strip(), meta


# Singleton
ai_service = AIService()
