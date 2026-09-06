"""Notification routes."""

from __future__ import annotations

from app.api.transactional import TransactionalRoute

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.session import get_db
from app.dependencies.auth import CurrentUserDep
from app.models.notifications import Notification
from app.schemas.notifications import NotificationOut, NotificationsList
from app.services import notifications as notifications_service

router = APIRouter(route_class=TransactionalRoute, prefix="/notifications", tags=["notifications"])


class UnreadCount(BaseModel):
    count: int


@router.get("", response_model=NotificationsList)
def list_notifications(
    current_user: CurrentUserDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    rows = notifications_service.list_notifications(
        db, current_user.id, offset=(page - 1) * page_size, limit=page_size
    )
    return NotificationsList(
        items=[NotificationOut.model_validate(r) for r in rows], total=db.scalar(select(func.count()).select_from(Notification).where(Notification.user_id == current_user.id)) or 0
    )


@router.get("/unread-count", response_model=UnreadCount)
def unread_count(current_user: CurrentUserDep, db: Session = Depends(get_db)):
    return UnreadCount(count=notifications_service.unread_count(db, current_user.id))


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: uuid.UUID, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    return NotificationOut.model_validate(
        notifications_service.mark_read(db, current_user.id, notification_id)
    )


@router.post("/read-all")
def mark_all_read(current_user: CurrentUserDep, db: Session = Depends(get_db)):
    marked = notifications_service.mark_all_read(db, current_user.id)
    return {"marked": marked}
