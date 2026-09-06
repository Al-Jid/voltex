"""Sales services: record, list, cancel, points + inventory integration."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone as dt_timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import SaleStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.models.catalog import Product
from app.models.identity import User
from app.models.inventory import InventoryMovement
from app.models.sales import Sale
from app.schemas.sales import SaleCreate, SaleOut
from app.dependencies.scope import require_manager, require_owner, owner_ids


def _price_of(db: Session, product_id: uuid.UUID) -> Decimal:
    product = db.get(Product, product_id)
    if product is None or not product.is_active:
        raise NotFoundError("Product not found or inactive")
    return product.price


def record_sale(
    db: Session,
    actor: User,
    payload: SaleCreate,
    *,
    promoter_id: uuid.UUID | None = None,
) -> Sale:
    """Record a sale for `actor` (promoter creating for themselves) or `promoter_id`.

    Server-authoritative price/total: `total = unit_price * quantity`.
    Quantity must be 1-999. The sale decrements branch stock.
    """
    if not (1 <= payload.quantity <= 999):
        raise ValidationError("Quantity must be between 1 and 999")

    unit_price = _price_of(db, payload.product_id)
    if unit_price < 0:
        raise ValidationError("Unit price cannot be negative")
    total = unit_price * payload.quantity

    sold_at = payload.sold_at or date.today()
    if sold_at > date.today():
        raise ValidationError("Sold-at date cannot be in the future")

    promoter = db.get(User, promoter_id) if promoter_id else actor
    if promoter is None or not promoter.is_active:
        raise NotFoundError("Promoter not found or inactive")
    if promoter.role != "promoter":
        raise ValidationError("Sales can only be attributed to promoters")

    sale = Sale(
        branch_id=actor.branch_id,
        product_id=payload.product_id,
        promoter_id=promoter.id,
        quantity=payload.quantity,
        unit_price=unit_price,
        total=total,
        sold_at=sold_at,
        status=SaleStatus.RECORDED,
        source=payload.source,
        notes=payload.notes,
        created_by=actor.id,
    )
    db.add(sale)
    db.flush()

    from app.services.inventory import record_sale_decrement
    from app.services.rewards import award_sale_points

    stock = record_sale_decrement(
        db,
        branch_id=actor.branch_id,
        product_id=payload.product_id,
        quantity=payload.quantity,
        actor_id=actor.id,
        sale=sale,
    )

    award_sale_points(db, promoter, sale, quantity=payload.quantity)

    db.flush()
    db.refresh(sale)
    return sale


def cancel_sale(
    db: Session, actor: User, sale: Sale, reason: str
) -> Sale:
    """Cancel an immutable sale: mark status, restore stock, reverse points."""
    require_manager(actor)
    require_owner(db, actor, sale.promoter_id)
    sale = db.scalar(select(Sale).where(Sale.id == sale.id).with_for_update().execution_options(populate_existing=True))
    if sale.status != SaleStatus.RECORDED:
        raise ValidationError("Only recorded sales can be cancelled")

    from app.services.inventory import _apply_delta
    from app.services.rewards import reverse_sale_points

    from app.core.enums import InventoryMovementType

    _apply_delta(
        db,
        branch_id=sale.branch_id,
        product_id=sale.product_id,
        delta=sale.quantity,
        movement_type=InventoryMovementType.ADJUSTMENT,
        actor_id=actor.id,
        reference_type="sale_cancel",
        reference_id=sale.id,
        note="Cancelled sale stock restoration",
    )

    reverse_sale_points(db, sale)

    sale.status = SaleStatus.CANCELLED
    sale.cancelled_at = datetime.now(tz=dt_timezone.utc)
    sale.cancelled_by = actor.id
    sale.cancellation_reason = reason
    db.flush()
    db.refresh(sale)
    return sale


def get_sale(db: Session, sale_id: uuid.UUID) -> Sale:
    sale = db.get(Sale, sale_id)
    if sale is None:
        raise NotFoundError("Sale not found")
    return sale


def list_sales(
    db: Session,
    *,
    branch_id: uuid.UUID | None = None,
    actor: User | None = None,
    promoter_id: uuid.UUID | None = None,
    product_id: uuid.UUID | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[Sale], int]:
    stmt = select(Sale)
    count_stmt = select(func.count()).select_from(Sale)
    if branch_id is not None:
        stmt = stmt.where(Sale.branch_id == branch_id)
        count_stmt = count_stmt.where(Sale.branch_id == branch_id)
    if actor is not None:
        stmt = stmt.where(Sale.promoter_id.in_(owner_ids(actor)))
        count_stmt = count_stmt.where(Sale.promoter_id.in_(owner_ids(actor)))

    if promoter_id is not None:
        stmt = stmt.where(Sale.promoter_id == promoter_id)
        count_stmt = count_stmt.where(Sale.promoter_id == promoter_id)
    if product_id is not None:
        stmt = stmt.where(Sale.product_id == product_id)
        count_stmt = count_stmt.where(Sale.product_id == product_id)
    if from_date is not None:
        stmt = stmt.where(Sale.sold_at >= from_date)
        count_stmt = count_stmt.where(Sale.sold_at >= from_date)
    if to_date is not None:
        stmt = stmt.where(Sale.sold_at <= to_date)
        count_stmt = count_stmt.where(Sale.sold_at <= to_date)

    total = db.scalar(count_stmt) or 0
    rows = list(
        db.scalars(stmt.order_by(Sale.created_at.desc()).offset(offset).limit(limit))
    )
    return rows, total


def daily_summary(db: Session, branch_id: uuid.UUID, day: date) -> list[dict]:
    """Per-product sales summary for a branch+day (used to build daily targets)."""
    rows = db.execute(
        select(
            Sale.product_id,
            func.sum(Sale.quantity).label("units"),
            func.sum(Sale.total).label("revenue"),
        )
        .where(Sale.branch_id == branch_id, Sale.sold_at == day, Sale.status == SaleStatus.RECORDED)
        .group_by(Sale.product_id)
    ).all()
    return [
        {
            "product_id": str(row.product_id),
            "units": int(row.units or 0),
            "revenue": str(row.revenue or Decimal("0")),
        }
        for row in rows
    ]


def sale_to_out(sale: Sale) -> SaleOut:
    return SaleOut(
        id=str(sale.id),
        branch_id=str(sale.branch_id),
        product_id=str(sale.product_id),
        promoter_id=str(sale.promoter_id),
        quantity=sale.quantity,
        unit_price=str(sale.unit_price),
        total=str(sale.total),
        sold_at=sale.sold_at,
        status=SaleStatus(sale.status).value,
        source=sale.source,
        notes=sale.notes,
        created_at=sale.created_at,
    )

