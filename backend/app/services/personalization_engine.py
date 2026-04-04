"""
app/services/personalization_engine.py — Persistent User Health Personalization Engine
Builds a rich user context object to inform AI decisions.
"""
from __future__ import annotations
import logging
from typing import Optional
from datetime import date
from calendar import month_name

logger = logging.getLogger("arogyaai.personalization")


# ── Seasonal Disease Patterns (India) ─────────────────────────────────────────
SEASONAL_RISKS: dict[int, list[str]] = {
    # Month → [risk diseases]
    1:  ["respiratory infections", "cold", "asthma exacerbation"],
    2:  ["respiratory infections", "seasonal allergy", "viral fever"],
    3:  ["seasonal allergy", "heat exhaustion early"],
    4:  ["heat exhaustion", "dehydration", "skin rashes"],
    5:  ["heat stroke", "prickly heat", "dehydration", "food poisoning"],
    6:  ["heat stroke", "dengue early", "leptospirosis", "food poisoning"],
    7:  ["dengue", "malaria", "leptospirosis", "cholera", "typhoid", "chikungunya"],
    8:  ["dengue", "malaria", "typhoid", "hepatitis A/E", "gastroenteritis"],
    9:  ["dengue", "malaria", "chikungunya", "eye infections"],
    10: ["dengue", "viral fever", "respiratory infections"],
    11: ["respiratory infections", "air pollution effects", "asthma"],
    12: ["respiratory infections", "cold", "asthma", "joint pain (cold)"],
}

# ── Age-Related Risk Context ──────────────────────────────────────────────────
def _age_context(age: Optional[int]) -> str:
    if age is None:
        return ""
    if age <= 2:
        return (
            "INFANT: Fever >38°C = Emergency. Any breathing difficulty = Emergency. "
            "Always refer to Pediatrician. Do not suggest any self-medication."
        )
    if age <= 12:
        return (
            "CHILD: Dose adjustments needed for all medications. "
            "Normal temp up to 38°C. Weight-based dosing required."
        )
    if age <= 18:
        return "ADOLESCENT: Consider puberty-related changes. Mental health screening relevant."
    if age >= 70:
        return (
            "ELDERLY (70+): Very high risk patient. Polypharmacy common — caution with drug interactions. "
            "Fall risk, dehydration risk, atypical disease presentation common. "
            "Symptoms may be muted or masked. Lower threshold for doctor referral."
        )
    if age >= 60:
        return (
            "SENIOR: Increased risk for cardiovascular, metabolic, and bone diseases. "
            "Check BP regularly. Doctor consultation threshold should be lower."
        )
    return ""


# ── Condition-Specific Flags ──────────────────────────────────────────────────
CONDITION_FLAGS: dict[str, str] = {
    "diabetes": (
        "DIABETES ACTIVE: Monitor blood sugar during illness. "
        "Fever/infection can spike glucose. Avoid sugary foods+drinks. "
        "Never skip medication. Signs of DKA = Emergency."
    ),
    "hypertension": (
        "HYPERTENSION: Extra caution with pain medications (NSAIDs raise BP). "
        "Monitor BP during illness. Headache + high BP = urgent care."
    ),
    "asthma": (
        "ASTHMA PATIENT: Respiratory infections can trigger acute exacerbation. "
        "Ensure rescue inhaler available. Cold air, dust, smoke = triggers."
    ),
    "heart disease": (
        "CARDIAC HISTORY: ANY chest pain = Emergency. "
        "Extra vigilance with respiratory and exertion symptoms. "
        "NSAIDs contraindicated — use paracetamol only."
    ),
    "kidney disease": (
        "KIDNEY DISEASE: Avoid NSAIDs (ibuprofen, naproxen) — nephrotoxic. "
        "Hydration critical but don't overload. Many drugs need dose adjustment."
    ),
    "pregnancy": (
        "PREGNANT: Most medications contraindicated. "
        "Only paracetamol for fever (never ibuprofen). "
        "Any fever >38°C = must see doctor. Vaginal bleeding = Emergency."
    ),
    "liver disease": (
        "LIVER DISEASE: Limit paracetamol to max 2g/day. "
        "Avoid all herbal remedies without doctor approval. "
        "Jaundice worsening = Emergency."
    ),
    "thyroid": (
        "THYROID PATIENT: Ensure consistent medication timing. "
        "Fatigue and weight changes may reflect thyroid dysfunction."
    ),
    "tb": (
        "TB PATIENT: Ensure medication compliance — never skip doses. "
        "Cough with blood = Emergency. Fever in TB = contact doctor."
    ),
    "immunocompromised": (
        "IMMUNOCOMPROMISED: ANY fever = urgent medical evaluation. "
        "Infections escalate rapidly — low threshold for emergency."
    ),
}


