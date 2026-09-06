"""Inventory routes: stock, counts, restock, adjustments, transfers."""

from __future__ import annotations

from app.api.transactional import TransactionalRoute

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.db.session import get_db
from app.dependencies.auth import CurrentUserDep
from app.dependencies.scope import require_branch
from app.schemas.inventory import (
    CountCreate,
    CountOut,
    MovementOut,
    RestockCreate,
    StockAdjustCreate,
    StockList,
    TransferCreate,
)
from app.services import inventory as inventory_service

router = APIRouter(route_class=TransactionalRoute, prefix="/inventory", tags=["inventory"])


@router.get("/stock", response_model=StockList)
def get_stock(current_user: CurrentUserDep, branch_id: uuid.UUID | None = None, db: Session = Depends(get_db)):
    selected = branch_id or current_user.branch_id
    require_branch(db, current_user, selected)
    rows = inventory_service.get_stock_for_branch(db, selected)
    return StockList(items=rows, total=len(rows))


@router.get("/movements", response_model=list[MovementOut])
def list_movements(
    current_user: CurrentUserDep,
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return inventory_service.list_movements(db, current_user.branch_id, limit=limit)


@router.get("/counts", response_model=list[CountOut])
def list_counts(
    current_user: CurrentUserDep,
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return inventory_service.list_count_history(db, current_user.branch_id)[:limit]


@router.post("/counts", response_model=CountOut, status_code=status.HTTP_201_CREATED)
def record_count(payload: CountCreate, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    return CountOut.model_validate(inventory_service.record_count(db, current_user, payload))


@router.post("/restock", response_model=dict)
def restock(payload: RestockCreate, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    if current_user.role == UserRole.PROMOTER.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Promoters cannot restock")
    stock = inventory_service.restock(db, current_user, payload)
    return {"product_id": str(stock.product_id), "quantity": stock.quantity}


@router.post("/adjust", response_model=dict)
def adjust_stock(payload: StockAdjustCreate, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    if current_user.role == UserRole.PROMOTER.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Promoters cannot adjust stock")
    stock = inventory_service.adjust_stock(db, current_user, payload)
    return {"product_id": str(stock.product_id), "quantity": stock.quantity}


@router.post("/transfer", status_code=status.HTTP_204_NO_CONTENT)
def transfer_to_branch(payload: TransferCreate, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    if current_user.role == UserRole.PROMOTER.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Promoters cannot transfer stock")
    inventory_service.transfer_to_branch(
        db,
        current_user,
        product_id=uuid.UUID(str(payload.product_id)),
        quantity=payload.quantity,
        target_branch_id=uuid.UUID(str(payload.target_branch_id)),
    )

