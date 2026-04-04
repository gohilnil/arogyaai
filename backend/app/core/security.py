"""
app/core/security.py — JWT authentication, refresh tokens & password hashing
"""
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def _safe_password(password: str) -> str:
    # SHA-256 hash = 64 hex chars, always safe under bcrypt's 72-byte limit
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    return pwd_context.hash(_safe_password(password))


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(_safe_password(plain), hashed)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=settings.JWT_EXPIRE_HOURS)
    )
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    })
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """30-day refresh token — used to silently renew access tokens."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    })
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


def refresh_access_token(refresh_token: str) -> Optional[str]:
    """Validate a refresh token and return a new access token."""
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return None
    # Build new access token with same identity claims
    new_data = {
        "sub": payload.get("sub"),
        "email": payload.get("email", ""),
        "name": payload.get("name", ""),
        "premium": payload.get("premium", False),
    }
    return create_access_token(new_data)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[dict]:
    if not credentials:
        return None
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") == "refresh":
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return {
        "user_id": user_id,
        "email": payload.get("email", ""),
        "is_premium": payload.get("premium", False),
        "name": payload.get("name", ""),
    }


async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    user = await get_current_user(credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user