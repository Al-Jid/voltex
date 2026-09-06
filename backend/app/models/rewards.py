"""Rewards models: reward rules, points ledger, lessons, challenges.

Points are derived data — there is no mutable `user.points` column.
The authoritative source is `point_ledger`; totals are computed via `SUM()`.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import RewardReferenceType
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RewardRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reward_rules"

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    metric: Mapped[str] = mapped_column(String(40), nullable=False)  # e.g. sale_unit, lesson_complete
    reward_points: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    period: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")

    __table_args__ = (
        CheckConstraint("reward_points >= 0", name="reward_points_non_negative"),
        CheckConstraint("char_length(code) BETWEEN 2 AND 60", name="code_length"),
        Index("ix_reward_rules_metric", "metric"),
    )


class PointLedger(UUIDPrimaryKeyMixin, Base):
    """Append-only ledger of points awarded to a user."""

    __tablename__ = "point_ledger"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    points_delta: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str] = mapped_column(String(120), nullable=False)
    reference_type: Mapped[RewardReferenceType] = mapped_column(
        String(20),
        nullable=False,
    )
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB(), nullable=True)

    __table_args__ = (
        CheckConstraint("points_delta <> 0", name="points_delta_nonzero"),
        Index("ix_point_ledger_user_created", "user_id", "created_at"),
        Index("ix_point_ledger_reference", "reference_type", "reference_id"),
    )


class Lesson(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "lessons"

    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_path: Mapped[str | None] = mapped_column(String(256), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")

    __table_args__ = (
        CheckConstraint("char_length(title) BETWEEN 2 AND 120", name="title_length"),
        Index("ix_lessons_order", "order_index"),
    )


class LessonCompletion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "lesson_completions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="RESTRICT"),
        nullable=False,
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson"),
        Index("ix_lesson_completions_user", "user_id"),
    )


class Challenge(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "challenges"

    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False)
    target_units: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_points: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")

    __table_args__ = (
        CheckConstraint("ends_on >= starts_on", name="end_after_start"),
        CheckConstraint("target_units > 0", name="target_units_positive"),
        CheckConstraint("reward_points >= 0", name="reward_points_non_negative"),
        CheckConstraint("char_length(title) BETWEEN 2 AND 120", name="title_length"),
    )


class ChallengeEnrollment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "challenge_enrollments"

    challenge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("challenges.id", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    progress_units: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    __table_args__ = (
        UniqueConstraint("challenge_id", "user_id", name="uq_challenge_user"),
        CheckConstraint("progress_units >= 0", name="progress_units_non_negative"),
        Index("ix_challenge_enrollments_user", "user_id"),
    )
