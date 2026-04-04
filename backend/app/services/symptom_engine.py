"""
app/services/symptom_engine.py — Clinical Intelligence Engine
Symptom NER, Intent Detection, Differential Diagnosis, Follow-up question generation.
This powers the multi-agent pipeline behind every chat message.
"""
from __future__ import annotations
import re
import logging
from typing import Optional

logger = logging.getLogger("arogyaai.symptom")


# ── SYMPTOM LEXICON ─────────────────────────────────────────────────────────
# Covers English, common Hindi/Gujarati transliteration
SYMPTOM_LEXICON: dict[str, str] = {
    # Fever family
    "fever": "fever", "bukhar": "fever", "bukhaar": "fever", "tapi": "fever",
    "high temperature": "fever", "temperature": "fever", "garmi": "fever",
    # Pain
    "headache": "headache", "sir dard": "headache", "sir mein dard": "headache",
    "sar dard": "headache", "mathunu dukhe": "headache",
    "chest pain": "chest_pain", "sine mein dard": "chest_pain", "chhati mein dard": "chest_pain",
    "back pain": "back_pain", "kamar dard": "back_pain", "peeth dard": "back_pain",
    "stomach pain": "abdominal_pain", "pet dard": "abdominal_pain",
    "pet mein dard": "abdominal_pain", "pait mein dard": "abdominal_pain",
    "joint pain": "joint_pain", "jodo mein dard": "joint_pain",
    "throat pain": "throat_pain", "gale mein dard": "throat_pain",
    # Respiratory
    "cough": "cough", "khansi": "cough", "khaansi": "cough",
    "cold": "cold", "sardi": "cold", "zukam": "cold", "nasal": "cold",
    "breathless": "breathlessness", "saans nahi": "breathlessness",
    "difficulty breathing": "breathlessness", "saans lene mein takleef": "breathlessness",
    "shortness of breath": "breathlessness",
    # GI
    "diarrhea": "diarrhea", "loose motion": "diarrhea", "dast": "diarrhea",
    "vomiting": "vomiting", "ulti": "vomiting",
    "nausea": "nausea", "ji michlana": "nausea", "ji michlaana": "nausea",
    "constipation": "constipation", "kabz": "constipation",
    "acidity": "acidity", "gas": "acidity", "pet mein jalan": "acidity",
    # Skin
    "rash": "rash", "daane": "rash", "itching": "itching", "khujli": "itching",
    "swelling": "swelling", "sujan": "swelling",
    # Neuro
    "dizziness": "dizziness", "chakkar": "dizziness", "chakkar aana": "dizziness",
    "weakness": "weakness", "kamzori": "weakness", "thakan": "fatigue",
    "fatigue": "fatigue", "tired": "fatigue",
    "numbness": "numbness", "sun hojaana": "numbness",
    # Cardiac
    "palpitations": "palpitations", "dil ki tez dhadkan": "palpitations",
    "heart racing": "palpitations",
    # Special
    "blood": "bleeding", "khoon": "bleeding", "bleeding": "bleeding",
    "seizure": "seizure", "fits": "seizure", "daura": "seizure",
    "unconscious": "loss_of_consciousness", "behosh": "loss_of_consciousness",
}

# ── DURATION PATTERNS ────────────────────────────────────────────────────────
DURATION_PATTERNS = [
    (r"\b(\d+)\s*din\b", "days"),
    (r"\b(\d+)\s*day[s]?\b", "days"),
    (r"\b(\d+)\s*week[s]?\b", "weeks"),
    (r"\bkal se\b", "since_yesterday"),
    (r"\bdo din se\b|\btwo days\b", "2_days"),
    (r"\bteen din se\b|\bthree days\b|\b3 days\b", "3_days"),
    (r"\behfte se\b|\bone week\b", "1_week"),
    (r"\bkafi din se\b|\blong time\b|\bchronic\b", "chronic"),
    (r"\babhi\b|\bjust now\b|\bsuddenly\b|\bturant\b", "sudden"),
]

