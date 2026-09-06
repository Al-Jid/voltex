"""Sales repository: aggregation queries for dashboards and targets."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import SaleStatus
from app.models.sales import Sale


def aggregate_by_product(
    db: Session, *, branch_id, day: date | None = None
) -> list[dict]:
    stmt = (
        select(
            Sale.product_id,
            func.sum(Sale.quantity).label("units"),
            func.sum(Sale.total).label("revenue"),
        )
        .where(Sale.branch_id == branch_id, Sale.status == SaleStatus.RECORDED)
        .group_by(Sale.product_id)
    )
    if day is not None:
        stmt = stmt.where(Sale.sold_at == day)
    rows = db.execute(stmt).all()
    return [
        {
            "product_id": str(row.product_id),
            "units": int(row.units or 0),
            "revenue": str(row.revenue or 0),
        }
        for row in rows
    ]


def total_revenue(
    db: Session, *, branch_id, from_date: date, to_date: date
) -> float:
    value = db.scalar(
        select(func.sum(Sale.total)).where(
            Sale.branch_id == branch_id,
            Sale.status == SaleStatus.RECORDED,
            Sale.sold_at >= from_date,
            Sale.sold_at <= to_date,
        )
    )
    return float(value or 0)