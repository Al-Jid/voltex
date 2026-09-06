"""Target services."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import TargetPeriodType
from app.core.exceptions import NotFoundError, ValidationError
from app.models.identity import User
from app.models.organization import Branch
from app.models.targets import BranchTarget
from app.schemas.targets import TargetCreate, TargetUpdate
from app.dependencies.scope import require_branch


def create_target(db: Session, payload: TargetCreate) -> BranchTarget:
    if payload.period_end < payload.period_start:
        raise ValidationError("Period end cannot be before period start")
    branch = db.get(Branch, uuid.UUID(str(payload.branch_id)))
    if branch is None:
        raise NotFoundError("Branch not found")

    target = BranchTarget(
        branch_id=payload.branch_id,
        period_type=payload.period_type,
        period_start=payload.period_start,
        period_end=payload.period_end,
        target_amount=payload.target_amount,
        currency=payload.currency,
    )
    db.add(target)
    db.flush()
    db.refresh(target)
    return target


def list_targets(
    db: Session,
    *,
    branch_id: uuid.UUID | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[BranchTarget]:
    stmt = select(BranchTarget).order_by(BranchTarget.period_start.desc())
    if branch_id is not None:
        stmt = stmt.where(BranchTarget.branch_id == branch_id)
    if from_date is not None:
        stmt = stmt.where(BranchTarget.period_start >= from_date)
    if to_date is not None:
        stmt = stmt.where(BranchTarget.period_end <= to_date)
    return list(db.scalars(stmt))


def update_target(db: Session, target: BranchTarget, payload: TargetUpdate) -> BranchTarget:
    for field in ("target_amount", "currency"):
        value = getattr(payload, field)
        if value is not None:
            setattr(target, field, value)
    if payload.period_type is not None:
        target.period_type = payload.period_type
    if payload.period_start is not None:
        target.period_start = payload.period_start
    if payload.period_end is not None:
        target.period_end = payload.period_end
    if target.period_end < target.period_start:
        raise ValidationError("Period end cannot be before period start")
    db.flush()
    db.refresh(target)
    return target


def branch_progress(
    db: Session, target: BranchTarget, actor: User
) -> dict:
    """Compute recorded sales within the target window for the branch."""
    require_branch(db, actor, target.branch_id)
    from app.core.enums import SaleStatus
    from sqlalchemy import func
    from app.models.sales import Sale

    revenue = db.scalar(
        select(func.sum(Sale.total)).where(
            Sale.branch_id == target.branch_id,
            Sale.status == SaleStatus.RECORDED,
            Sale.sold_at >= target.period_start,
            Sale.sold_at <= target.period_end,
        )
    )
    imported = float(revenue or 0)
    return {
        "target_id": str(target.id),
        "period_type": TargetPeriodType(target.period_type).value,
        "period_start": target.period_start.isoformat(),
        "period_end": target.period_end.isoformat(),
        "target_amount": target.target_amount,
        "achieved_amount": imported,
        "percentage": round(imported / target.target_amount * 100, 2)
        if target.target_amount > 0
        else 0.0,
    }

