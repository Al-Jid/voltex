"""Schemas for stock requests."""

from __future__ import annotations

from uuid import UUID

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import RequestStatus, RequestType


class RequestCreate(BaseModel):
    type: RequestType
    product_id: UUID
    quantity: int = Field(ge=1, le=9999)
    reason: str = Field(min_length=5, max_length=1000)


class RequestReview(BaseModel):
    decision: RequestStatus  # approved | changes_requested
    note: str | None = Field(default=None, min_length=5, max_length=500)


class RequestCancel(BaseModel):
    reason: str | None = Field(default=None, max_length=300)


class RequestFulfill(BaseModel):
    note: str | None = Field(default=None, max_length=300)
    source_branch_id: UUID | None = None


class RequestOut(BaseModel):
    id: UUID
    branch_id: UUID
    requested_by: UUID
    type: RequestType
    product_id: UUID
    quantity: int
    reason: str
    status: RequestStatus
    reviewed_by: UUID | None = None
    reviewed_at: datetime | None = None
    review_comment: str | None = None
    fulfilled_by: UUID | None = None
    fulfilled_at: datetime | None = None
    source_branch_id: UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RequestList(BaseModel):
    items: list[RequestOut]
    total: int

