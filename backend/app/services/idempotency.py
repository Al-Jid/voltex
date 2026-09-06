"""Idempotency service: dedupe mutating requests via Idempotency-Key.

Usage pattern (in route/service):

    replay = get_idempotent_response(db, user, key, fingerprint)
    if replay is not None:
        return JSONResponse(replay.response_body, replay.response_status)
    ... process ...
    store_idempotent_response(db, user, key, req, status, body)
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import IdempotencyKeyMismatchError, ValidationError
from app.models.identity import IdempotencyKey


def request_fingerprint(method: str, path: str, body: bytes) -> str:
    """Stable fingerprint of (method, path, body) for one idempotent request."""
    raw = f"{method.upper()}|{path}|".encode() + body
    return hashlib.sha256(raw).hexdigest()[:64]


def lookup(db: Session, *, user_id: uuid.UUID, key: str) -> IdempotencyKey | None:
    return db.scalar(
        select(IdempotencyKey).where(
            IdempotencyKey.key == key, IdempotencyKey.user_id == user_id
        )
    )


def get_replay(db: Session, *, user_id: uuid.UUID, key: str, fingerprint: str) -> dict | None:
    """Return (status, body) if this key was already stored with same fingerprint."""
    row = lookup(db, user_id=user_id, key=key)
    if row is None:
        return None
    if row.request_fingerprint != fingerprint:
        raise IdempotencyKeyMismatchError(
            "Idempotency-Key was already used with a different request"
        )
    if row.response_body is None:
        return None  # request is still in-flight or failed; reprocess
    return {"status": row.response_status, "body": row.response_body}


def store(
    db: Session,
    *,
    user_id: uuid.UUID,
    key: str,
    endpoint: str,
    fingerprint: str,
    status: int | None,
    body: dict[str, Any] | None,
) -> IdempotencyKey:
    """Persist the response for an idempotency key (or create the row)."""
    row = lookup(db, user_id=user_id, key=key)
    now = datetime.now(tz=timezone.utc)
    if row is None:
        row = IdempotencyKey(
            key=key,
            user_id=user_id,
            endpoint=endpoint,
            request_fingerprint=fingerprint,
            expires_at=now + timedelta(hours=get_settings().idempotency_ttl_hours),
        )
        db.add(row)
    row.response_status = status
    row.response_body = body
    return row


def require_header(key: str | None) -> str:
    if not key or not key.strip():
        raise ValidationError("Idempotency-Key header is required for this endpoint")
    if len(key) > 128:
        raise ValidationError("Idempotency-Key header is too long")
    return key.strip()