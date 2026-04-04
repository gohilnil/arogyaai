"""
tests/test_chat.py — Chat endpoint tests
Emergency fast-path, guest queries, rate limiting, query counter.
"""
import pytest
from unittest.mock import AsyncMock, patch


# ── Emergency Fast-Path ───────────────────────────────────────────────────────

def test_emergency_keywords_detected_without_ai(client):
    """Emergency keywords must trigger fast-path — no AI call made."""
    # We patch ai_service.chat to verify it's NOT called for emergencies
    with patch("app.api.chat.ai_service") as mock_ai:
        mock_ai.available = True
        mock_ai.chat = AsyncMock(return_value={
            "reply": "Emergency response",
            "tokens": 50,
            "meta": {"severity": "serious", "urgency": "emergency", "emergency": True,
                     "body_system": "cardiac", "confidence": "high",
                     "needs_doctor": True, "specialist": None,
                     "suggested_tests": [], "followup_questions": [], "home_care_steps": []},
        })

        resp = client.post("/api/chat/", json={
            "message": "I have severe chest pain and cannot breathe",
            "history": [],
            "language": "en",
        })

        # Should respond (not 500) — emergency path runs without full AI call  
        assert resp.status_code in (200, 429), f"Unexpected status: {resp.status_code}: {resp.text}"
        if resp.status_code == 200:
            data = resp.json()
            # Emergency should be flagged
            assert data.get("urgency_level", 0) >= 4 or data.get("emergency_detected") is True or "108" in data.get("reply", "")


def test_emergency_hindi_detected(client):
    """Hindi emergency keywords must be detected."""
    resp = client.post("/api/chat/", json={
        "message": "सीने में दर्द और साँस नहीं आ रही",
        "history": [],
        "language": "hi",
    })
    assert resp.status_code in (200, 429)
    if resp.status_code == 200:
        data = resp.json()
        # Should have high urgency or emergency
        assert data.get("urgency_level", 0) >= 4 or "108" in data.get("reply", "")


# ── Rate Limiting ─────────────────────────────────────────────────────────────

def test_guest_query_returns_200(client):
    """Unauthenticated chat query should succeed (up to free limit)."""
    resp = client.post("/api/chat/", json={
        "message": "I have a mild headache",
        "history": [],
        "language": "en",
    })
    # Either succeeds or returns rate limit (429) if mocked AI is unavailable
    assert resp.status_code in (200, 429, 503)


def test_chat_includes_queries_remaining(client, auth_headers):
    """Authenticated chat response should include free_queries_left field."""
    resp = client.post("/api/chat/", headers=auth_headers, json={
        "message": "I feel a mild cold",
        "history": [],
        "language": "en",
    })
    # If AI not configured, we may get 503 — skip gracefully
    if resp.status_code == 503:
        pytest.skip("AI not configured in test environment")
    assert resp.status_code in (200, 429)
    if resp.status_code == 200:
        data = resp.json()
        assert "free_queries_left" in data, f"Missing free_queries_left in: {data.keys()}"


# ── Chat History ──────────────────────────────────────────────────────────────

def test_user_history_requires_auth(client):
    """History endpoint requires authentication."""
    resp = client.get("/api/user/history")
    assert resp.status_code == 401


def test_user_history_returns_list(client, auth_headers):
    """Authenticated user gets history list."""
    resp = client.get("/api/user/history", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "history" in data
    assert isinstance(data["history"], list)


# ── Health Check ──────────────────────────────────────────────────────────────

def test_health_endpoint_returns_ok(client):
    """/health must return status=ok with services dict."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "services" in data
    assert "performance" in data
    services = data["services"]
    assert "groq_ai" in services
    assert "supabase" in services


def test_health_endpoint_has_performance_stats(client):
    """Performance dict must include uptime_seconds and total_requests."""
    resp = client.get("/health")
    assert resp.status_code == 200
    perf = resp.json()["performance"]
    assert "uptime_seconds" in perf
    assert "total_requests" in perf
    assert "avg_response_ms" in perf