# ── INTENT DETECTION PATTERNS ─────────────────────────────────────────────────
INTENT_PATTERNS: list[tuple[str, str, str]] = [
    # (regex, intent_id, description)
    (r"\b(emergency|108|ambulance|help|chest pain|not breathing|unconscious|bleeding heavily)\b",
     "emergency", "Emergency / immediate danger"),
    (r"\b(diagnose|diagnosis|kya bimari|kya rog|kya hai mujhe|kya ho sakta)\b",
     "diagnosis_request", "Diagnosis request"),
    (r"\b(medicine|davai|tablet|treatment|ilaj|kya lein|kya khana chahiye|upay)\b",
     "treatment_advice", "Treatment/medicine advice"),
    (r"\b(diet|khaana|food|khana chahiye|nutrition|meal|breakfast|dinner)\b",
     "diet_advice", "Dietary advice"),
    (r"\b(exercise|yoga|workout|fitness|vyayam|running|walk|jogging)\b",
     "fitness_advice", "Fitness advice"),
    (r"\b(doctor|hospital|consult|appointment|jana chahiye|check up|ek baar)\b",
     "doctor_referral", "Doctor referral inquiry"),
    (r"\b(report|test result|blood report|lab|xray|mri|pathology)\b",
     "report_analysis", "Medical report analysis"),
    (r"\b(pregnant|pregnancy|garbi|bache ke liye|baby|garbhavati)\b",
     "pregnancy", "Pregnancy-related query"),
    (r"\b(mental|anxiety|depression|stress|tension|darr|worried|sad|udaas)\b",
     "mental_health", "Mental health query"),
    (r"\b(child|baby|bachha|bacchi|infant|newborn|navajaata)\b",
     "pediatric", "Pediatric query"),
    (r"\b(how|kaise|kya|why|kyun|when|kab|what is|explain|samjhao)\b",
     "information_request", "General health information"),
]

# ── FOLLOW-UP RULES ──────────────────────────────────────────────────────────
# When these symptoms are detected but no duration is given, ask for it
FOLLOWUP_RULES: dict[str, str] = {
    "fever": "Kitne din se bukhar hai? Aur temperature kitna hai?",
    "chest_pain": "Dard kaisa hai — daba hua, ched jaisa ya jalan? Haath/kaandhe mein bhi ja raha hai?",
    "breathlessness": "Kya saas lene mein takleef aarama se bhi hoti hai ya sirf chalne par?",
    "headache": "Sar dard kab se hai? Aur kahan dard hai — puri sar mein ya ek taraf?",
    "abdominal_pain": "Pet mein dard kahan hai — upar, neeche, ya beech mein? Khaane ke baad zyada hota hai?",
    "rash": "Daane kahan hai — kisi khaas jagah ya poore badan par? Khujli hoti hai?",
    "diarrhea": "Loose motion mein khoon hai kya? Aur kitni baar ho raha hai?",
    "joint_pain": "Kaun sa joint dard kar raha hai? Sujan bhi hai kya?",
}

# ── BODY SYSTEM MAPPING ───────────────────────────────────────────────────────
BODY_SYSTEM_MAP: dict[str, str] = {
    "fever": "general",
    "headache": "neurological",
    "chest_pain": "cardiovascular",
    "breathlessness": "respiratory",
    "cough": "respiratory",
    "cold": "respiratory",
    "abdominal_pain": "gastrointestinal",
    "vomiting": "gastrointestinal",
    "nausea": "gastrointestinal",
    "diarrhea": "gastrointestinal",
    "constipation": "gastrointestinal",
    "acidity": "gastrointestinal",
    "back_pain": "musculoskeletal",
    "joint_pain": "musculoskeletal",
    "rash": "dermatological",
    "itching": "dermatological",
    "swelling": "general",
    "dizziness": "neurological",
    "weakness": "general",
    "fatigue": "general",
    "palpitations": "cardiovascular",
    "bleeding": "general",
    "seizure": "neurological",
    "loss_of_consciousness": "neurological",
    "numbness": "neurological",
}


