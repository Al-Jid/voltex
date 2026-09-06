"""Schemas for branches."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class BranchCreate(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=80)
    address: str | None = Field(default=None, max_length=200)


class BranchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    address: str | None = Field(default=None, max_length=200)


class BranchOut(BaseModel):
    id: UUID
    code: str
    name: str
    address: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class BranchList(BaseModel):
    items: list[BranchOut]
    total: int
