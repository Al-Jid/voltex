"""Pagination helpers for list endpoints."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.schemas.base import Page


def paginate(
    db: Session,
    query: Any,
    page: int,
    page_size: int,
) -> Page[list]:
    """Run `query`, count total rows, and slice into a Page envelope.

    `query` must be a SQLAlchemy `Select` built with `select(...).where(...)`.
    """
    count_stmt = select(func.count()).select_from(query.order_by(None).subquery())
    total = db.scalar(count_stmt) or 0
    rows = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    has_more = page * page_size < total
    return Page(
        items=list(rows),
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )