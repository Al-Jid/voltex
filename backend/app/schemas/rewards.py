"""Schemas for rewards."""

from __future__ import annotations

from uuid import UUID

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class RewardRuleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    code: str = Field(min_length=2, max_length=60)
    metric: str = Field(min_length=2, max_length=40)
    reward_points: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    period: str | None = Field(default=None, max_length=20)


class RewardRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    metric: str | None = Field(default=None, min_length=2, max_length=40)
    reward_points: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    period: str | None = Field(default=None, max_length=20)
    is_active: bool | None = None


class RewardRuleOut(BaseModel):
    id: UUID
    name: str
    code: str
    metric: str
    reward_points: Decimal
    period: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class LessonCompleteRequest(BaseModel):
    lesson_id: UUID


class LessonOut(BaseModel):
    id: UUID
    code: str
    title: str
    description: str | None = None
    order_index: int

    model_config = {"from_attributes": True}


class LessonCompletionOut(BaseModel):
    id: UUID
    lesson_id: UUID
    completed_at: datetime

    model_config = {"from_attributes": True}


class ChallengeEnrollRequest(BaseModel):
    challenge_id: UUID


class ChallengeOut(BaseModel):
    id: UUID
    code: str
    title: str
    description: str | None = None
    starts_on: date
    ends_on: date
    target_units: int
    reward_points: Decimal
    is_active: bool

    model_config = {"from_attributes": True}


class ChallengeEnrollmentOut(BaseModel):
    id: UUID
    challenge_id: UUID
    progress_units: int
    completed_at: datetime | None = None
    enrolled_at: datetime

    model_config = {"from_attributes": True}


class RewardSummary(BaseModel):
    balance: Decimal
    lessons_completed: int
    challenges_enrolled: int
