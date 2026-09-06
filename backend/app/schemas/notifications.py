"""Schemas for notifications."""

from __future__ import annotations

from uuid import UUID

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.core.enums import NotificationType


class NotificationOut(BaseModel):
    id: UUID
    type: NotificationType
    title: str
    body: str
    is_read: bool
    read_at: datetime | None = None
    payload: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationsList(BaseModel):
    items: list[NotificationOut]
    total: int
