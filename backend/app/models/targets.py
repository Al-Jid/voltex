"""Targets model: branch sales targets."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import TargetPeriodType
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BranchTarget(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "branch_targets"

    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    period_type: Mapped[TargetPeriodType] = mapped_column(String(20), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    target_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="EGP", server_default="EGP")

    __table_args__ = (
        CheckConstraint("period_end >= period_start", name="end_after_start"),
        CheckConstraint("target_amount >= 0", name="target_amount_non_negative"),
        CheckConstraint(
            "char_length(currency) BETWEEN 3 AND 8",
            name="currency_length",
        ),
        Index("ix_branch_targets_branch_period", "branch_id", "period_type", "period_start"),
    )