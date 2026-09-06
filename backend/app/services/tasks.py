"""Task services."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.dependencies.scope import owner_ids

from app.core.enums import TaskStatus
from app.core.exceptions import (
    AssigneeNotInTeamError,
    NotFoundError,
    ValidationError,
)
from app.models.identity import User
from app.models.tasks import Task
from app.schemas.tasks import TaskCreate, TaskStatusChange
from app.dependencies.scope import require_manager, require_owner


def create_task(db: Session, assigner: User, payload: TaskCreate) -> Task:
    require_manager(assigner)
    if len(payload.title.strip()) < 4:
        raise ValidationError("Title must be at least 4 characters")
    if payload.due_date < date.today():
        raise ValidationError("Due date cannot be in the past")

    assignee = db.get(User, uuid.UUID(str(payload.assignee_id)))
    if assignee is None or not assignee.is_active:
        raise NotFoundError("Assignee not found or inactive")

    # Assignee must be in the assigner's branch team (or admin assigns anywhere).
    require_owner(db, assigner, assignee.id)
    if assignee.role != "promoter":
        raise ValidationError("Tasks can only be assigned to promoters")

    task = Task(
        assigner_id=assigner.id,
        assignee_id=assignee.id,
        branch_id=assignee.branch_id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        status=TaskStatus.OPEN,
    )
    db.add(task)
    db.flush()
    db.refresh(task)
    from app.services.notifications import notify
    from app.core.enums import NotificationType
    notify(db, user_id=assignee.id, type=NotificationType.SYSTEM, title="New task", body=task.title, payload={"task_id": str(task.id)})
    return task


def get_task(db: Session, task_id: uuid.UUID) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise NotFoundError("Task not found")
    return task


def list_tasks(
    db: Session,
    *,
    branch_id: uuid.UUID | None = None,
    actor: User | None = None,
    assignee_id: uuid.UUID | None = None,
    status: TaskStatus | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[Task]:
    stmt = select(Task).order_by(Task.due_date)
    if actor is not None:
        stmt = stmt.where(Task.assignee_id.in_(owner_ids(actor)))
    if branch_id is not None:
        stmt = stmt.where(Task.branch_id == branch_id)
    if assignee_id is not None:
        stmt = stmt.where(Task.assignee_id == assignee_id)
    if status is not None:
        stmt = stmt.where(Task.status == status)
    return list(db.scalars(stmt.offset(offset).limit(limit)))


def change_status(
    db: Session, user: User, task: Task, payload: TaskStatusChange
) -> Task:
    """Complete/reopen a task. The assignee completes; the assigner reopens."""
    require_owner(db, user, task.assignee_id)
    if payload.status == TaskStatus.COMPLETED:
        if task.assignee_id != user.id:
            raise ValidationError("Only the assignee can complete the task")
        if task.status != TaskStatus.OPEN:
            raise ValidationError("Task is not open")
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(tz=timezone.utc)
    elif payload.status == TaskStatus.OPEN:
        if task.assigner_id != user.id:
            raise ValidationError("Only the assigner can reopen the task")
        task.status = TaskStatus.OPEN
        task.completed_at = None
    else:
        raise ValidationError("Unsupported status")

    db.flush()
    db.refresh(task)
    return task


