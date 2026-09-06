"""Schemas for tasks."""

from __future__ import annotations

from uuid import UUID

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.core.enums import TaskStatus


class TaskCreate(BaseModel):
    assignee_id: UUID
    title: str = Field(min_length=4, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    due_date: date


class TaskStatusChange(BaseModel):
    status: TaskStatus  # open | completed


class TaskOut(BaseModel):
    id: UUID
    assigner_id: UUID
    assignee_id: UUID
    branch_id: UUID
    title: str
    description: str | None = None
    due_date: date
    status: TaskStatus
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskList(BaseModel):
    items: list[TaskOut]
    total: int
