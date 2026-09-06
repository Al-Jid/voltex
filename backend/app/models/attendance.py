"""Attendance model: attendance shifts."""

from __future__ import annotations

import uuid
from datetime import datetime, time

from sqlalchemy import (
    CheckConstraint,
    UniqueConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Time,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import TaskStatus
from app.db.base import Base, UUIDPrimaryKeyMixin


class AttendanceShift(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "attendance_shifts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    clock_in_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    clock_out_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[TaskStatus] = mapped_column(String(20), nullable=False, default=TaskStatus.OPEN)
    note: Mapped[str | None] = mapped_column(nullable=True)
    scheduled_start: Mapped[time | None] = mapped_column(Time(timezone=True), nullable=True)
    scheduled_end: Mapped[time | None] = mapped_column(Time(timezone=True), nullable=True)

    __table_args__ = (
        # Partial unique index: at most one open shift per user.
        # Implemented as a partial index in the migration.
        Index(
            "uq_attendance_open_shift_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("status = 'open'"),
        ),
        UniqueConstraint("user_id", "clock_in_at", name="uq_attendance_user_clockin"),
        CheckConstraint(
            "clock_out_at IS NULL OR clock_out_at > clock_in_at",
            name="clock_out_after_clock_in",
        ),
        Index("ix_attendance_shifts_branch", "branch_id", "clock_in_at"),
    )
