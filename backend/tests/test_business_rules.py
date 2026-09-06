"""Integration tests: business rules + transactional integrity."""

from __future__ import annotations

from sqlalchemy import select

import pytest

from app.core.enums import RequestStatus
from app.core.exceptions import (
    BusinessRuleViolation,
    CountRequiresNoteError,
    EmailAlreadyExistsError,
    LastAdminProtectionError,
    SelfApprovalForbiddenError,
    SupervisorHasActiveTeamError,
    ValidationError,
)
from app.models.catalog import Product
from app.models.inventory import BranchStock, InventoryMovement
from app.models.rewards import PointLedger
from app.models.requests import StockRequest
from app.models.sales import Sale
from app.schemas.inventory import CountCreate
from app.schemas.requests import RequestCreate, RequestFulfill
from app.schemas.sales import SaleCreate
from app.schemas.users import UserCreate
from app.services import inventory, requests as requests_service
from app.services import sales as sales_service
from app.services import users as users_service

pytestmark = pytest.mark.integration


def test_email_unique_rule(db, fixtures):
    payload = UserCreate(
        email="u1@voltex.app",  # already taken by pro1
        display_name="Duplicate",
        password="password123",
        role="promoter",
        branch_id=str(fixtures["b1"].id),
        supervisor_id=str(fixtures["sup1"].id),
    )
    with pytest.raises(EmailAlreadyExistsError):
        users_service.create_user(db, payload)


def test_last_admin_protection(db, fixtures):
    admin = fixtures["admin"]
    with pytest.raises(LastAdminProtectionError):
        users_service.deactivate_user(db, admin, admin)


def test_promoter_requires_supervisor(db, fixtures):
    payload = UserCreate(
        email="nobody@voltex.app",
        display_name="No Boss",
        password="password123",
        role="promoter",
        branch_id=str(fixtures["b1"].id),
        supervisor_id=None,
    )
    with pytest.raises(ValidationError):
        users_service.create_user(db, payload)


def test_cross_branch_supervisor_rejected(db, fixtures):
    """A promoter in branch 1 cannot be supervised by someone in branch 2."""
    payload = UserCreate(
        email="nobody2@voltex.app",
        display_name="Cross Branch",
        password="password123",
        role="promoter",
        branch_id=str(fixtures["b1"].id),
        supervisor_id=str(fixtures["pro2"].id),  # promoter in a different branch
    )
    with pytest.raises(ValidationError):
        users_service.create_user(db, payload)


def test_sale_decrements_stock_and_awards_points(db, fixtures):
    actor = fixtures["pro1"]
    product = fixtures["p1"]

    stock = inventory.get_product_stock(db, actor.branch_id, product.id)
    stock.quantity = 10
    db.flush()

    sale = sales_service.record_sale(
        db, actor, SaleCreate(product_id=str(product.id), quantity=2)
    )
    assert sale.total == 200  # 2 x price 100

    refreshed = db.get(BranchStock, stock.id)
    assert refreshed.quantity == 8

    movement = db.scalar(
        select(InventoryMovement).where(
            InventoryMovement.reference_type == "sale",
            InventoryMovement.reference_id == sale.id,
        )
    )
    assert movement is not None
    assert movement.quantity_delta == -2
    assert movement.quantity_after == 8

    ledger = db.scalar(
        select(PointLedger).where(
            PointLedger.reference_type == "sale",
            PointLedger.reference_id == sale.id,
        )
    )
    assert ledger is not None
    assert ledger.points_delta == 20  # 2 units x 10 pts/unit


def test_sale_does_not_drive_stock_negative(db, fixtures):
    actor = fixtures["pro1"]
    product = fixtures["p1"]
    stock = inventory.get_product_stock(db, actor.branch_id, product.id)
    stock.quantity = 0
    db.flush()

    with pytest.raises(BusinessRuleViolation):
        sales_service.record_sale(
            db, actor, SaleCreate(product_id=str(product.id), quantity=5)
        )


def test_count_requires_note_when_difference(db, fixtures):
    actor = fixtures["pro1"]
    product = fixtures["p1"]
    stock = inventory.get_product_stock(db, actor.branch_id, product.id)
    stock.quantity = 7
    db.flush()

    with pytest.raises(CountRequiresNoteError):
        inventory.record_count(
            db,
            actor,
            CountCreate(product_id=str(product.id), observed_quantity=5),
        )

    obs = inventory.record_count(
        db,
        actor,
        CountCreate(
            product_id=str(product.id), observed_quantity=5, note="Saw 5 on the floor"
        ),
    )
    assert obs.reference_quantity == 7
    # A count observation must NOT alter the reference stock.
    assert db.get(BranchStock, stock.id).quantity == 7


def test_request_flow_no_self_approval_fulfill(db, fixtures):
    pro1 = fixtures["pro1"]
    sup1 = fixtures["sup1"]
    product = fixtures["p1"]

    request = requests_service.create_request(
        db,
        pro1,
        RequestCreate(
            type="restock",
            product_id=str(product.id),
            quantity=3,
            reason="Running low on this SKU.",
        ),
    )
    assert request.status == RequestStatus.PENDING

    from app.core.exceptions import ForbiddenError
    with pytest.raises(ForbiddenError):
        requests_service.review_request(db, pro1, request, "approved", "ok")

    reviewed = requests_service.review_request(db, sup1, request, "approved", "Approved")
    assert reviewed.status == RequestStatus.APPROVED

    fulfilled = requests_service.fulfill_request(
        db, sup1, reviewed, RequestFulfill(note="Delivered")
    )
    assert fulfilled.status == RequestStatus.FULFILLED

    stock = inventory.get_product_stock(db, pro1.branch_id, product.id)
    assert stock.quantity == 3


def test_supervisor_with_active_promoter_not_deactivatable(db, fixtures):
    admin = fixtures["admin"]
    sup1 = fixtures["sup1"]
    with pytest.raises(SupervisorHasActiveTeamError):
        users_service.deactivate_user(db, admin, sup1)


def test_created_product_sku_unique(db, fixtures):
    from app.schemas.products import ProductCreate
    from app.core.exceptions import SkuAlreadyExistsError
    from app.services import products as products_service

    payload = ProductCreate(
        sku="VX-TEST1", name="Dup", price=10
    )
    with pytest.raises(SkuAlreadyExistsError):
        products_service.create_product(db, payload)
