"""Schemas for products."""

from __future__ import annotations

from uuid import UUID

from decimal import Decimal

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    sku: str = Field(min_length=2, max_length=30, pattern=r"^[A-Z0-9-]+$")
    name: str = Field(min_length=2, max_length=80)
    name_ar: str | None = Field(default=None, max_length=80)
    description: str | None = None
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    daily_target: int | None = Field(default=None, ge=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    name_ar: str | None = Field(default=None, max_length=80)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    daily_target: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProductOut(BaseModel):
    id: UUID
    sku: str
    name: str
    name_ar: str | None = None
    description: str | None = None
    price: Decimal
    daily_target: int | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class ProductList(BaseModel):
    items: list[ProductOut]
    total: int
