"""
app/api/auth.py — Signup, Login, Refresh Token, Me endpoints
UPGRADED: refresh token system, both tokens returned on auth
"""
import logging
from fastapi import APIRouter, HTTPException, Depends

from app.core.database import Database
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    refresh_access_token, require_auth,
)
from app.schemas import SignupRequest, LoginRequest

logger = logging.getLogger("arogyaai.auth")
router = APIRouter(prefix="/api/auth", tags=["Auth"])


def _token_response(user: dict) -> dict:
    """Build the standard auth response with both access + refresh tokens."""
    claims = {
        "sub": user["id"],
        "email": user["email"],
        "name": user.get("name", ""),
        "premium": user.get("is_premium", False),
    }
    return {
        "access_token": create_access_token(claims),
        "refresh_token": create_refresh_token(claims),
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user.get("name", ""),
            "is_premium": user.get("is_premium", False),
            "plan": user.get("plan", "free"),
        },
    }


@router.post("/signup")
async def signup(req: SignupRequest):
    """Create a new ArogyaAI account. Returns both access and refresh tokens."""
    existing = await Database.get_user_by_email(req.email)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already registered. Please log in.",
        )

    hashed = hash_password(req.password)
    user = await Database.create_user(
        email=req.email,
        name=req.name,
        hashed_password=hashed,
    )
    if not user:
        raise HTTPException(status_code=500, detail="Failed to create account. Please try again.")

    logger.info("New user registered: %s", req.email)
    return _token_response(user)


@router.post("/login")
async def login(req: LoginRequest):
    """Log in and get access + refresh tokens."""
    user = await Database.get_user_by_email(req.email)
    # Consistent error to prevent email enumeration timing attacks
    if not user or not verify_password(req.password, user.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    # Update streak on login
    try:
        await Database.update_streak(user["id"])
    except Exception:
        pass  # Never block login for streak errors

    logger.info("User logged in: %s", req.email)
    return _token_response(user)


@router.post("/refresh")
async def refresh(body: dict):
    """
    Exchange a valid refresh token for a new access token.
    Client stores refresh_token in localStorage and calls this silently on 401.
    """
    refresh_tok = (body or {}).get("refresh_token", "")
    if not refresh_tok:
        raise HTTPException(status_code=400, detail="refresh_token is required.")

    new_access = refresh_access_token(refresh_tok)
    if not new_access:
        raise HTTPException(
            status_code=401,
            detail="Refresh token is invalid or expired. Please log in again.",
        )
    return {"access_token": new_access, "token_type": "bearer"}


@router.get("/me")
async def get_me(current_user: dict = Depends(require_auth)):
    """Get current authenticated user profile."""
    user = await Database.get_user_by_id(current_user["user_id"])
    if not user:
        return current_user
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user.get("name", ""),
        "is_premium": user.get("is_premium", False),
        "plan": user.get("plan", "free"),
        "created_at": user.get("created_at"),
    }
