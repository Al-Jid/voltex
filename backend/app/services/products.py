"""Product catalog services."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, SkuAlreadyExistsError, ValidationError
from app.models.catalog import Product
from app.schemas.products import ProductCreate, ProductUpdate


def get_product(db: Session, product_id: uuid.UUID) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise NotFoundError("Product not found")
    return product


def list_products(
    db: Session,
    *,
    active_only: bool = True,
    search: str | None = None,
) -> list[Product]:
    stmt = select(Product).order_by(Product.sku)
    if active_only:
        stmt = stmt.where(Product.is_active.is_(True))
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(Product.name.ilike(pattern) | Product.sku.ilike(pattern))
    return list(db.scalars(stmt))


def create_product(db: Session, payload: ProductCreate) -> Product:
    if db.scalar(select(Product).where(Product.sku == payload.sku)) is not None:
        raise SkuAlreadyExistsError("A product with this SKU already exists")
    product = Product(
        sku=payload.sku,
        name=payload.name,
        name_ar=payload.name_ar,
        description=payload.description,
        price=payload.price,
        daily_target=payload.daily_target,
    )
    db.add(product)
    db.flush()
    db.refresh(product)
    return product


def update_product(db: Session, product: Product, payload: ProductUpdate) -> Product:
    for field in ("name", "name_ar", "description", "price", "daily_target", "is_active"):
        value = getattr(payload, field)
        if value is not None:
            setattr(product, field, value)
    db.flush()
    db.refresh(product)
    return product


def deactivate_product(db: Session, product: Product) -> Product:
    """Soft-remove a product from the live catalog (keeps historical references)."""
    product.is_active = False
    db.flush()
    db.refresh(product)
    return product
