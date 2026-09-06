"""Schemas for targets."""

from __future__ import annotations

from uuid import UUID

from datetime import date

from pydantic import BaseModel, Field

from app.core.enums import TargetPeriodType


class TargetCreate(BaseModel):
    branch_id: UUID
    period_type: TargetPeriodType
    period_start: date
    period_end: date
    target_amount: int = Field(ge=0)
    currency: str = Field(default="EGP", min_length=3, max_length=8)


class TargetUpdate(BaseModel):
    period_type: TargetPeriodType | None = None
    period_start: date | None = None
    period_end: date | None = None
    target_amount: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=8)


class TargetOut(BaseModel):
    id: UUID
    branch_id: UUID
    period_type: TargetPeriodType
    period_start: date
    period_end: date
    target_amount: int
    currency: str

    model_config = {"from_attributes": True}


class TargetList(BaseModel):
    items: list[TargetOut]
    total: int


class TargetProgress(BaseModel):
    target_id: UUID
    period_type: str
    period_start: str
    period_end: str
    target_amount: int
    achieved_amount: float
    percentage: float
