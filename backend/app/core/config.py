"""
app/core/config.py — Centralized configuration for ArogyaAI
All settings loaded from environment variables with safe defaults.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ── AI ──────────────────────────────────────
    GROQ_API_KEY: str        = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str          = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_WHISPER_MODEL: str  = "whisper-large-v3"
    MAX_TOKENS: int          = int(os.getenv("MAX_TOKENS", "2000"))
    TEMPERATURE: float       = float(os.getenv("TEMPERATURE", "0.45"))

    # ── Database ────────────────────────────────
    SUPABASE_URL: str        = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str        = os.getenv("SUPABASE_KEY", "")

    # ── Security ────────────────────────────────
    JWT_SECRET: str          = os.getenv("JWT_SECRET", "CHANGE-THIS-IN-PRODUCTION-MIN-64-CHARS-RANDOM-STRING-HERE-NOW")
    JWT_ALGORITHM: str       = "HS256"
    JWT_EXPIRE_HOURS: int    = int(os.getenv("JWT_EXPIRE_HOURS", "168"))   # 7 days
    JWT_REFRESH_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "30"))

    # ── CORS — never wildcard in production ────
    CORS_ORIGINS: list       = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8000,http://localhost:3000,http://127.0.0.1:8000"
    ).split(",")

    # ── App ─────────────────────────────────────
    APP_NAME: str            = "ArogyaAI"
    APP_VERSION: str         = "3.0.0"
    PORT: int                = int(os.getenv("PORT", "8000"))
    APP_ENV: str             = os.getenv("APP_ENV", "development")

    # ── Rate Limiting ───────────────────────────
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
    RATE_LIMIT_WINDOW: int   = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

    # ── Monetization — Pricing Tiers ────────────
    FREE_DAILY_QUERIES: int  = int(os.getenv("FREE_DAILY_QUERIES", "5"))
    PLAN_PRO_PRICE_INR: int  = int(os.getenv("PLAN_PRO_PRICE_INR", "99"))
    PLAN_ELITE_PRICE_INR: int = int(os.getenv("PLAN_ELITE_PRICE_INR", "299"))

    # ── Payment ─────────────────────────────────
    RAZORPAY_KEY_ID: str     = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_SECRET: str     = os.getenv("RAZORPAY_SECRET", "")

    # ── Infrastructure ──────────────────────────
    REDIS_URL: str           = os.getenv("REDIS_URL", "")

    # ── Admin ───────────────────────────────────
    ADMIN_SECRET: str        = os.getenv("ADMIN_SECRET", "")

    # ── External APIs ───────────────────────────
    OPENFDA_BASE: str        = "https://api.fda.gov/drug"
    WIKI_API: str            = "https://en.wikipedia.org/api/rest_v1/page/summary"

    # ── Cache ───────────────────────────────────
    CACHE_TTL_SECONDS: int   = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

    # ── Password security ───────────────────────
    MAX_PASSWORD_BYTES: int  = 72

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def has_supabase(self) -> bool:
        return bool(self.SUPABASE_URL and self.SUPABASE_KEY)

    @property
    def has_groq(self) -> bool:
        return bool(self.GROQ_API_KEY)

    @property
    def has_razorpay(self) -> bool:
        return bool(self.RAZORPAY_KEY_ID and self.RAZORPAY_SECRET)

    @property
    def has_redis(self) -> bool:
        return bool(self.REDIS_URL)

    def validate(self) -> None:
        """Called at startup — enforces production safety requirements."""
        if not self.is_production:
            return
        errors = []
        if "CHANGE-THIS" in self.JWT_SECRET:
            errors.append("JWT_SECRET must be changed in production (min 64 chars).")
        if not self.has_supabase:
            errors.append("SUPABASE_URL and SUPABASE_KEY are required in production.")
        if "*" in str(self.CORS_ORIGINS):
            errors.append("Wildcard CORS (*) is not allowed in production.")
        if not self.ADMIN_SECRET:
            errors.append("ADMIN_SECRET must be set in production.")
        if errors:
            raise RuntimeError("FATAL production config errors:\n" + "\n".join(f"  - {e}" for e in errors))


settings = Settings()
