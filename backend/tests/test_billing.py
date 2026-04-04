"""
tests/test_billing.py — Billing and subscription tests
Tests adjusted for the new API pattern (throws on error, returns data directly).
"""


class TestBillingPlans:
    def test_get_plans_public(self, client):
        """Plans endpoint is public — no auth required."""
        resp = client.get("/api/billing/plans")
        assert resp.status_code == 200, f"Expected 200: {resp.text}"
        data = resp.json()
        assert "plans" in data, f"Missing 'plans' key: {data}"
        assert "pro" in data["plans"]
        assert "elite" in data["plans"]

    def test_pro_plan_has_price(self, client):
        resp = client.get("/api/billing/plans")
        assert resp.status_code == 200
        pro = resp.json()["plans"]["pro"]
        assert pro["price_inr"] > 0

    def test_elite_more_expensive_than_pro(self, client):
        resp = client.get("/api/billing/plans")
        plans = resp.json()["plans"]
        assert plans["elite"]["price_inr"] > plans["pro"]["price_inr"]

    def test_plans_have_features(self, client):
        resp = client.get("/api/billing/plans")
        for plan_key in ["pro", "elite"]:
            plan = resp.json()["plans"][plan_key]
            assert "features" in plan
            assert len(plan["features"]) > 0


class TestCreateOrder:
    def test_create_order_requires_auth(self, client):
        resp = client.post("/api/billing/create-order", json={"plan": "pro"})
        assert resp.status_code == 401

    def test_create_order_invalid_plan(self, client, auth_headers):
        resp = client.post(
            "/api/billing/create-order",
            json={"plan": "invalid_plan_xyz"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_create_order_pro_dev_mode(self, client, auth_headers):
        """In dev mode (no Razorpay keys), returns a mock order."""
        resp = client.post(
            "/api/billing/create-order",
            json={"plan": "pro"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Unexpected: {resp.text}"
        data = resp.json()
        assert "order_id" in data, f"Missing order_id: {data}"
        assert "amount" in data
        assert data["plan"] == "pro"

    def test_create_order_elite(self, client, auth_headers):
        resp = client.post(
            "/api/billing/create-order",
            json={"plan": "elite"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["plan"] == "elite"


class TestSubscription:
    def test_get_subscription_requires_auth(self, client):
        resp = client.get("/api/billing/subscription")
        assert resp.status_code == 401

    def test_get_subscription_new_user_is_free(self, client, auth_headers):
        resp = client.get("/api/billing/subscription", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200: {resp.text}"
        data = resp.json()
        assert data["plan"] == "free"
        assert data["is_premium"] is False


class TestMemoryServiceCache:
    def test_lru_cache_stores_and_retrieves(self):
        from app.services.memory_service import ResponseCache
        cache = ResponseCache(maxsize=10, ttl_seconds=3600)
        cache.set("What is diabetes?", "Diabetes is a condition...")
        result = cache.get("What is diabetes?")
        assert result == "Diabetes is a condition..."

    def test_lru_cache_ignores_personal_queries(self):
        from app.services.memory_service import ResponseCache
        cache = ResponseCache(maxsize=10, ttl_seconds=3600)
        cache.set("I have diabetes", "Personal response")
        result = cache.get("I have diabetes")
        assert result is None  # Personal queries never cached

    def test_lru_cache_respects_maxsize(self):
        from app.services.memory_service import ResponseCache
        cache = ResponseCache(maxsize=3, ttl_seconds=3600)
        for i in range(5):
            cache.set(f"generic question number {i}", f"answer {i}")
        assert cache.size <= 3

    def test_lru_cache_case_insensitive_key(self):
        from app.services.memory_service import ResponseCache
        cache = ResponseCache(maxsize=10, ttl_seconds=3600)
        cache.set("WHAT IS FEVER?", "Fever is...")
        # Same query different case should hit cache (normalized)
        result = cache.get("what is fever?")
        assert result == "Fever is..."
