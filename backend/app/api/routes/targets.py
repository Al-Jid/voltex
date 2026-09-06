"""Target routes."""

from __future__ import annotations

from app.api.transactional import TransactionalRoute

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.db.session import get_db
from app.dependencies.auth import CurrentUserDep
from app.dependencies.scope import branch_ids
from sqlalchemy import select
from app.models.targets import BranchTarget
from app.schemas.targets import (
    TargetCreate,
    TargetList,
    TargetOut,
    TargetProgress,
    TargetUpdate,
)
from app.services import targets as targets_service

router = APIRouter(route_class=TransactionalRoute, prefix="/targets", tags=["targets"])


@router.get("", response_model=TargetList)
def list_targets(current_user: CurrentUserDep, db: Session = Depends(get_db)):
    rows = list(db.scalars(select(BranchTarget).where(BranchTarget.branch_id.in_(branch_ids(current_user))).order_by(BranchTarget.period_start.desc())))
    return TargetList(items=[TargetOut.model_validate(r) for r in rows], total=len(rows))


@router.get("/{target_id}/progress", response_model=TargetProgress)
def target_progress(target_id: uuid.UUID, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    target = db.get(BranchTarget, target_id)
    if target is None:
        raise HTTPException(404, "Target not found")
    return targets_service.branch_progress(db, target, current_user)


@router.post("", response_model=TargetOut)
def create_target(payload: TargetCreate, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(403, "Only admins create targets")
    return TargetOut.model_validate(targets_service.create_target(db, payload))


@router.patch("/{target_id}", response_model=TargetOut)
def update_target(
    target_id: uuid.UUID,
    payload: TargetUpdate,
    current_user: CurrentUserDep,
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(403, "Only admins update targets")
    target = db.get(BranchTarget, target_id)
    if target is None:
        raise HTTPException(404, "Target not found")
    return TargetOut.model_validate(targets_service.update_target(db, target, payload))
