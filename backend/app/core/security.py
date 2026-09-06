"""Security primitives: password hashing, token signing, token hashing."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.enums import UserRole
from app.core.exceptions import (
    ExpiredTokenError,
    InvalidTokenError,
)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- Password hashing ---


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with the configured cost."""
    settings = get_settings()
    return _pwd_context.hash(password, rounds=settings.password_hash_rounds)


def verify_password(password: str, password_hash: str) -> bool:
    """Constant-time password verification."""
    try:
        return _pwd_context.verify(password, password_hash)
    except (ValueError, TypeError):
        return False


# --- Token hashing (for storing refresh tokens) ---


def hash_token(token: str) -> str:
    """Return a SHA-256 hex digest of the token. Used for storing refresh tokens."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_refresh_token() -> tuple[str, str]:
    """Generate a refresh token. Returns (raw, sha256(raw))."""
    raw = secrets.token_urlsafe(48)
    return raw, hash_token(raw)


# --- Access token (JWT) ---


@dataclass(frozen=True)
class TokenPayload:
    sub: str  # user UUID
    role: UserRole
    branch_id: str
    jti: str
    iat: int
    exp: int
    auth_version: int = 0

    def to_claims(self) -> dict[str, Any]:
        return {
            "sub": self.sub,
            "role": UserRole(self.role).value,
            "branch_id": self.branch_id,
            "jti": self.jti,
            "iat": self.iat,
            "exp": self.exp,
            "auth_version": self.auth_version,
            "iss": get_settings().jwt_issuer,
            "aud": get_settings().jwt_audience,
        }


def create_access_token(
    *,
    user_id: uuid.UUID,
    role: UserRole,
    branch_id: uuid.UUID,
    auth_version: int = 0,
) -> tuple[str, TokenPayload]:
    """Create a short-lived JWT access token."""
    settings = get_settings()
    now = datetime.now(tz=timezone.utc)
    exp = now + timedelta(minutes=settings.access_token_expire_minutes)
    jti = str(uuid.uuid4())
    payload = TokenPayload(
        sub=str(user_id),
        role=role,
        branch_id=str(branch_id),
        jti=jti,
        iat=int(now.timestamp()),
        exp=int(exp.timestamp()),
        auth_version=auth_version,
    )
    token = jwt.encode(
        payload.to_claims(),
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return token, payload


def decode_access_token(token: str) -> TokenPayload:
    """Decode and validate a JWT access token. Raises on failure."""
    settings = get_settings()
    try:
        raw = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except jwt.ExpiredSignatureError as exc:
        raise ExpiredTokenError("Access token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidTokenError("Invalid access token") from exc

    try:
        uuid.UUID(raw["sub"])
        uuid.UUID(raw["branch_id"])
        return TokenPayload(
            sub=raw["sub"],
            role=UserRole(raw["role"]),
            branch_id=raw["branch_id"],
            jti=raw["jti"],
            iat=int(raw["iat"]),
            exp=int(raw["exp"]),
            auth_version=int(raw.get("auth_version", 0)),
        )
    except (KeyError, ValueError, TypeError, AttributeError) as exc:
        raise InvalidTokenError("Malformed access token claims") from exc