# ── DIFFERENTIAL DIAGNOSIS TABLE ────────────────────────────────────────────────
# symptom_set → [(condition, probability_weight, description)]
DIFFERENTIAL_TABLE: dict[frozenset, list[tuple[str, float, str]]] = {
    frozenset(["fever", "headache"]):
        [("Viral Fever", 0.55, "Most common cause in India — often self-limiting"),
         ("Dengue", 0.20, "Check platelets if fever > 3 days with joint pain"),
         ("Typhoid", 0.15, "If fever is step-wise rising over 3-5 days"),
         ("Malaria", 0.10, "If in endemic area or monsoon season")],
    frozenset(["fever", "cough"]):
        [("Common Cold / URI", 0.50, "Viral respiratory infection — usually resolves in 5-7 days"),
         ("Influenza", 0.25, "Body ache + sudden onset fever with cough"),
         ("COVID-19", 0.15, "If loss of smell/taste, fatigue, or recent exposure"),
         ("Pneumonia", 0.10, "If fever > 3 days with productive cough")],
    frozenset(["chest_pain"]):
        [("Musculoskeletal Pain", 0.40, "Common — worsens on touch/movement"),
         ("Acidity/GERD", 0.25, "Burning type, worse after eating"),
         ("Cardiac (STEMI/Angina)", 0.20, "EMERGENCY if radiating to arm/jaw, sweating"),
         ("Pleurisy", 0.10, "Worsens with deep breath")],
    frozenset(["abdominal_pain", "vomiting"]):
        [("Gastroenteritis", 0.45, "Food poisoning or stomach infection — very common"),
         ("Appendicitis", 0.20, "If pain is lower right and constant"),
         ("Acidity / GERD", 0.20, "Upper abdominal burning pain"),
         ("Gallstone", 0.15, "Upper right pain after fatty meal")],
    frozenset(["diarrhea", "vomiting"]):
        [("Food Poisoning", 0.50, "Sudden onset, often within 6h of eating"),
         ("Gastroenteritis", 0.30, "Viral / bacterial gut infection"),
         ("Cholera", 0.10, "Severe rice-water diarrhea — emergency in endemic zones"),
         ("Typhoid", 0.10, "With fever and step-wise progression")],
    frozenset(["headache", "dizziness"]):
        [("Tension Headache", 0.45, "Most common — stress, poor sleep, dehydration"),
         ("Migraine", 0.25, "Throbbing, one-sided, with light/sound sensitivity"),
         ("Hypertension", 0.20, "Check BP — headache at base of skull"),
         ("Anemia", 0.10, "Especially in women — fatigue + dizziness")],
    frozenset(["rash", "fever"]):
        [("Viral Exanthem", 0.35, "Many viruses cause rash + fever"),
         ("Dengue", 0.25, "Dengue rash after 3-4 days of fever"),
         ("Chikungunya", 0.20, "Severe joint pain + rash"),
         ("Chickenpox", 0.15, "Itchy blisters — highly contagious")],
}


