"""Catalog model: products."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Product(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    name_ar: Mapped[str | None] = mapped_column(String(80), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    daily_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    __table_args__ = (
        CheckConstraint(
            "sku ~ '^[A-Z0-9-]{2,30}$'",
            name="sku_format",
        ),
        CheckConstraint(
            "char_length(name) BETWEEN 2 AND 80",
            name="name_length",
        ),
        CheckConstraint("price >= 0", name="price_non_negative"),
        CheckConstraint(
            "daily_target IS NULL OR daily_target >= 0",
            name="daily_target_non_negative",
        ),
        Index("ix_products_is_active", "is_active"),
    )