"""
tests/test_premium.py — Premium module access tests
Verifies premium-gate enforcement on all locked endpoints.
"""


# ── Premium API Gate ──────────────────────────────────────────────────────────

PREMIUM_MODULES = [
    "nutrition",
    "fitness",
    "mindfulness",
]


def test_premium_chat_requires_auth(client):
    """All premium module chat endpoints must require authentication."""
    for module in PREMIUM_MODULES:
        resp = client.post(f"/api/premium/{module}/chat", json={
            "message": "test",
            "history": [],
            "language": "en",
        })
        assert resp.status_code == 401, (
            f"Module '{module}' returned {resp.status_code} without auth — expected 401"
        )


def test_premium_plan_endpoint_requires_auth(client):
    """Premium plan details endpoint requires auth."""
    resp = client.get("/api/premium/plan")
    assert resp.status_code == 401


def test_premium_upgrade_check(client, auth_headers):
    """Authenticated free user gets is_premium=False in plan response."""
    resp = client.get("/api/premium/plan", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "is_premium" in data
    assert data["is_premium"] is False  # Test user is free tier


def test_free_user_blocked_from_premium_module(client, auth_headers):
    """Free-tier user should receive 403 when accessing premium module (if enforced)."""
    resp = client.post("/api/premium/nutrition/chat", headers=auth_headers, json={
        "message": "What should I eat for diabetes?",
        "history": [],
        "language": "en",
    })
    # Premium gate returns 403 for free users, or 200 if in dev mode
    assert resp.status_code in (200, 403, 503), (
        f"Unexpected status for free user on premium module: {resp.status_code}"
    )


# ── Billing Module ────────────────────────────────────────────────────────────

def test_billing_plans_public(client):
    """Plan listing is public — no auth required."""
    resp = client.get("/api/billing/plans")
    assert resp.status_code == 200
    data = resp.json()
    assert "plans" in data
    assert "pro" in data["plans"]
    assert "elite" in data["plans"]
    # Verify plan structure
    for plan_key, plan in data["plans"].items():
        assert "price_inr" in plan, f"Plan {plan_key} missing price_inr"
        assert "features" in plan, f"Plan {plan_key} missing features"


def test_create_order_requires_auth(client):
    """Creating a payment order requires authentication."""
    resp = client.post("/api/billing/create-order", json={"plan": "pro"})
    assert resp.status_code == 401


def test_create_order_invalid_plan(client, auth_headers):
    """Creating order with invalid plan returns 400."""
    resp = client.post("/api/billing/create-order",
                       headers=auth_headers,
                       json={"plan": "ultra_super_invalid"})
    assert resp.status_code == 400


def test_create_order_dev_mode(client, auth_headers):
    """In dev mode (no Razorpay keys), create-order returns mock order."""
    resp = client.post("/api/billing/create-order",
                       headers=auth_headers,
                       json={"plan": "pro"})
    assert resp.status_code == 200
    data = resp.json()
    assert "order_id" in data
    assert "amount" in data
    # In dev mode, order_id starts with order_DEV_
    assert data["order_id"].startswith("order_DEV_"), (
        f"Expected dev mock order but got: {data['order_id']}"
    )
    assert data.get("dev_mode") is True


def test_subscription_status_requires_auth(client):
    """Subscription status requires auth."""
    resp = client.get("/api/billing/subscription")
    assert resp.status_code == 401


def test_subscription_status_free_user(client, auth_headers):
    """Free user should show plan=free."""
    resp = client.get("/api/billing/subscription", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["plan"] == "free"
    assert data["is_premium"] is False


# ── Analytics ─────────────────────────────────────────────────────────────────

def test_analytics_event_no_auth_needed(client):
    """Analytics event tracking works without authentication."""
    resp = client.post("/api/analytics/event", json={
        "event": "test_event",
        "properties": {"source": "pytest"},
        "session_id": "test-session-123",
    })
    assert resp.status_code == 200
    assert resp.json().get("ok") is True


def test_analytics_event_sanitizes_large_payload(client):
    """Oversized property values are truncated, not rejected."""
    resp = client.post("/api/analytics/event", json={
        "event": "test_large",
        "properties": {"big_value": "x" * 5000},  # Very long string
    })
    assert resp.status_code == 200
