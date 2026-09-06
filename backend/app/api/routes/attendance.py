"""Attendance routes."""

from __future__ import annotations

from app.api.transactional import TransactionalRoute

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.db.session import get_db
from app.dependencies.auth import CurrentUserDep
from app.schemas.attendance import (
    ClockInRequest,
    ClockOutRequest,
    ShiftList,
    ShiftOut,
)
from app.services import attendance as attendance_service

router = APIRouter(route_class=TransactionalRoute, prefix="/attendance", tags=["attendance"])


@router.get("/me", response_model=ShiftList)
def my_shifts(current_user: CurrentUserDep, db: Session = Depends(get_db)):
    rows = attendance_service.list_shifts(db, user_id=current_user.id)
    return ShiftList(items=[ShiftOut.model_validate(r) for r in rows], total=len(rows))


@router.get("", response_model=ShiftList)
def list_shifts(
    current_user: CurrentUserDep,
    user_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.PROMOTER.value:
        raise HTTPException(403, "Promoters cannot view others' attendance")
    rows = attendance_service.list_shifts(
        db, actor=current_user, user_id=user_id
    )
    return ShiftList(items=[ShiftOut.model_validate(r) for r in rows], total=len(rows))


@router.get("/current", response_model=ShiftOut | None)
def current_shift(current_user: CurrentUserDep, db: Session = Depends(get_db)):
    shift = attendance_service.current_shift(db, current_user.id)
    return ShiftOut.model_validate(shift) if shift else None


@router.post("/clock-in", response_model=ShiftOut)
def clock_in(payload: ClockInRequest, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    return ShiftOut.model_validate(attendance_service.clock_in(db, current_user, payload))


@router.post("/clock-out", response_model=ShiftOut)
def clock_out(payload: ClockOutRequest, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    return ShiftOut.model_validate(attendance_service.clock_out(db, current_user, payload))

