"""Integration tests: transactional integrity (atomicity of multi-row writes)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import select

from app.core.exceptions import BusinessRuleViolation
from app.models.inventory import InventoryMovement
from app.models.rewards import PointLedger
from app.models.sales import Sale
from app.schemas.sales import SaleCreate
from app.services import sales as sales_service

pytestmark = pytest.mark.integration


def _count(db, model) -> int:
    return len(db.scalars(select(model)).all())


def test_failed_sale_rolls_back_everything(db, fixtures):
    """Insufficient stock -> no sale, no movement, no points rows remain."""
    actor = fixtures["pro1"]
    product = fixtures["p1"]

    stock_before = _count(db, Sale), _count(db, InventoryMovement), _count(db, PointLedger)
    with pytest.raises(BusinessRuleViolation):
        sales_service.record_sale(
            db, actor, SaleCreate(product_id=str(product.id), quantity=999)
        )
    db.rollback()

    stock_after = _count(db, Sale), _count(db, InventoryMovement), _count(db, PointLedger)
    assert stock_before == stock_after


def test_successful_sale_commits_as_one_atomic_unit(db, fixtures):
    actor = fixtures["pro1"]
    product = fixtures["p1"]
    from app.services import inventory

    stock = inventory.get_product_stock(db, actor.branch_id, product.id)
    stock.quantity = 5
    db.flush()

    sales_service.record_sale(db, actor, SaleCreate(product_id=str(product.id), quantity=2))

    assert _count(db, Sale) == 1
    assert _count(db, InventoryMovement) == 1
    assert _count(db, PointLedger) == 1

    movement = db.scalar(select(InventoryMovement))
    # Ledger continuity invariant: after = before + delta.
    assert movement.quantity_after == movement.quantity_before + movement.quantity_delta


def test_cancel_sale_restores_stock_and_reverses_points(db, fixtures):
    actor = fixtures["pro1"]
    product = fixtures["p1"]
    from app.services import inventory

    stock = inventory.get_product_stock(db, actor.branch_id, product.id)
    stock.quantity = 5
    db.flush()

    sale = sales_service.record_sale(db, actor, SaleCreate(product_id=str(product.id), quantity=2))
    qty_after_sale = db.get(type(stock), stock.id).quantity

    cancelled = sales_service.cancel_sale(db, fixtures["sup1"], sale, "Customer returned")
    assert cancelled.status == "cancelled"
    assert db.get(type(stock), stock.id).quantity == qty_after_sale + 2

    # Points ledger has a positive entry and a negative reversal.
    points = list(
        db.scalars(select(PointLedger).where(PointLedger.reference_type == "sale"))
    )
    deltas = [p.points_delta for p in points]
    assert sum(Decimal(d) for d in deltas) == 0