class SymptomEngine:
    """
    Clinical Intelligence Engine:
    1. Extracts symptoms from natural language (NER)
    2. Detects intent
    3. Extracts duration
    4. Generates differential diagnosis
    5. Suggests follow-up questions when critical info is missing
    """

    def analyze(self, message: str, history: list[dict] | None = None) -> dict:
        msg_lower = message.lower()
        history = history or []

        # -- Symptom extraction --
        symptoms = self._extract_symptoms(msg_lower)

        # -- Duration extraction --
        duration = self._extract_duration(msg_lower)

        # -- Intent detection --
        intent = self._detect_intent(msg_lower)

        # -- Body system --
        body_system = self._infer_body_system(symptoms)

        # -- Differential diagnosis --
        differentials = self._build_differential(symptoms)

        # -- Follow-up question --
        followup = self._generate_followup(symptoms, duration, history)

        # -- Novelty detection (new symptom vs. continuation) --
        prior_symptoms = self._extract_prior_symptoms(history)
        new_symptoms = [s for s in symptoms if s not in prior_symptoms]

        logger.debug(
            "[SymptomEngine] symptoms=%s intent=%s duration=%s system=%s",
            symptoms, intent, duration, body_system
        )

        return {
            "symptoms": symptoms,
            "new_symptoms": new_symptoms,
            "intent": intent,
            "duration_raw": duration,
            "duration_days": self._duration_to_days(duration),
            "body_system": body_system,
            "differentials": differentials,
            "followup_question": followup,
            "symptom_count": len(symptoms),
        }

    # ── Private methods ─────────────────────────────────────────────────────

    def _extract_symptoms(self, msg: str) -> list[str]:
        found = set()
        for term, canonical in SYMPTOM_LEXICON.items():
            if term in msg:
                found.add(canonical)
        return sorted(found)

    def _detect_intent(self, msg: str) -> str:
        for pattern, intent_id, _ in INTENT_PATTERNS:
            if re.search(pattern, msg, re.IGNORECASE):
                return intent_id
        return "general_query"

    def _extract_duration(self, msg: str) -> Optional[str]:
        for pattern, label in DURATION_PATTERNS:
            m = re.search(pattern, msg, re.IGNORECASE)
            if m:
                if m.lastindex and m.lastindex >= 1:
                    qty = m.group(1)
                    return f"{qty}_{label}"
                return label
        return None

    def _duration_to_days(self, duration_raw: Optional[str]) -> Optional[int]:
        if not duration_raw:
            return None
        mapping = {
            "since_yesterday": 1, "2_days": 2, "3_days": 3, "1_week": 7, "chronic": 21,
            "sudden": 0,
        }
        if duration_raw in mapping:
            return mapping[duration_raw]
        try:
            parts = duration_raw.split("_")
            n = int(parts[0])
            unit = parts[1] if len(parts) > 1 else "days"
            if unit == "weeks":
                return n * 7
            return n
        except (ValueError, IndexError):
            return None

    def _infer_body_system(self, symptoms: list[str]) -> str:
        counts: dict[str, int] = {}
        for s in symptoms:
            system = BODY_SYSTEM_MAP.get(s, "general")
            counts[system] = counts.get(system, 0) + 1
        if not counts:
            return "general"
        return max(counts, key=counts.__getitem__)

    def _build_differential(self, symptoms: list[str]) -> list[dict]:
        if not symptoms:
            return []
        s_set = frozenset(symptoms)
        best_match: list[tuple[str, float, str]] = []
        best_overlap = 0
        for key, conditions in DIFFERENTIAL_TABLE.items():
            overlap = len(key & s_set)
            if overlap > best_overlap:
                best_overlap = overlap
                best_match = conditions
        if not best_match:
            return []
        # Normalize to dicts
        return [
            {"condition": c, "probability": round(p, 2), "note": n}
            for c, p, n in best_match
        ]

    def _generate_followup(
        self,
        symptoms: list[str],
        duration: Optional[str],
        history: list[dict],
    ) -> Optional[str]:
        """
        Returns a single focused follow-up question if critical info is missing.
        Only asks ONE question at a time.
        """
        # Don't ask follow-ups if we already have duration and more than 2 conversation turns
        if duration and len(history) > 2:
            return None
        # Don't ask if conversation is already deep (>6 turns = enough context)
        if len(history) > 6:
            return None
        for symptom in symptoms:
            if symptom in FOLLOWUP_RULES and not duration:
                return FOLLOWUP_RULES[symptom]
        return None

    def _extract_prior_symptoms(self, history: list[dict]) -> set[str]:
        prior: set[str] = set()
        for msg in history:
            if msg.get("role") == "user":
                prior.update(self._extract_symptoms(msg.get("content", "").lower()))
        return prior


# ── Singleton ─────────────────────────────────────────────────────────────────
symptom_engine = SymptomEngine()
