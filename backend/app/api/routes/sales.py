"""Sales routes."""

from __future__ import annotations

from app.api.transactional import TransactionalRoute

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.db.session import get_db
from app.dependencies.auth import CurrentUserDep
from app.dependencies.scope import require_owner
from app.schemas.sales import SaleCancel, SaleCreate, SaleList, SaleOut
from app.services import sales as sales_service

router = APIRouter(route_class=TransactionalRoute, prefix="/sales", tags=["sales"])


@router.get("", response_model=SaleList)
def list_sales(
    current_user: CurrentUserDep,
    promoter_id: uuid.UUID | None = None,
    product_id: uuid.UUID | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    rows, total = sales_service.list_sales(
        db,
        actor=current_user,
        promoter_id=promoter_id,
        product_id=product_id,
        from_date=from_date,
        to_date=to_date,
        offset=(page - 1) * page_size,
        limit=page_size,
    )
    return SaleList(
        items=[SaleOut.model_validate(r) for r in rows],
        total=total,
    )


@router.get("/{sale_id}", response_model=SaleOut)
def get_sale(sale_id: uuid.UUID, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    sale = sales_service.get_sale(db, sale_id)
    require_owner(db, current_user, sale.promoter_id)
    return SaleOut.model_validate(sale)


@router.post("", response_model=SaleOut, status_code=status.HTTP_201_CREATED)
def record_sale(payload: SaleCreate, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    if current_user.role != UserRole.PROMOTER.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only promoters record sales")
    return SaleOut.model_validate(sales_service.record_sale(db, current_user, payload))


@router.post("/{sale_id}/cancel", response_model=SaleOut)
def cancel_sale(sale_id: uuid.UUID, payload: SaleCancel, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    sale = sales_service.get_sale(db, sale_id)
    require_owner(db, current_user, sale.promoter_id)
    return SaleOut.model_validate(sales_service.cancel_sale(db, current_user, sale, payload.reason))

