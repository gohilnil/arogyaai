"""
╔══════════════════════════════════════════════════════════════╗
║  ArogyaAI — Production Backend  v5.0.0                      ║
║  Stack : FastAPI · Groq (llama-3.3-70b) · OpenFDA · Wiki    ║
╚══════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import os
import time
import logging
import pathlib
import base64
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from groq import AsyncGroq
from pydantic import BaseModel, Field, field_validator

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("arogyaai")


# ══════════════════════════════════════════════
# § 1  CONFIGURATION
# ══════════════════════════════════════════════
class Config:
    GROQ_API_KEY:        str   = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL:          str   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    MAX_TOKENS:          int   = 1800
    TEMPERATURE:         float = 0.50
    RATE_LIMIT_REQUESTS: int   = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
    RATE_LIMIT_WINDOW:   int   = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    PORT:                int   = int(os.getenv("PORT", "8000"))
    OPENFDA_BASE:        str   = "https://api.fda.gov/drug"
    WIKI_API:            str   = "https://en.wikipedia.org/api/rest_v1/page/summary"
    APP_NAME:            str   = "ArogyaAI"
    APP_VERSION:         str   = "5.0.0"


# ══════════════════════════════════════════════
# § 2  SYSTEM PROMPT — Doctor-Grade AI
# ══════════════════════════════════════════════
SYSTEM_PROMPT = """You are ArogyaAI — an advanced, compassionate AI health assistant for Indian users.

You think and communicate like an experienced, empathetic MBBS-level general physician with 15+ years of practice. You seamlessly blend evidence-based modern medicine with trusted traditional Indian practices (Ayurveda, Unani, home remedies).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE QUALITY RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Always open with a warm, empathetic acknowledgment of the user's discomfort.
• Assign a SEVERITY LEVEL: 🟢 Mild | 🟡 Moderate | 🔴 Serious
• Assign a CONFIDENCE: High / Medium / Low
• Ask ONE focused follow-up question if truly critical info is missing.
• List 2–4 probable causes clearly marked as possibilities, not diagnoses.
• Give actionable, culturally appropriate home remedies using Indian ingredients.
• Recommend OTC medicines only when clearly appropriate (ORS, paracetamol, antacids, antihistamines).
• Provide diet & lifestyle advice relevant to Indian context.
• State clearly when in-person consultation is needed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INDIAN CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Know Indian medicinal foods: turmeric, ginger, tulsi, neem, amla, ashwagandha, triphala, giloy, methi, jeera, ajwain, saunf, haldi, kadha.
• Know India-prevalent diseases: dengue, typhoid, malaria, chikungunya, TB, enteric fever, filariasis, leptospirosis, hand-foot-mouth disease.
• Emergency: 108 (ambulance), AIIMS helpline: 1800-11-7091.
• Respect socioeconomic diversity — suggest affordable remedies.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ABSOLUTE SAFETY RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Serious symptoms (chest pain, stroke signs, severe breathlessness, infant with high fever, seizures, severe bleeding, loss of consciousness) → IMMEDIATELY urge 108 / emergency room.
• NEVER recommend prescription antibiotics, steroids, opioids.
• NEVER diagnose definitively.
• End with a brief, warm AI disclaimer.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LANGUAGE RULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Pure Hindi (Devanagari) → reply fully in Hindi
• Pure Gujarati → reply fully in Gujarati
• English or mixed → reply in English
• Match the user's dominant language

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY RESPONSE FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Start with: A warm empathetic opening sentence addressing the person's concern.

Then include these EXACT section headers:

**SEVERITY:** [🟢 Mild / 🟡 Moderate / 🔴 Serious] — [one sentence explanation]

**🔍 Possible Causes**
2–4 likely causes in plain, non-scary language.

**✅ What You Can Do Now**
Specific home remedies, safe OTC options, rest/hydration advice. Use Indian ingredients and culturally familiar options.

**🍽️ Diet & Lifestyle**
What to eat, what to avoid, one key lifestyle tip. Keep it practical.

**🏥 When to See a Doctor**
Specific red-flag symptoms that require professional consultation. Be clear and reassuring.

