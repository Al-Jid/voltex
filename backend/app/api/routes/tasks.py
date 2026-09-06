"""Task routes."""

from __future__ import annotations

from app.api.transactional import TransactionalRoute

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.enums import TaskStatus, UserRole
from app.db.session import get_db
from app.dependencies.auth import CurrentUserDep
from app.dependencies.scope import require_owner
from app.schemas.tasks import TaskCreate, TaskList, TaskOut, TaskStatusChange
from app.services import tasks as tasks_service

router = APIRouter(route_class=TransactionalRoute, prefix="/tasks", tags=["tasks"])


@router.get("", response_model=TaskList)
def list_tasks(
    current_user: CurrentUserDep,
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.PROMOTER.value:
        assignee_id = current_user.id
        branch_id = None
    else:
        assignee_id = None
        branch_id = current_user.branch_id
    rows = tasks_service.list_tasks(
        db,
        actor=current_user,
        assignee_id=assignee_id,
        status=status_filter,
        offset=(page - 1) * page_size,
        limit=page_size,
    )
    from sqlalchemy import select, func
    from app.models.tasks import Task
    from app.dependencies.scope import owner_ids
    count = select(func.count()).select_from(Task).where(Task.assignee_id.in_(owner_ids(current_user)))
    if status_filter is not None:
        count = count.where(Task.status == status_filter)
    return TaskList(items=[TaskOut.model_validate(r) for r in rows], total=db.scalar(count) or 0)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: uuid.UUID, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    task = tasks_service.get_task(db, task_id)
    require_owner(db, current_user, task.assignee_id)
    return task


@router.post("", response_model=TaskOut)
def create_task(payload: TaskCreate, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    if current_user.role == UserRole.PROMOTER.value:
        raise HTTPException(403, "Promoters cannot create tasks")
    return TaskOut.model_validate(tasks_service.create_task(db, current_user, payload))


@router.post("/{task_id}/status", response_model=TaskOut)
def change_status(
    task_id: uuid.UUID,
    payload: TaskStatusChange,
    current_user: CurrentUserDep,
    db: Session = Depends(get_db),
):
    task = tasks_service.get_task(db, task_id)
    return TaskOut.model_validate(tasks_service.change_status(db, current_user, task, payload))


