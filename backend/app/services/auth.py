"""Authentication services: login, refresh, logout, password change."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import UserRole
from app.core.exceptions import (
    AuthenticationError,
    ExpiredTokenError,
    InvalidCredentialsError,
    NotFoundError,
    RefreshExpiredError,
    RefreshInvalidError,
    UserInactiveError,
)
from app.core.security import (
    TokenPayload,
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.identity import RefreshToken, User
from app.schemas.auth import LoginRequest

CHECK_LAST_ADMIN_QUERY: str = (
    "SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = TRUE"
)


def _build_token_pair(db: Session, user: User) -> dict:
    """Issue a fresh access + refresh token pair for `user`."""
    settings = get_settings()
    access_token, _ = create_access_token(
        user_id=user.id, role=user.role, branch_id=user.branch_id, auth_version=user.auth_version
    )
    raw, token_hash = generate_refresh_token()
    now = datetime.now(tz=timezone.utc)
    resource = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        issued_at=now,
        expires_at=now + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(resource)
    return {
        "access_token": access_token,
        "refresh_token": raw,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


def login(db: Session, credentials: LoginRequest) -> dict:
    """Validate credentials, record last_login_at, return token pair."""
    user = db.scalar(select(User).where(User.email == credentials.email))
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise InvalidCredentialsError("Invalid email or password")
    if not user.is_active:
        raise UserInactiveError("Account is deactivated")

    user.last_login_at = datetime.now(tz=timezone.utc)
    tokens = _build_token_pair(db, user)
    db.flush()
    return tokens


def refresh(db: Session, refresh_token: str) -> dict:
    """Rotate a refresh token: revoke the presented token, issue a new pair."""
    settings = get_settings()
    token_hash = hash_token(refresh_token)
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash).with_for_update())

    if stored is None:
        raise RefreshInvalidError("Unknown refresh token")

    now = datetime.now(tz=timezone.utc)
    if stored.expires_at < now:
        raise RefreshExpiredError("Refresh token expired")
    if stored.revoked_at is not None:
        raise RefreshInvalidError("Refresh token already revoked")

    user = db.get(User, stored.user_id)
    if user is None or not user.is_active:
        raise UserInactiveError("Account is not active")

    # Rotate: revoke the old token, create a replacement.
    stored.revoked_at = now
    raw, new_token_hash = generate_refresh_token()
    new_resource = RefreshToken(
        user_id=user.id,
        token_hash=new_token_hash,
        issued_at=now,
        expires_at=now + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(new_resource)
    db.flush()
    stored.replaced_by_id = new_resource.id

    access_token, _ = create_access_token(
        user_id=user.id, role=user.role, branch_id=user.branch_id, auth_version=user.auth_version
    )
    db.flush()
    return {
        "access_token": access_token,
        "refresh_token": raw,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


def logout(db: Session, refresh_token: str) -> None:
    """Revoke a refresh token (idempotent)."""
    token_hash = hash_token(refresh_token)
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if stored is not None and stored.revoked_at is None:
        stored.revoked_at = datetime.now(tz=timezone.utc)
        db.flush()


def change_password(
    db: Session, user: User, current_password: str, new_password: str
) -> None:
    """Validate current password and set the new hash."""
    if not verify_password(current_password, user.password_hash):
        raise InvalidCredentialsError("Current password is incorrect")
    user.password_hash = hash_password(new_password)
    user.auth_version += 1
    user.must_change_password = False
    now = datetime.now(tz=timezone.utc)
    for token in db.scalars(select(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))):
        token.revoked_at = now
    db.flush()


def revoke_all_user_tokens(db: Session, user_id: uuid.UUID) -> None:
    """Revoke every outstanding refresh token for a user (e.g. after compromise)."""
    now = datetime.now(tz=timezone.utc)
    for token in db.scalars(select(RefreshToken).where(RefreshToken.user_id == user_id)):
        if token.revoked_at is None:
            token.revoked_at = now
    db.flush()


