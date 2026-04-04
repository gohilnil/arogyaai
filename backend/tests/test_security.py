"""
tests/test_security.py — Security headers, input validation, and access control tests
"""


class TestSecurityHeaders:
    """Every API response must include OWASP security headers."""

    def _get_resp(self, client):
        """Use the test client which goes through ALL middleware."""
        resp = client.get("/health")
        return resp

    def test_x_content_type_options(self, client):
        resp = self._get_resp(client)
        # starlette TestClient processes middleware; check case-insensitively
        header = resp.headers.get("x-content-type-options", resp.headers.get("X-Content-Type-Options", ""))
        assert header == "nosniff", f"Expected nosniff, got '{header}'. Headers: {dict(resp.headers)}"

    def test_x_frame_options(self, client):
        resp = self._get_resp(client)
        header = resp.headers.get("x-frame-options", resp.headers.get("X-Frame-Options", ""))
        assert header == "DENY", f"Expected DENY, got '{header}'"

    def test_x_xss_protection(self, client):
        resp = self._get_resp(client)
        header = resp.headers.get("x-xss-protection", resp.headers.get("X-XSS-Protection", ""))
        assert header == "1; mode=block"

    def test_referrer_policy(self, client):
        resp = self._get_resp(client)
        header = resp.headers.get("referrer-policy", resp.headers.get("Referrer-Policy", ""))
        assert header == "strict-origin-when-cross-origin"

    def test_permissions_policy(self, client):
        resp = self._get_resp(client)
        # Accept either case or lowercase
        has_header = (
            "permissions-policy" in resp.headers or
            "Permissions-Policy" in resp.headers
        )
        assert has_header, f"Missing Permissions-Policy. Headers: {list(resp.headers.keys())}"

    def test_server_header_removed(self, client):
        """Server fingerprint should be stripped."""
        resp = self._get_resp(client)
        # Server header should not reveal framework details (or should be absent)
        server = resp.headers.get("server", "").lower()
        assert "uvicorn" not in server or server == "", f"Server header leaks: {server}"


class TestAdminProtection:
    def test_admin_stats_no_secret_returns_403(self, client):
        resp = client.get("/api/admin/stats")
        assert resp.status_code == 403

    def test_admin_stats_wrong_secret_returns_403(self, client):
        resp = client.get("/api/admin/stats", headers={"X-Admin-Secret": "wrong-secret"})
        assert resp.status_code == 403

    def test_admin_stats_correct_secret(self, client):
        resp = client.get("/api/admin/stats", headers={"X-Admin-Secret": "test-admin-secret"})
        assert resp.status_code in (200, 503)

    def test_admin_users_no_secret_returns_403(self, client):
        resp = client.get("/api/admin/users")
        assert resp.status_code == 403


class TestInputValidation:
    def test_chat_empty_message_rejected(self, client):
        resp = client.post("/api/chat/", json={"message": ""})
        assert resp.status_code == 422

    def test_chat_message_too_long_rejected(self, client):
        resp = client.post("/api/chat/", json={"message": "x" * 5000})
        assert resp.status_code == 422

    def test_signup_missing_fields_rejected(self, client):
        resp = client.post("/api/auth/signup", json={"email": "test@example.com"})
        assert resp.status_code == 422


class TestAuthProtection:
    def test_health_profile_requires_auth(self, client):
        resp = client.get("/api/user/profile/health")
        assert resp.status_code == 401

    def test_history_requires_auth(self, client):
        resp = client.get("/api/user/history")
        assert resp.status_code == 401

    def test_streak_requires_auth(self, client):
        resp = client.get("/api/user/streak")
        assert resp.status_code == 401

    def test_export_data_requires_auth(self, client):
        resp = client.get("/api/user/export-data")
        assert resp.status_code == 401

    def test_billing_create_order_requires_auth(self, client):
        resp = client.post("/api/billing/create-order", json={"plan": "pro"})
        assert resp.status_code == 401


class TestHealthCheck:
    def test_health_endpoint_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "services" in data
        assert "performance" in data
