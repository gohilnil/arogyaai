"""
tests/test_auth.py — Authentication endpoint tests
"""
import uuid


def test_signup_success(client):
    """New user can sign up and receives JWT + refresh token."""
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post("/api/auth/signup", json={
        "email": email,
        "name": "Test User",
        "password": "SecurePass123!",
    })
    assert resp.status_code == 200, f"Signup failed: {resp.text}"
    data = resp.json()
    assert "access_token" in data, f"No access_token in: {data}"
    assert "refresh_token" in data, f"No refresh_token in: {data}"
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email
    assert data["user"]["plan"] == "free"
    assert data["user"]["is_premium"] is False


def test_signup_duplicate_email(client):
    """Duplicate email returns 400."""
    email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    payload = {"email": email, "name": "User", "password": "Pass123!"}
    client.post("/api/auth/signup", json=payload)
    resp = client.post("/api/auth/signup", json=payload)
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


def test_signup_invalid_email(client):
    """Invalid email format returns 422."""
    resp = client.post("/api/auth/signup", json={
        "email": "not-an-email",
        "name": "User",
        "password": "Pass123!",
    })
    assert resp.status_code == 422


def test_signup_short_password(client):
    """Password under 6 chars returns 422."""
    resp = client.post("/api/auth/signup", json={
        "email": f"short_{uuid.uuid4().hex[:8]}@example.com",
        "name": "User",
        "password": "abc",
    })
    assert resp.status_code == 422


def test_login_success(client):
    """Login returns access + refresh tokens."""
    email = f"login_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "LoginPass123!"
    client.post("/api/auth/signup", json={"email": email, "name": "User", "password": pwd})

    resp = client.post("/api/auth/login", json={"email": email, "password": pwd})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_wrong_password(client):
    """Wrong password returns 401 with consistent error message."""
    email = f"wrongpw_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/auth/signup", json={"email": email, "name": "User", "password": "RealPass123!"})

    resp = client.post("/api/auth/login", json={"email": email, "password": "WrongPass999!"})
    assert resp.status_code == 401
    assert "invalid" in resp.json()["detail"].lower()


def test_login_nonexistent_email(client):
    """Non-existent email returns 401 (same as wrong password — no email enumeration)."""
    resp = client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "AnyPass123!",
    })
    assert resp.status_code == 401


def test_get_me_authenticated(client, auth_headers):
    """Authenticated user gets their profile."""
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200, f"Expected 200 but got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "email" in data
    assert "id" in data


def test_get_me_unauthenticated(client):
    """No token → 401."""
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_get_me_bad_token(client):
    """Invalid JWT → 401."""
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer bad.token.here"})
    assert resp.status_code == 401


def test_refresh_token(client):
    """Refresh token returns a new access token."""
    email = f"refresh_{uuid.uuid4().hex[:8]}@example.com"
    signup = client.post("/api/auth/signup", json={
        "email": email, "name": "User", "password": "Pass123!",
    })
    refresh_tok = signup.json()["refresh_token"]

    resp = client.post("/api/auth/refresh", json={"refresh_token": refresh_tok})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_refresh_with_invalid_token(client):
    """Invalid refresh token → 401."""
    resp = client.post("/api/auth/refresh", json={"refresh_token": "invalid.token"})
    assert resp.status_code == 401
