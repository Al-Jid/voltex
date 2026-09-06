"""Schemas for inventory."""

from __future__ import annotations

from uuid import UUID

from datetime import datetime

from pydantic import BaseModel, Field


class CountCreate(BaseModel):
    product_id: UUID
    observed_quantity: int = Field(ge=0, le=99999)
    note: str | None = Field(default=None, min_length=5, max_length=500)


class CountOut(BaseModel):
    id: UUID
    branch_id: UUID
    product_id: UUID
    observed_quantity: int
    reference_quantity: int
    note: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RestockCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0, le=9999)
    note: str | None = Field(default=None, max_length=500)


class StockAdjustCreate(BaseModel):
    product_id: UUID
    delta: int = Field(ge=-9999, le=9999)
    note: str | None = Field(default=None, max_length=500)


class TransferCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0, le=9999)
    target_branch_id: UUID


class StockRow(BaseModel):
    branch_id: UUID
    product_id: UUID
    sku: str
    product_name: str
    quantity: int
    updated_at: datetime


class StockList(BaseModel):
    items: list[StockRow]
    total: int


class MovementOut(BaseModel):
    id: UUID
    movement_type: str
    quantity_delta: int
    quantity_before: int
    quantity_after: int
    reference_type: str | None = None
    note: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
