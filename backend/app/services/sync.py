"""Sync services: snapshot cursors for offline-first clients."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.catalog import Product
from app.models.identity import User
from app.models.inventory import BranchStock, InventoryMovement
from app.models.notifications import Notification
from app.models.rewards import Lesson, RewardRule
from app.models.sales import Sale
from app.models.tasks import Task


def _latest(db: Session, *tables: type, actor: User | None = None) -> datetime | None:
    """Return the max(updated_at or created_at) across the given tables."""
    greatest: datetime | None = None
    for table in tables:
        column = getattr(table, "updated_at", None)
        if column is None:
            column = getattr(table, "created_at", None)
        if column is None:
            continue
        statement = select(func.max(column))
        if actor is not None:
            from app.dependencies.scope import owner_ids, branch_ids
            if table is Sale:
                statement = statement.where(Sale.promoter_id.in_(owner_ids(actor)))
            elif table is Task:
                statement = statement.where(Task.assignee_id.in_(owner_ids(actor)))
            elif table is Notification:
                statement = statement.where(Notification.user_id == actor.id)
            elif table in (BranchStock, InventoryMovement):
                statement = statement.where(table.branch_id.in_(branch_ids(actor)))
        value = db.scalar(statement)
        if value is not None and (greatest is None or value > greatest):
            greatest = value
    return greatest


def snapshot(db: Session, user: User) -> dict:
    """Return `updated_at` cursors for the caller's scoped slice.

    The snapshot returns only cursor values; the client then pulls each
    changed collection with `since=...` from the list endpoints.
    """
    return {
        "incremental_sync_supported": False,
        "scope": user.role,
        "branch_id": str(user.branch_id) if user.branch_id else None,
        "servers": {
            "products": _latest(db, Product, actor=user),
            "branch_stock": _latest(db, BranchStock, actor=user),
            "sales": _latest(db, Sale, actor=user),
            "stock_movements": _latest(db, InventoryMovement, actor=user),
            "notifications": _latest(db, Notification, actor=user),
            "lessons": _latest(db, Lesson, actor=user),
            "reward_rules": _latest(db, RewardRule, actor=user),
            "tasks": _latest(db, Task, actor=user),
        },
    }

