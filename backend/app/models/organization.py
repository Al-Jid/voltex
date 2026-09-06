"""Organization model: branches."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Branch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "branches"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    address: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    __table_args__ = (
        CheckConstraint(
            "char_length(code) BETWEEN 2 AND 32",
            name="code_length",
        ),
        CheckConstraint(
            "char_length(name) BETWEEN 2 AND 80",
            name="name_length",
        ),
        Index("ix_branches_is_active", "is_active"),
    )

    # Forward refs are populated when related models are imported.
    users: Mapped[list["User"]] = relationship(  # type: ignore[name-defined]
        "User",
        back_populates="branch",
        foreign_keys="User.branch_id",
    )