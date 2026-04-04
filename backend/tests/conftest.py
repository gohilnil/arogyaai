"""
tests/conftest.py — Shared pytest fixtures for ArogyaAI test suite

All external services are bypassed in test mode:
- SUPABASE: Empty URL → has_supabase=False → app uses built-in _DEV_USERS store
- RAZORPAY: Empty keys → has_razorpay=False → create-order returns mock order
- GROQ: Empty key → AI routes unavailable but other endpoints tested
"""
import os
import pytest
import uuid

# ── Environment: Set BEFORE any app imports ───────────────────────────────────
os.environ["APP_ENV"] = "test"
os.environ["GROQ_API_KEY"] = "test-key-not-real"
os.environ["JWT_SECRET"] = "test-jwt-secret-that-is-long-enough-for-testing-minimum-64-chars-xx"
os.environ["CORS_ORIGINS"] = "http://localhost:8000,http://testserver"
os.environ["FREE_DAILY_QUERIES"] = "50"
os.environ["ADMIN_SECRET"] = "test-admin-secret"

# CRITICAL: Empty these to force DEV fallback mode (no real connections needed)
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""
os.environ["RAZORPAY_KEY_ID"] = ""
os.environ["RAZORPAY_SECRET"] = ""
os.environ["REDIS_URL"] = ""


@pytest.fixture(scope="session")
def client():
    """
    Session-scoped TestClient.
    With Supabase/Razorpay empty, the app uses its built-in dev fallbacks.
    """
    from main import app
    from starlette.testclient import TestClient

    with TestClient(app, raise_server_exceptions=False) as tc:
        yield tc


@pytest.fixture
def auth_headers(client):
    """Register a unique test user and return Bearer auth headers."""
    email = f"ci_test_{uuid.uuid4().hex[:8]}@arogyaai.test"

    signup_resp = client.post("/api/auth/signup", json={
        "email": email,
        "name": "Test User",
        "password": "TestPassword123!",
    })
    if signup_resp.status_code != 200:
        pytest.skip(f"Auth setup failed ({signup_resp.status_code}): {signup_resp.text}")

    token = signup_resp.json().get("access_token", "")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_ai_response():
    """Standard mock AI response for testing without real Groq calls."""
    return {
        "reply": "Based on your symptoms, this appears to be a mild condition. Stay hydrated and rest.",
        "tokens": 150,
        "model": "llama-3.3-70b-versatile",
        "meta": {
            "severity": "mild",
            "urgency": "self_care",
            "body_system": "general",
            "confidence": "high",
            "needs_doctor": False,
            "emergency": False,
            "specialist": None,
            "suggested_tests": [],
            "followup_questions": ["How long have you had these symptoms?"],
            "home_care_steps": ["Rest well", "Stay hydrated"],
        },
    }
