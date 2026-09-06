"""Inventory services: stock snapshot, movements, counts, restock, transfers."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.core.enums import InventoryMovementType
from app.core.exceptions import (
    BusinessRuleViolation,
    CountRequiresNoteError,
    NotFoundError,
    ValidationError,
)
from app.models.catalog import Product
from app.models.identity import User
from app.models.inventory import (
    BranchStock,
    InventoryMovement,
    StockCountObservation,
)
from app.models.organization import Branch
from app.models.sales import Sale
from app.schemas.inventory import (
    CountCreate,
    CountOut,
    RestockCreate,
    StockAdjustCreate,
)


def _get_or_create_stock(db: Session, branch_id: uuid.UUID, product_id: uuid.UUID) -> BranchStock:
    db.execute(insert(BranchStock).values(branch_id=branch_id, product_id=product_id, quantity=0).on_conflict_do_nothing(index_elements=["branch_id", "product_id"]))
    stock = db.scalar(
        select(BranchStock).where(
            BranchStock.branch_id == branch_id,
            BranchStock.product_id == product_id,
        ).with_for_update().execution_options(populate_existing=True)
    )
    if stock is None:
        stock = BranchStock(branch_id=branch_id, product_id=product_id, quantity=0)
        db.add(stock)
        db.flush()
    return stock


def _apply_delta(
    db: Session,
    *,
    branch_id: uuid.UUID,
    product_id: uuid.UUID,
    delta: int,
    movement_type: InventoryMovementType,
    actor_id: uuid.UUID,
    reference_type: str | None = None,
    reference_id: uuid.UUID | None = None,
    note: str | None = None,
) -> BranchStock:
    if delta == 0:
        raise ValidationError("Quantity delta cannot be zero")
    stock = _get_or_create_stock(db, branch_id, product_id)
    before = stock.quantity
    after = before + delta
    if after < 0:
        raise BusinessRuleViolation("Insufficient stock for this operation")
    stock.quantity = after
    db.add(
        InventoryMovement(
            branch_id=branch_id,
            product_id=product_id,
            movement_type=movement_type,
            quantity_delta=delta,
            quantity_before=before,
            quantity_after=after,
            reference_type=reference_type,
            reference_id=reference_id,
            actor_id=actor_id,
            note=note,
        )
    )
    return stock


def get_stock_for_branch(db: Session, branch_id: uuid.UUID) -> list[dict]:
    rows = db.execute(
        select(BranchStock, Product)
        .join(Product, Product.id == BranchStock.product_id)
        .where(BranchStock.branch_id == branch_id)
        .order_by(Product.sku)
    ).all()
    return [
        {
            "branch_id": str(stock.branch_id),
            "product_id": str(stock.product_id),
            "sku": product.sku,
            "product_name": product.name,
            "quantity": stock.quantity,
            "updated_at": stock.updated_at,
        }
        for stock, product in rows
    ]


def get_product_stock(db: Session, branch_id: uuid.UUID, product_id: uuid.UUID) -> BranchStock:
    return _get_or_create_stock(db, branch_id, product_id)


def record_count(db: Session, actor: User, payload: CountCreate) -> StockCountObservation:
    """Record an observed count. Does NOT overwrite reference stock.

    - `note` is required when observed != reference.
    - A `count_observation` inventory movement is logged so the ledger stays complete,
      but reference `branch_stock.quantity` is untouched.
    """
    product = db.get(Product, payload.product_id)
    if product is None or not product.is_active:
        raise NotFoundError("Product not found")

    reference = get_product_stock(db, actor.branch_id, product.id).quantity
    observed = payload.observed_quantity

    if observed != reference and not payload.note:
        raise CountRequiresNoteError(
            "A note is required when the observed quantity differs from reference"
        )

    observation = StockCountObservation(
        branch_id=actor.branch_id,
        product_id=product.id,
        observed_quantity=observed,
        reference_quantity=reference,
        note=payload.note or "Count matches reference",
        observer_id=actor.id,
    )
    db.add(observation)
    db.flush()

    # Append to movement ledger for traceability (does not alter reference).
    delta = observed - reference
    if delta:
        db.add(
            InventoryMovement(
                branch_id=actor.branch_id,
                product_id=product.id,
                movement_type=InventoryMovementType.COUNT_OBSERVATION,
                quantity_delta=0,
                quantity_before=reference,
                quantity_after=reference,  # reference unchanged
                reference_type="stock_count_observation",
                reference_id=observation.id,
                actor_id=actor.id,
                note=payload.note,
            )
        )

    db.flush()
    db.refresh(observation)
    return observation


def restock(db: Session, actor: User, payload: RestockCreate) -> BranchStock:
    """Add stock from a supplier or central warehouse (supervisor/admin)."""
    product = db.get(Product, payload.product_id)
    if product is None or not product.is_active:
        raise NotFoundError("Product not found")
    stock = _apply_delta(
        db,
        branch_id=actor.branch_id,
        product_id=product.id,
        delta=payload.quantity,
        movement_type=InventoryMovementType.RESTOCK,
        actor_id=actor.id,
        note=payload.note,
    )
    db.flush()
    db.refresh(stock)
    return stock


def adjust_stock(
    db: Session, actor: User, payload: StockAdjustCreate
) -> BranchStock:
    """Manual stock adjustment (supervisor/admin). Similar to count but authoritative."""
    product = db.get(Product, payload.product_id)
    if product is None or not product.is_active:
        raise NotFoundError("Product not found")
    stock = _apply_delta(
        db,
        branch_id=actor.branch_id,
        product_id=product.id,
        delta=payload.delta,
        movement_type=InventoryMovementType.ADJUSTMENT,
        actor_id=actor.id,
        note=payload.note,
    )
    db.flush()
    db.refresh(stock)
    return stock


def transfer_to_branch(
    db: Session,
    actor: User,
    *,
    product_id: uuid.UUID,
    quantity: int,
    target_branch_id: uuid.UUID,
) -> None:
    """Move quantity from actor's branch to another branch (supervisor/admin)."""
    if actor.branch_id == target_branch_id:
        raise ValidationError("Target branch must differ from source branch")

    target = db.get(Branch, target_branch_id)
    if target is None or not target.is_active:
        raise NotFoundError("Target branch not found or inactive")

    product = db.get(Product, product_id)
    if product is None or not product.is_active:
        raise NotFoundError("Product not found")

    from app.dependencies.scope import require_branch, require_manager
    require_manager(actor)
    require_branch(db, actor, target_branch_id)
    for branch in sorted((actor.branch_id, target_branch_id), key=str):
        _get_or_create_stock(db, branch, product_id)
    _apply_delta(
        db,
        branch_id=actor.branch_id,
        product_id=product_id,
        delta=-quantity,
        movement_type=InventoryMovementType.TRANSFER_OUT,
        actor_id=actor.id,
        reference_type="branch",
        reference_id=target_branch_id,
    )
    _apply_delta(
        db,
        branch_id=target_branch_id,
        product_id=product_id,
        delta=quantity,
        movement_type=InventoryMovementType.TRANSFER_IN,
        actor_id=actor.id,
        reference_type="branch",
        reference_id=actor.branch_id,
    )
    db.flush()


