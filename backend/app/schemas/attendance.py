"""Schemas for attendance."""

from __future__ import annotations

from uuid import UUID

from datetime import datetime, time

from pydantic import BaseModel, Field

from app.core.enums import TaskStatus


class ClockInRequest(BaseModel):
    note: str | None = Field(default=None, max_length=300)
    scheduled_start: time | None = None
    scheduled_end: time | None = None


class ClockOutRequest(BaseModel):
    note: str | None = Field(default=None, max_length=300)


class ShiftOut(BaseModel):
    id: UUID
    user_id: UUID
    branch_id: UUID
    clock_in_at: datetime
    clock_out_at: datetime | None = None
    status: TaskStatus
    note: str | None = None

    model_config = {"from_attributes": True}


class ShiftList(BaseModel):
    items: list[ShiftOut]
    total: int
