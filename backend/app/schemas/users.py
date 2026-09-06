"""Schemas for user management."""

from __future__ import annotations

from uuid import UUID

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.core.enums import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=2, max_length=60)
    phone: str | None = Field(default=None, max_length=20)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole
    branch_id: UUID
    supervisor_id: UUID | None = None
    is_active: bool = True
    must_change_password: bool = False


class UserUpdate(BaseModel):
    role: UserRole | None = None
    email: EmailStr | None = None
    display_name: str | None = Field(default=None, min_length=2, max_length=60)
    phone: str | None = Field(default=None, max_length=20)
    branch_id: UUID | None = None
    supervisor_id: UUID | None = None
    clear_supervisor: bool = False


class UserDeactivateRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=300)


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    display_name: str
    phone: str | None = None
    role: UserRole
    branch_id: UUID
    supervisor_id: UUID | None = None
    is_active: bool
    must_change_password: bool
    last_login_at: datetime | None = None

    model_config = {"from_attributes": True}


class UsersList(BaseModel):
    items: list[UserOut]
    total: int
