"""Audit logging service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import AuditActor
from app.core.logging import get_logger
from app.models.audit import AuditEvent
from app.models.identity import User

logger = get_logger("audit")


def record(
    db: Session,
    *,
    actor: User | None,
    action: str,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
    ip: str | None = None,
) -> AuditEvent:
    """Append an immutable audit event to the ledger."""
    if actor is not None:
        actor_type = AuditActor(actor.role)
        actor_user_id = actor.id
    else:
        actor_type = AuditActor.SYSTEM
        actor_user_id = None

    event = AuditEvent(
        actor_type=actor_type,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        payload=payload,
        ip=ip,
    )
    db.add(event)
    return event


def list_events(
    db: Session,
    *,
    actor_user_id: uuid.UUID | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[AuditEvent]:
    stmt = select(AuditEvent).order_by(AuditEvent.created_at.desc())
    if actor_user_id is not None:
        stmt = stmt.where(AuditEvent.actor_user_id == actor_user_id)
    if action is not None:
        stmt = stmt.where(AuditEvent.action == action)
    if entity_type is not None:
        stmt = stmt.where(AuditEvent.entity_type == entity_type)
    return list(db.scalars(stmt.offset(offset).limit(limit)))
