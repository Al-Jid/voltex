"""Notification services."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import NotificationType
from app.core.exceptions import NotFoundError
from app.models.identity import User
from app.models.notifications import Notification


def notify(
    db: Session,
    *,
    user_id: uuid.UUID,
    type: NotificationType,
    title: str,
    body: str,
    payload: dict | None = None,
) -> Notification:
    """Internal: create a notification for a user."""
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        payload=payload,
    )
    db.add(notification)
    return notification


def list_notifications(
    db: Session, user_id: uuid.UUID, *, offset: int = 0, limit: int = 50
) -> list[Notification]:
    return list(
        db.scalars(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    )


def unread_count(db: Session, user_id: uuid.UUID) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        )
        or 0
    )


def mark_read(db: Session, user_id: uuid.UUID, notification_id: uuid.UUID) -> Notification:
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != user_id:
        raise NotFoundError("Notification not found")
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(tz=timezone.utc)
        db.flush()
    return notification


def mark_all_read(db: Session, user_id: uuid.UUID) -> int:
    now = datetime.now(tz=timezone.utc)
    rows = list(
        db.scalars(
            select(Notification).where(
                Notification.user_id == user_id, Notification.is_read.is_(False)
            )
        )
    )
    for row in rows:
        row.is_read = True
        row.read_at = now
    db.flush()
    return len(rows)
