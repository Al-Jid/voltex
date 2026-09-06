"""Schemas for sales."""

from __future__ import annotations

from uuid import UUID

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class SaleCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(ge=1, le=999)
    unit_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    sold_at: date | None = None
    source: str | None = Field(default=None, max_length=40)
    notes: str | None = Field(default=None, max_length=1000)


class SaleCancel(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class SaleOut(BaseModel):
    id: UUID
    branch_id: UUID
    product_id: UUID
    promoter_id: UUID
    quantity: int
    unit_price: Decimal
    total: Decimal
    sold_at: date
    status: str
    source: str | None = None
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SaleList(BaseModel):
    items: list[SaleOut]
    total: int
