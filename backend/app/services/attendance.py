"""Attendance services."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.dependencies.scope import owner_ids

from app.core.exceptions import (
    ActiveShiftExistsError,
    NotFoundError,
    ValidationError,
)
from app.core.enums import TaskStatus
from app.models.attendance import AttendanceShift
from app.models.identity import User
from app.schemas.attendance import ClockInRequest, ClockOutRequest


def clock_in(db: Session, user: User, payload: ClockInRequest) -> AttendanceShift:
    open_shift = db.scalar(
        select(AttendanceShift).where(
            AttendanceShift.user_id == user.id,
            AttendanceShift.status == TaskStatus.OPEN,
        )
    )
    if open_shift is not None:
        raise ActiveShiftExistsError("You already have an open shift")

    shift = AttendanceShift(
        user_id=user.id,
        branch_id=user.branch_id,
        status=TaskStatus.OPEN,
        note=payload.note,
        scheduled_start=payload.scheduled_start,
        scheduled_end=payload.scheduled_end,
    )
    db.add(shift)
    db.flush()
    db.refresh(shift)
    return shift


def clock_out(db: Session, user: User, payload: ClockOutRequest) -> AttendanceShift:
    shift = db.scalar(
        select(AttendanceShift).where(
            AttendanceShift.user_id == user.id,
            AttendanceShift.status == TaskStatus.OPEN,
        )
    )
    if shift is None:
        raise NotFoundError("No open shift found")

    now = datetime.now(tz=timezone.utc)
    if shift.clock_in_at >= now:
        raise ValidationError("Clock-out time must be after clock-in")

    shift.clock_out_at = now
    shift.status = TaskStatus.COMPLETED
    if payload.note:
        shift.note = payload.note
    db.flush()
    db.refresh(shift)
    return shift


def list_shifts(
    db: Session,
    *,
    user_id: uuid.UUID | None = None,
    branch_id: uuid.UUID | None = None,
    actor: User | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[AttendanceShift]:
    stmt = select(AttendanceShift).order_by(AttendanceShift.clock_in_at.desc())
    if actor is not None:
        stmt = stmt.where(AttendanceShift.user_id.in_(owner_ids(actor)))
    if user_id is not None:
        stmt = stmt.where(AttendanceShift.user_id == user_id)
    if branch_id is not None:
        stmt = stmt.where(AttendanceShift.branch_id == branch_id)
    return list(db.scalars(stmt.offset(offset).limit(limit)))


def current_shift(db: Session, user_id: uuid.UUID) -> AttendanceShift | None:
    return db.scalar(
        select(AttendanceShift).where(
            AttendanceShift.user_id == user_id,
            AttendanceShift.status == TaskStatus.OPEN,
        )
    )

