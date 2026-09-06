"""Authentication schemas."""

from __future__ import annotations

from uuid import UUID

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.core.enums import UserRole


class LoginRequest(BaseModel):
    email: EmailStr = Field(examples=["hassan@voltex.app"])
    password: str = Field(min_length=8, examples=["password123"])


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


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


class MeResponse(BaseModel):
    user: UserOut


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)


class PasswordChangeResponse(BaseModel):
    ok: bool
