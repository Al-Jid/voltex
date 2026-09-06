"""Branch management services."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BranchNameAlreadyExistsError, NotFoundError, ValidationError
from app.models.identity import User
from app.models.organization import Branch
from app.schemas.branches import BranchCreate, BranchUpdate


def get_branch(db: Session, branch_id: uuid.UUID) -> Branch:
    branch = db.get(Branch, branch_id)
    if branch is None:
        raise NotFoundError("Branch not found")
    return branch


def list_branches(db: Session, *, include_inactive: bool = False) -> list[Branch]:
    stmt = select(Branch).order_by(Branch.name)
    if not include_inactive:
        stmt = stmt.where(Branch.is_active.is_(True))
    return list(db.scalars(stmt))


def create_branch(db: Session, payload: BranchCreate) -> Branch:
    if db.scalar(select(Branch).where(Branch.name == payload.name)) is not None:
        raise BranchNameAlreadyExistsError("A branch with this name already exists")
    if db.scalar(select(Branch).where(Branch.code == payload.code)) is not None:
        raise BranchNameAlreadyExistsError("A branch with this code already exists")

    branch = Branch(
        code=payload.code,
        name=payload.name,
        address=payload.address,
    )
    db.add(branch)
    db.flush()
    db.refresh(branch)
    return branch


def update_branch(db: Session, branch: Branch, payload: BranchUpdate) -> Branch:
    if payload.name is not None and payload.name != branch.name:
        if db.scalar(select(Branch).where(Branch.name == payload.name)) is not None:
            raise BranchNameAlreadyExistsError("A branch with this name already exists")
        branch.name = payload.name
    if payload.address is not None:
        branch.address = payload.address
    db.flush()
    db.refresh(branch)
    return branch


def _has_active_staff(db: Session, branch_id: uuid.UUID) -> bool:
    count = db.scalar(
        select(func.count())
        .select_from(User)
        .where(User.branch_id == branch_id, User.is_active.is_(True))
    )
    return bool(count and count > 0)


def set_branch_active(
    db: Session, branch: Branch, is_active: bool
) -> Branch:
    """Activate/deactivate a branch. Deactivation requires no active staff."""
    if branch.is_active == is_active:
        return branch
    if not is_active and branch.is_active:
        if _has_active_staff(db, branch.id):
            raise ValidationError("Branch has active staff; reassign them first")
    branch.is_active = is_active
    db.flush()
    db.refresh(branch)
    return branch
