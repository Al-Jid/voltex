"""Schemas for photos."""

from __future__ import annotations

from uuid import UUID

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import PhotoSource


class PhotoUploadOut(BaseModel):
    id: UUID
    branch_id: UUID
    uploaded_by: UUID
    object_key: str
    content_type: str
    size_bytes: int | None = None
    source: PhotoSource
    created_at: datetime

    model_config = {"from_attributes": True}


class PhotoOut(PhotoUploadOut):
    url: str


class NoteCreate(BaseModel):
    photo_id: UUID
    body: str = Field(min_length=5, max_length=2000)


class NoteOut(BaseModel):
    id: UUID
    shelf_photo_id: UUID
    author_id: UUID
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}

