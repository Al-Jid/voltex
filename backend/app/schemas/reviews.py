"""Schemas for reviews."""

from __future__ import annotations

from uuid import UUID

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import ReviewDecision


class ReviewCreate(BaseModel):
    target_id: UUID
    decision: ReviewDecision  # approved | changes_requested
    note: str = Field(min_length=5, max_length=1000)


class ReviewOut(BaseModel):
    is_current: bool = True
    id: UUID
    reviewer_id: UUID
    target_type: str
    target_id: UUID
    decision: ReviewDecision
    note: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewList(BaseModel):
    items: list[ReviewOut]
    total: int
