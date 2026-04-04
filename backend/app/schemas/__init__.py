"""
app/schemas/__init__.py — All Pydantic request/response models
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# ── Auth ──────────────────────────────────────────────
class SignupRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=200)
    password: str = Field(..., min_length=6, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address.")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=200)
    password: str = Field(..., min_length=1, max_length=100)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# ── Chat ──────────────────────────────────────────────
VALID_LANGUAGES = {"en", "hi", "gu", "mr", "ta", "te", "bn", "kn"}


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: List[ChatMessage] = Field(default_factory=list, max_length=20)
    language: Optional[str] = "en"
    conversation_id: Optional[str] = None   # client-side tracking; stored in DB if present

    @field_validator("message")
    @classmethod
    def strip_message(cls, v: str) -> str:
        return v.strip()

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> str:
        if v is None:
            return "en"
        lang = v.strip().lower()[:2]
        if lang not in VALID_LANGUAGES:
            return "en"  # silent fallback — never reject a query for bad lang
        return lang


class DoctorUpsell(BaseModel):
    show: bool
    message: str
    specialty: Optional[str] = None
    price_inr: int


class RiskAssessment(BaseModel):
    risk_score: int
    risk_level: str          # low / medium / high / critical
    risk_color: str
    risk_icon: str
    recommended_action: str
    action_steps: List[str]


class ChatResponse(BaseModel):
    # Primary response fields — both names so old & new frontend code works
    reply: str
    response: Optional[str] = None          # alias consumed by frontend
    message: Optional[str] = None           # fallback alias
    model: str = "groq"
    tokens_used: Optional[int] = None
    response_ms: Optional[int] = None

    # Clinical metadata
    severity: str = "mild"
    urgency_level: Optional[int] = None     # 1=self-care … 5=emergency (frontend banner)
    health_score: Optional[int] = None
    needs_doctor: bool = False
    emergency: bool = False
    body_system: Optional[str] = None
    confidence_score: Optional[int] = None
    cached: bool = False
    wiki_context: Optional[str] = None
    conversation_id: Optional[str] = None   # echoed back for UI thread tracking

    # Action guidance
    suggested_actions: List[str] = []       # quick action buttons shown in chat
    quick_replies: List[str] = []           # smart reply suggestions
    doctor_upsell: Optional[DoctorUpsell] = None
    risk_assessment: Optional[RiskAssessment] = None
    free_queries_left: Optional[int] = None

    # Clinical Intelligence Engine fields
    detected_symptoms: List[str] = []
    differentials: List[dict] = []
    followup_question: Optional[str] = None
    intent: Optional[str] = None

    def model_post_init(self, __context) -> None:
        # Populate frontend aliases from reply
        if self.response is None:
            object.__setattr__(self, 'response', self.reply)
        if self.message is None:
            object.__setattr__(self, 'message', self.reply)


# ── Health Profile ────────────────────────────────────
class HealthProfileRequest(BaseModel):
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    height_cm: Optional[int] = Field(None, ge=50, le=250)
    weight_kg: Optional[int] = Field(None, ge=1, le=300)
    # Phase 2.2: max 20 items, 100 chars each
    conditions: List[str] = Field(default_factory=list, max_length=20)
    allergies: List[str] = Field(default_factory=list, max_length=20)
    medications: List[str] = Field(default_factory=list, max_length=20)
    language: str = "en"

    @field_validator("conditions", "allergies", "medications", mode="before")
    @classmethod
    def trim_list_items(cls, v: List) -> List:
        if not isinstance(v, list):
            return []
        return [str(item)[:100].strip() for item in v[:20] if item]

    @field_validator("language")
    @classmethod
    def validate_profile_lang(cls, v: str) -> str:
        lang = (v or "en").strip().lower()[:2]
        return lang if lang in VALID_LANGUAGES else "en"

    def model_post_init(self, __context) -> None:
        """BMI sanity check: flag implausible height/weight combinations."""
        if self.height_cm and self.weight_kg:
            bmi = self.weight_kg / ((self.height_cm / 100) ** 2)
            if bmi < 10 or bmi > 80:
                # Log suspicious values — don't reject, just note for audit
                import logging
                logging.getLogger("arogyaai.schemas").warning(
                    "Suspicious BMI %.1f (height=%dcm weight=%dkg) — accepting anyway.",
                    bmi, self.height_cm, self.weight_kg,
                )


# ── Family ────────────────────────────────────────────
class FamilyMemberRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    relation: str = Field(..., pattern="^(parent|child|spouse|sibling|other)$")
    age: int = Field(..., ge=0, le=120)
    gender: Optional[str] = None
    conditions: List[str] = []


# ── Drug / Medical ────────────────────────────────────
class DrugSearchRequest(BaseModel):
    drug_name: str = Field(..., min_length=2, max_length=100)

    @field_validator("drug_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class MedicalInfoRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=200)


# ── Health Card ───────────────────────────────────────
class HealthScoreCard(BaseModel):
    user_id: str
    score: int
    streak_days: int
    consultations: int
    top_concern: Optional[str] = None
    share_message: str
    whatsapp_url: str


# ── User Profile (response) ───────────────────────────
class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    is_premium: bool
    plan: str
    created_at: Optional[str] = None