Close with: A single warm disclaimer line reminding this is AI guidance, not a medical diagnosis."""


# ══════════════════════════════════════════════
# § 3  PYDANTIC MODELS
# ══════════════════════════════════════════════
class ChatMessage(BaseModel):
    role:    str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message:  str               = Field(..., min_length=1, max_length=1000)
    history:  list[ChatMessage] = Field(default_factory=list, max_length=20)
    language: Optional[str]     = Field(default="en")

    @field_validator("message")
    @classmethod
    def strip_message(cls, v: str) -> str:
        return v.strip()


class ChatResponse(BaseModel):
    reply:        str
    model:        str
    tokens_used:  Optional[int] = None
    response_ms:  Optional[int] = None
    wiki_context: Optional[str] = None
    severity:     Optional[str] = None


class DrugSearchRequest(BaseModel):
    drug_name: str = Field(..., min_length=2, max_length=100)

    @field_validator("drug_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class MedicalInfoRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=200)

    @field_validator("query")
    @classmethod
    def strip_query(cls, v: str) -> str:
        return v.strip()


# ══════════════════════════════════════════════
# § 4  RATE LIMITER
# ══════════════════════════════════════════════
class RateLimiter:
    def __init__(self, max_requests: int, window: int):
        self.max_requests = max_requests
        self.window       = window
        self._store: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, identifier: str) -> bool:
        now = time.time()
        self._store[identifier] = [
            ts for ts in self._store[identifier] if ts > now - self.window
        ]
        if len(self._store[identifier]) >= self.max_requests:
            return False
        self._store[identifier].append(now)
        return True


rate_limiter = RateLimiter(Config.RATE_LIMIT_REQUESTS, Config.RATE_LIMIT_WINDOW)


# ══════════════════════════════════════════════
# § 5  MEDICAL API SERVICE
# ══════════════════════════════════════════════
class MedicalAPIService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=8.0, follow_redirects=True)

    async def search_drug_fda(self, drug_name: str) -> dict:
        try:
            resp = await self.client.get(
                f"{Config.OPENFDA_BASE}/label.json",
                params={
                    "search": f'brand_name:"{drug_name}" OR generic_name:"{drug_name}"',
                    "limit":  3,
                },
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results:
                    r   = results[0]
                    ofd = r.get("openfda", {})
                    return {
                        "found":        True,
                        "brand_name":   ofd.get("brand_name",     ["Unknown"])[0],
                        "generic_name": ofd.get("generic_name",   ["Unknown"])[0],
                        "purpose":      (r.get("purpose",              [""])[0])[:500],
                        "warnings":     (r.get("warnings",             [""])[0])[:500],
                        "dosage":       (r.get("dosage_and_administration", [""])[0])[:500],
                        "manufacturer": ofd.get("manufacturer_name", [""])[0],
                        "source":       "OpenFDA Drug Label Database",
                    }
            return {"found": False}
        except Exception as exc:
            logger.warning("[FDA label] %s", exc)
            return {"found": False, "error": str(exc)}

    async def get_adverse_events(self, drug_name: str) -> dict:
        try:
            resp = await self.client.get(
                f"{Config.OPENFDA_BASE}/event.json",
                params={
                    "search": f'patient.drug.medicinalproduct:"{drug_name}"',
                    "count":  "patient.reaction.reactionmeddrapt.exact",
                    "limit":  5,
                },
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                return {
                    "found":            True,
                    "common_reactions": [r["term"] for r in results[:5]],
                    "source":           "FDA Adverse Event Reporting System (FAERS)",
                }
            return {"found": False}
        except Exception as exc:
            logger.warning("[FDA AE] %s", exc)
            return {"found": False}

    async def get_wikipedia_summary(self, condition: str) -> dict:
        try:
            term = condition.strip().replace(" ", "_").title()
            resp = await self.client.get(
                f"{Config.WIKI_API}/{term}",
                headers={"User-Agent": "ArogyaAI/5.0 (health assistant)"},
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("type") == "disambiguation":
                    return {"found": False}
                return {
                    "found":     True,
                    "title":     data.get("title", ""),
                    "summary":   data.get("extract", "")[:600],
                    "thumbnail": data.get("thumbnail", {}).get("source", ""),
                    "wiki_url":  data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                    "source":    "Wikipedia Medical Encyclopedia",
                }
            return {"found": False}
        except Exception as exc:
            logger.warning("[Wikipedia] %s", exc)
            return {"found": False}

    async def close(self):
        await self.client.aclose()


# ══════════════════════════════════════════════
# § 6  GROQ AI SERVICE
# ══════════════════════════════════════════════
class GroqAIService:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set. Get your FREE key at https://console.groq.com")
        self.client = AsyncGroq(api_key=api_key)
        self.model  = Config.GROQ_MODEL

    async def chat(
        self,
        user_message:  str,
        history:       list[ChatMessage],
        extra_context: str = "",
    ) -> tuple[str, int]:
        messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

        for msg in history[-16:]:
            messages.append({"role": msg.role, "content": msg.content})

        content = user_message
        if extra_context:
            content = (
                f"{user_message}\n\n"
                f"[Reference Data for context]:\n{extra_context}"
            )
        messages.append({"role": "user", "content": content})

        response = await self.client.chat.completions.create(
            model       = self.model,
            messages    = messages,
            max_tokens  = Config.MAX_TOKENS,
            temperature = Config.TEMPERATURE,
            stream      = False,
        )

        reply       = response.choices[0].message.content or ""
        tokens_used = response.usage.total_tokens if response.usage else 0
        return reply, tokens_used

    def extract_severity(self, reply: str) -> str:
        if "🔴" in reply or "Serious" in reply:
            return "serious"
        if "🟡" in reply or "Moderate" in reply:
            return "moderate"
        return "mild"


# ══════════════════════════════════════════════
# § 7  SERVICE REGISTRY
# ══════════════════════════════════════════════
groq_service:    Optional[GroqAIService]     = None
medical_service: Optional[MedicalAPIService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global groq_service, medical_service
    logger.info("🌿 Starting %s v%s …", Config.APP_NAME, Config.APP_VERSION)
    if not Config.GROQ_API_KEY:
        logger.error("⚠️  GROQ_API_KEY not set! Visit https://console.groq.com")
    try:
        groq_service    = GroqAIService(Config.GROQ_API_KEY)
        medical_service = MedicalAPIService()
        logger.info("✅ All services initialised.")
    except Exception as exc:
        logger.error("❌ Service init failed: %s", exc)
    yield
    if medical_service:
        await medical_service.close()
    logger.info("👋 ArogyaAI shutdown complete.")


# ══════════════════════════════════════════════
# § 8  FASTAPI APPLICATION
# ══════════════════════════════════════════════
app = FastAPI(
    title       = Config.APP_NAME,
    description = "AI-Powered Health Assistant for India",
    version     = Config.APP_VERSION,
    lifespan    = lifespan,
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

if pathlib.Path("static").exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")


# ══════════════════════════════════════════════
# § 9  MIDDLEWARE
# ══════════════════════════════════════════════
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    if request.url.path.startswith("/api/"):
        if not rate_limiter.is_allowed(client_ip):
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded. Please wait a moment.", "code": 429},
            )
    return await call_next(request)


# ══════════════════════════════════════════════
# § 10  ROUTES
# ══════════════════════════════════════════════
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_frontend():
    for path in ["templates/index.html", "index.html"]:
        try:
            return HTMLResponse(pathlib.Path(path).read_text(encoding="utf-8"))
        except FileNotFoundError:
            continue
    raise HTTPException(status_code=404, detail="Frontend not found.")


@app.get("/api/health", tags=["System"])
async def health_check():
    return {
        "status":      "healthy",
        "app":         Config.APP_NAME,
        "version":     Config.APP_VERSION,
        "model":       Config.GROQ_MODEL,
        "groq_ready":  groq_service is not None,
        "apis_ready":  medical_service is not None,
        "timestamp":   time.time(),
    }


@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    if not groq_service:
        raise HTTPException(status_code=503, detail="AI service unavailable. Ensure GROQ_API_KEY is set.")

    start     = time.time()
    extra_ctx = ""
    wiki_used = ""

    CONDITION_KEYWORDS = [
        "fever", "malaria", "dengue", "typhoid", "chikungunya", "covid",
        "diabetes", "hypertension", "asthma", "tuberculosis", "tb",
        "cold", "flu", "influenza", "pneumonia", "bronchitis",
        "arthritis", "migraine", "anemia", "anaemia", "thyroid",
        "kidney", "liver", "hepatitis", "anxiety", "depression",
        "acidity", "gastritis", "ulcer", "piles", "haemorrhoids",
    ]
    msg_lower = request.message.lower()
    for kw in CONDITION_KEYWORDS:
        if kw in msg_lower:
            if medical_service:
                wiki = await medical_service.get_wikipedia_summary(kw)
                if wiki.get("found"):
                    extra_ctx = f"Wikipedia on {kw.title()}: {wiki['summary']}"
                    wiki_used = wiki.get("title", kw)
            break

    try:
        reply, tokens = await groq_service.chat(
            user_message  = request.message,
            history       = request.history,
            extra_context = extra_ctx,
        )
    except Exception as exc:
        logger.error("[Chat] Groq error: %s", exc)
        raise HTTPException(status_code=502, detail=f"AI inference error: {exc}")

    elapsed  = int((time.time() - start) * 1000)
    severity = groq_service.extract_severity(reply)
    logger.info("[Chat] %dms | %d tokens | wiki=%s | severity=%s", elapsed, tokens, bool(wiki_used), severity)

    return ChatResponse(
        reply        = reply,
        model        = Config.GROQ_MODEL,
        tokens_used  = tokens,
        response_ms  = elapsed,
        wiki_context = wiki_used or None,
        severity     = severity,
    )


@app.post("/api/upload", tags=["Image"])
async def upload_image(file: UploadFile = File(...)):
    """Image upload placeholder — returns basic AI analysis prompt."""
    if not groq_service:
        raise HTTPException(status_code=503, detail="AI service unavailable.")

    allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 5MB).")

    return {
        "message":  "Image received. Visual analysis coming in a future update.",
        "filename": file.filename,
        "size_kb":  round(len(content) / 1024, 1),
        "status":   "queued",
        "note":     "Currently ArogyaAI processes text symptoms. Describe what you see in the image as text for best results.",
    }


@app.post("/api/drug/search", tags=["Medical Data"])
async def search_drug(request: DrugSearchRequest):
    if not medical_service:
        raise HTTPException(status_code=503, detail="Medical service unavailable.")
    drug_info = await medical_service.search_drug_fda(request.drug_name)
    ae_data   = await medical_service.get_adverse_events(request.drug_name)
    return {
        "drug_info":      drug_info,
        "adverse_events": ae_data,
        "disclaimer":     "Data from FDA. Always consult a licensed pharmacist before taking any medicine.",
    }


@app.post("/api/medical/info", tags=["Medical Data"])
async def medical_info(request: MedicalInfoRequest):
    if not medical_service:
        raise HTTPException(status_code=503, detail="Medical service unavailable.")
    result = await medical_service.get_wikipedia_summary(request.query)
    return {
        "result":     result,
        "disclaimer": "Educational information only. Not a substitute for professional medical advice.",
    }


@app.get("/api/config", tags=["System"])
async def get_config():
    return {
        "app_name":    Config.APP_NAME,
        "app_version": Config.APP_VERSION,
        "features": {
            "voice_input":   True,
            "drug_lookup":   True,
            "medical_info":  True,
            "dark_mode":     True,
            "multilingual":  True,
            "chat_history":  True,
            "export_chat":   True,
            "share_card":    True,
            "image_upload":  True,
        },
        "supported_languages": ["English", "हिंदी", "ગુજરાતી"],
        "emergency_numbers": {
            "ambulance":      "108",
            "aiims_helpline": "1800-11-7091",
            "women_helpline": "1091",
        },
    }


# ══════════════════════════════════════════════
# § 11  ENTRY POINT
# ══════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=Config.PORT, reload=True, log_level="info")