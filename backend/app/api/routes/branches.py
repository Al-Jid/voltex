"""Branch routes."""

from __future__ import annotations

from app.api.transactional import TransactionalRoute

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.db.session import get_db
from app.dependencies.auth import CurrentUserDep
from app.dependencies.scope import branch_ids, require_branch
from app.models.organization import Branch
from sqlalchemy import select
from app.schemas.branches import (
    BranchCreate,
    BranchList,
    BranchOut,
    BranchUpdate,
)
from app.services import branches as branches_service

router = APIRouter(route_class=TransactionalRoute, prefix="/branches", tags=["branches"])


class BranchActive(BaseModel):
    is_active: bool


@router.get("", response_model=BranchList)
def list_branches(current_user: CurrentUserDep, db: Session = Depends(get_db)):
    statement = select(Branch).where(Branch.id.in_(branch_ids(current_user)))
    if current_user.role != "admin":
        statement = statement.where(Branch.is_active.is_(True))
    rows = list(db.scalars(statement.order_by(Branch.name)))
    return BranchList(items=[BranchOut.model_validate(b) for b in rows], total=len(rows))


@router.get("/{branch_id}", response_model=BranchOut)
def get_branch(branch_id: uuid.UUID, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    branch = branches_service.get_branch(db, branch_id)
    require_branch(db, current_user, branch.id)
    return branch


@router.post("", response_model=BranchOut, status_code=status.HTTP_201_CREATED)
def create_branch(payload: BranchCreate, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admins create branches")
    return BranchOut.model_validate(branches_service.create_branch(db, payload))


@router.patch("/{branch_id}", response_model=BranchOut)
def update_branch(
    branch_id: uuid.UUID,
    payload: BranchUpdate,
    current_user: CurrentUserDep,
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admins update branches")
    branch = branches_service.get_branch(db, branch_id)
    return BranchOut.model_validate(branches_service.update_branch(db, branch, payload))


@router.post("/{branch_id}/active", response_model=BranchOut)
def set_branch_active(
    branch_id: uuid.UUID,
    payload: BranchActive,
    current_user: CurrentUserDep,
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admins toggle branches")
    branch = branches_service.get_branch(db, branch_id)
    return BranchOut.model_validate(branches_service.set_branch_active(db, branch, payload.is_active))
