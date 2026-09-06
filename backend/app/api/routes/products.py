"""Product routes."""

from __future__ import annotations

from app.api.transactional import TransactionalRoute

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.db.session import get_db
from app.dependencies.auth import CurrentUserDep
from app.schemas.products import ProductCreate, ProductList, ProductOut, ProductUpdate
from app.services import products as products_service

router = APIRouter(route_class=TransactionalRoute, prefix="/products", tags=["products"])


@router.get("", response_model=ProductList)
def list_products(
    current_user: CurrentUserDep,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    rows = products_service.list_products(
        db, active_only=(current_user.role != UserRole.ADMIN.value), search=search
    )
    return ProductList(items=[ProductOut.model_validate(p) for p in rows], total=len(rows))


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: uuid.UUID, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    return ProductOut.model_validate(products_service.get_product(db, product_id))


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admins create products")
    return ProductOut.model_validate(products_service.create_product(db, payload))


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    current_user: CurrentUserDep,
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admins update products")
    product = products_service.get_product(db, product_id)
    return ProductOut.model_validate(products_service.update_product(db, product, payload))


@router.post("/{product_id}/deactivate", response_model=ProductOut)
def deactivate_product(product_id: uuid.UUID, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admins deactivate products")
    product = products_service.get_product(db, product_id)
    return ProductOut.model_validate(products_service.deactivate_product(db, product))
