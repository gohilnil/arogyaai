"""
app/services/risk_engine.py — Clinical Risk Stratification Engine
Computes composite risk scores from symptoms, duration, red flags, and personal history.
"""
from typing import Optional


# ── Red Flag Symptom Patterns ────────────────────────────────────
RED_FLAG_PATTERNS = {
    "cardiac": [
        "chest pain", "chest tightness", "left arm pain", "jaw pain",
        "heart attack", "palpitations with dizziness", "sudden sweating",
    ],
    "neurological": [
        "sudden severe headache", "face drooping", "arm weakness", "slurred speech",
        "loss of consciousness", "seizure", "fits", "stroke", "paralysis",
    ],
    "respiratory": [
        "cannot breathe", "can't breathe", "choking", "blue lips",
        "severe difficulty breathing", "not breathing", "stopped breathing",
    ],
    "bleeding": [
        "vomiting blood", "blood in stool", "heavy bleeding", "uncontrolled bleeding",
        "coughing blood", "blood in urine sudden large",
    ],
    "pediatric": [
        "infant fever", "baby not breathing", "child seizure", "newborn unwell",
        "baby blue", "child unconscious",
    ],
    "toxicology": [
        "overdose", "poisoning", "swallowed chemicals", "drug overdose",
    ],
}

# ── Symptom Severity Weights ──────────────────────────────────────
SYMPTOM_WEIGHTS = {
    # High-risk
    "chest pain": 40, "difficulty breathing": 35, "seizure": 45,
    "unconscious": 50, "stroke": 50, "paralysis": 45, "vomiting blood": 40,
    "heavy bleeding": 40, "overdose": 50, "poisoning": 50,
    # Medium-risk
    "high fever": 20, "severe headache": 18, "persistent vomiting": 15,
    "severe abdominal pain": 18, "blood in urine": 15, "jaundice": 15,
    "sudden weight loss": 12, "chronic cough": 10,
    # Low-risk
    "mild fever": 5, "cold": 3, "cough": 5, "headache": 8,
    "back pain": 6, "stomach pain": 8, "diarrhea": 6, "rash": 5,
}

# ── Chronic Condition Risk Multipliers ────────────────────────────
CONDITION_RISK_MULTIPLIERS = {
    "diabetes": 1.3,
    "hypertension": 1.25,
    "heart disease": 1.5,
    "asthma": 1.2,
    "copd": 1.35,
    "kidney disease": 1.3,
    "liver disease": 1.3,
    "cancer": 1.4,
    "hiv": 1.35,
    "tb": 1.3,
    "pregnancy": 1.2,
    "immunocompromised": 1.45,
}

# ── Age Risk Factors ──────────────────────────────────────────────
def _age_risk_modifier(age: Optional[int]) -> float:
    if age is None:
        return 1.0
    if age < 2:
        return 1.6   # Infants — very high
    if age < 12:
        return 1.3   # Children
    if age > 70:
        return 1.4   # Elderly
    if age > 60:
        return 1.2
    return 1.0


class RiskStratificationEngine:
    """
    Computes a clinical risk score (0–100) from multiple factors:
    - Symptom severity
    - Red flag detection
    - Duration of illness
    - Personal health conditions
    - Age
    
    Outputs structured risk assessment with recommended action level.
    """

    def compute(
        self,
        message: str,
        severity: str,
        emergency: bool,
        needs_doctor: bool,
        duration_days: Optional[int] = None,
        user_profile: Optional[dict] = None,
    ) -> dict:
        if emergency:
            return self._build_result(95, "critical", "Emergency Room / Call 108 Immediately", [
                "Call 108 immediately",
                "Do not wait — this is a medical emergency",
                "Keep the person calm; do not give food/water",
            ])

        # ── Base score from symptom severity ─────────────────
        score = 0
        msg_lower = message.lower()
        for symptom, weight in SYMPTOM_WEIGHTS.items():
            if symptom in msg_lower:
                score += weight

        # ── Cap base at 60 (severity adjusts further) ────────
        score = min(score, 60)

        # ── Severity adjustment ───────────────────────────────
        if severity == "serious":
            score = max(score, 45)
            score += 15
        elif severity == "moderate":
            score = max(score, 25)
            score += 8
        elif severity == "mild":
            score = max(score, 5)

        # ── Duration penalty ──────────────────────────────────
        if duration_days:
            if duration_days > 14:
                score += 15
            elif duration_days > 7:
                score += 10
            elif duration_days > 3:
                score += 5

        # ── Chronic condition multipliers ─────────────────────
        multiplier = 1.0
        if user_profile and user_profile.get("conditions"):
            for cond in user_profile["conditions"]:
                cond_lower = cond.lower()
                for keyword, mult in CONDITION_RISK_MULTIPLIERS.items():
                    if keyword in cond_lower:
                        multiplier = max(multiplier, mult)  # Take highest

        score = min(100, int(score * multiplier))

        # ── Age modifier ──────────────────────────────────────
        age = user_profile.get("age") if user_profile else None
        age_mod = _age_risk_modifier(age)
        score = min(100, int(score * age_mod))

        # ── Needs doctor boost ────────────────────────────────
        if needs_doctor:
            score = max(score, 35)

        score = min(100, max(0, score))

        # ── Classify and recommend ────────────────────────────
        return self._classify(score)

    def _classify(self, score: int) -> dict:
        if score >= 75:
            return self._build_result(score, "high", "Seek Emergency Care / Call 108", [
                "Go to nearest hospital or call 108 immediately",
                "Do not delay — symptoms suggest serious risk",
                "Inform family members of the situation",
                "Bring all current medications with you",
            ])
        elif score >= 50:
            return self._build_result(score, "high", "Doctor Consultation Urgent (Within 24 hrs)", [
                "Visit a doctor or clinic within the next 24 hours",
                "Monitor symptoms closely — if worsening, call 108",
                "Stay hydrated and rest completely",
                "Do not self-medicate with antibiotics or steroids",
            ])
        elif score >= 30:
            return self._build_result(score, "medium", "Doctor Consultation Recommended (2–3 days)", [
                "Schedule a doctor appointment within 2–3 days",
                "Follow home care remedies in the meantime",
                "Monitor for red flag symptoms (breathing, chest pain)",
                "Stay hydrated; take OTC medication if appropriate",
            ])
        elif score >= 15:
            return self._build_result(score, "medium", "Monitor at Home (24–48 hrs)", [
                "Home care with rest and fluids is appropriate for now",
                "Track symptoms — if no improvement in 48 hrs, see doctor",
                "Use safe OTC medications (ORS, paracetamol, antacids)",
                "Avoid strenuous activity and eat light meals",
            ])
        else:
            return self._build_result(score, "low", "Home Care Sufficient", [
                "Rest and stay well-hydrated",
                "Home remedies and safe OTC medications are adequate",
                "Monitor and see a doctor only if symptoms worsen",
                "Maintain good diet and sleep schedule",
            ])

    @staticmethod
    def _build_result(score: int, level: str, action: str, steps: list) -> dict:
        level_colors = {"low": "#22c55e", "medium": "#f59e0b", "high": "#ef4444", "critical": "#dc2626"}
        level_icons = {"low": "🟢", "medium": "🟡", "high": "🔴", "critical": "🚨"}
        return {
            "risk_score": score,
            "risk_level": level,
            "risk_color": level_colors.get(level, "#6b7280"),
            "risk_icon": level_icons.get(level, "⚪"),
            "recommended_action": action,
            "action_steps": steps,
        }


# ── Singleton ─────────────────────────────────────────────────────
risk_engine = RiskStratificationEngine()
