"""User repository: user-scoped queries reused across services."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.models.identity import User


def find_team_members(
    db: Session, *, branch_id, include_inactive: bool = False
) -> Sequence[User]:
    stmt = select(User).where(User.branch_id == branch_id)
    if not include_inactive:
        stmt = stmt.where(User.is_active.is_(True))
    return db.scalars(stmt).all()


def find_active_promoters_under(db: Session, supervisor_id) -> Sequence[User]:
    return db.scalars(
        select(User).where(
            User.supervisor_id == supervisor_id,
            User.role == UserRole.PROMOTER.value,
            User.is_active.is_(True),
        )
    ).all()