def list_movements(
    db: Session, branch_id: uuid.UUID, *, limit: int = 100
) -> list[InventoryMovement]:
    stmt = (
        select(InventoryMovement)
        .where(InventoryMovement.branch_id == branch_id)
        .order_by(InventoryMovement.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))


def list_counts(
    db: Session, branch_id: uuid.UUID, *, limit: int = 100
) -> list[StockCountObservation]:
    stmt = (
        select(StockCountObservation)
        .where(StockCountObservation.branch_id == branch_id)
        .order_by(StockCountObservation.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))


def record_sale_decrement(
    db: Session, *, branch_id: uuid.UUID, product_id: uuid.UUID, quantity: int,
    actor_id: uuid.UUID, sale: Sale,
) -> BranchStock:
    """Internal: decrement stock when a sale is recorded. Used by sales service."""
    return _apply_delta(
        db,
        branch_id=branch_id,
        product_id=product_id,
        delta=-quantity,
        movement_type=InventoryMovementType.SALE_DECREMENT,
        actor_id=actor_id,
        reference_type="sale",
        reference_id=sale.id,
        note="Sale recorded",
    )


def list_count_history(db: Session, branch_id: uuid.UUID) -> list[StockCountObservation]:
    return list_counts(db, branch_id, limit=200)