class PersonalizationEngine:
    """
    Builds a rich, personalized context string for the AI from:
    - Health profile (age, gender, conditions, allergies, medications)
    - Seasonal disease risk (current month in India)
    - Recurring symptom patterns (from history)
    """

    def build_context(
        self,
        user_profile: Optional[dict],
        conversation_history: Optional[list[dict]] = None,
        language: str = "en",
    ) -> str:
        """Returns a formatted context string to inject into the AI system prompt."""
        if not user_profile:
            return self._seasonal_context_only()

        parts: list[str] = ["=== PERSONALIZED PATIENT CONTEXT ==="]

        # ── Demographics ─────────────────────────────────────────────────────
        demo_parts: list[str] = []
        if user_profile.get("age"):
            demo_parts.append(f"Age: {user_profile['age']} years")
        if user_profile.get("gender"):
            demo_parts.append(f"Gender: {user_profile['gender'].title()}")
        if user_profile.get("blood_group"):
            demo_parts.append(f"Blood Group: {user_profile['blood_group']}")
        if user_profile.get("weight_kg") and user_profile.get("height_cm"):
            h_m = user_profile["height_cm"] / 100
            bmi = user_profile["weight_kg"] / (h_m ** 2)
            bmi_cat = (
                "Underweight" if bmi < 18.5 else
                "Normal" if bmi < 25 else
                "Overweight" if bmi < 30 else "Obese"
            )
            demo_parts.append(
                f"BMI: {bmi:.1f} ({bmi_cat}) — {user_profile['weight_kg']}kg / {user_profile['height_cm']}cm"
            )
        if demo_parts:
            parts.append("DEMOGRAPHICS: " + " | ".join(demo_parts))

        # ── Age-specific guidance ─────────────────────────────────────────────
        age_ctx = _age_context(user_profile.get("age"))
        if age_ctx:
            parts.append(f"AGE GUIDANCE: {age_ctx}")

        # ── Conditions ───────────────────────────────────────────────────────
        conditions = user_profile.get("conditions", [])
        if conditions:
            parts.append(f"KNOWN CONDITIONS: {', '.join(conditions)}")
            # Inject specific flags for known conditions
            for cond in conditions:
                cond_lower = cond.lower()
                for keyword, flag in CONDITION_FLAGS.items():
                    if keyword in cond_lower:
                        parts.append(f"⚠️ {flag}")
                        break

        # ── Allergies ────────────────────────────────────────────────────────
        allergies = user_profile.get("allergies", [])
        if allergies:
            parts.append(f"🚫 ALLERGIES (NEVER suggest): {', '.join(allergies)}")

        # ── Medications ──────────────────────────────────────────────────────
        medications = user_profile.get("medications", [])
        if medications:
            parts.append(f"CURRENT MEDICATIONS: {', '.join(medications)} — check for interactions")

        # ── Recurring symptoms from history ───────────────────────────────────
        recurring = self._detect_recurring(conversation_history)
        if recurring:
            parts.append(f"RECURRING SYMPTOMS (past chats): {', '.join(recurring)} — increase concern threshold")

        # ── Seasonal risk ─────────────────────────────────────────────────────
        seasonal = self._seasonal_context_only(include_header=False)
        if seasonal:
            parts.append(seasonal)

        # ── Language preference ───────────────────────────────────────────────
        lang_names = {
            "hi": "Hindi", "gu": "Gujarati", "mr": "Marathi",
            "ta": "Tamil", "te": "Telugu", "en": "English"
        }
        lang_name = lang_names.get(language, language)
        parts.append(f"LANGUAGE: Respond in {lang_name}")

        parts.append("=== END CONTEXT ===")
        return "\n".join(parts)

    def compute_health_risk_modifier(self, user_profile: Optional[dict]) -> float:
        """Returns a 1.0-2.0 multiplier based on patient risk factors."""
        if not user_profile:
            return 1.0
        modifier = 1.0
        age = user_profile.get("age")
        if age:
            if age < 2 or age > 80:
                modifier *= 1.5
            elif age < 12 or age > 65:
                modifier *= 1.2
        conditions = user_profile.get("conditions", [])
        high_risk = {"heart disease", "kidney disease", "liver disease", "cancer",
                     "immunocompromised", "hiv", "tb"}
        medium_risk = {"diabetes", "hypertension", "asthma", "copd", "pregnancy"}
        for c in conditions:
            c_lower = c.lower()
            if any(hr in c_lower for hr in high_risk):
                modifier *= 1.4
                break
            if any(mr in c_lower for mr in medium_risk):
                modifier *= 1.2
                break
        return min(modifier, 2.0)

    # ── Private ───────────────────────────────────────────────────────────────

    def _seasonal_context_only(self, include_header: bool = True) -> str:
        month = date.today().month
        risks = SEASONAL_RISKS.get(month, [])
        if not risks:
            return ""
        header = "SEASONAL RISK" if include_header else "SEASONAL RISK (India)"
        return f"{header} ({month_name[month]}): Elevated risk for {', '.join(risks[:3])}. Adjust differential accordingly."

    def _detect_recurring(self, history: Optional[list[dict]]) -> list[str]:
        """Detect symptoms that appear in multiple conversation turns."""
        if not history or len(history) < 4:
            return []
        from collections import Counter
        counts: Counter = Counter()
        for msg in history:
            if msg.get("role") == "user":
                text = msg.get("content", "").lower()
                from app.services.symptom_engine import SYMPTOM_LEXICON
                for term, canonical in SYMPTOM_LEXICON.items():
                    if term in text:
                        counts[canonical] += 1
        return [s for s, c in counts.items() if c >= 2]


# ── Singleton ─────────────────────────────────────────────────────────────────
personalization_engine = PersonalizationEngine()
