"""Regression cases authored during source review; execution requires explicit approval."""
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.security import create_access_token, decode_access_token
from app.core.exceptions import ForbiddenError
from app.dependencies.scope import require_owner, require_manager
from app.schemas.auth import UserOut
from app.schemas.sales import SaleOut


@pytest.mark.unit
def test_database_string_role_can_issue_token():
    token, _ = create_access_token(user_id=uuid4(), role="promoter", branch_id=uuid4())
    assert decode_access_token(token).role == "promoter"


@pytest.mark.unit
def test_user_response_accepts_database_uuid():
    row = SimpleNamespace(id=uuid4(), email="user@example.com", display_name="Test user", phone=None, role="promoter", branch_id=uuid4(), supervisor_id=uuid4(), is_active=True, must_change_password=False, last_login_at=None)
    result = UserOut.model_validate(row)
    assert result.model_dump(mode="json")["id"] == str(row.id)


@pytest.mark.unit
def test_promoter_cannot_manage_or_read_colleague():
    actor = SimpleNamespace(id=uuid4(), role="promoter")
    db = SimpleNamespace(get=lambda *args: SimpleNamespace(role="promoter", supervisor_id=uuid4()))
    with pytest.raises(ForbiddenError):
        require_manager(actor)
    with pytest.raises(ForbiddenError):
        require_owner(db, actor, uuid4())


@pytest.mark.integration
def test_price_override_does_not_change_server_price(db, fixtures):
    from app.services.inventory import get_product_stock
    from app.services.sales import record_sale
    from app.schemas.sales import SaleCreate
    stock = get_product_stock(db, fixtures["b1"].id, fixtures["p1"].id)
    stock.quantity = 5
    db.flush()
    sale = record_sale(db, fixtures["pro1"], SaleCreate(product_id=fixtures["p1"].id, quantity=1, unit_price=Decimal("1")))
    assert sale.unit_price == Decimal("100")
    assert SaleOut.model_validate(sale).total == Decimal("100")


@pytest.mark.integration
def test_other_branch_request_cannot_be_reviewed(db, fixtures):
    from app.services.requests import create_request, review_request
    from app.schemas.requests import RequestCreate
    item = create_request(db, fixtures["pro2"], RequestCreate(type="restock", product_id=fixtures["p1"].id, quantity=1, reason="Need stock"))
    with pytest.raises(ForbiddenError):
        review_request(db, fixtures["sup1"], item, "approved", "Approved")


@pytest.mark.integration
def test_http_retry_replays_sale_without_second_stock_decrement(db, fixtures, monkeypatch):
    from contextlib import nullcontext
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.services.inventory import get_product_stock
    stock = get_product_stock(db, fixtures["b1"].id, fixtures["p1"].id)
    stock.quantity = 5
    db.flush()
    monkeypatch.setattr("app.api.transactional.SessionLocal", lambda: nullcontext(db))
    token, _ = create_access_token(user_id=fixtures["pro1"].id, role="promoter", branch_id=fixtures["b1"].id)
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "same-sale"}
    with TestClient(create_app()) as client:
        payload = {"product_id": str(fixtures["p1"].id), "quantity": 2}
        first = client.post("/api/v1/sales", json=payload, headers=headers)
        second = client.post("/api/v1/sales", json=payload, headers=headers)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json() == second.json()
    db.refresh(stock)
    assert stock.quantity == 3


@pytest.mark.integration
def test_http_profile_cannot_reassign_branch(db, fixtures, monkeypatch):
    from contextlib import nullcontext
    from fastapi.testclient import TestClient
    from app.main import create_app
    monkeypatch.setattr("app.api.transactional.SessionLocal", lambda: nullcontext(db))
    promoter = fixtures["pro1"]
    token, _ = create_access_token(user_id=promoter.id, role="promoter", branch_id=promoter.branch_id)
    with TestClient(create_app()) as client:
        response = client.patch(f"/api/v1/users/{promoter.id}", json={"branch_id": str(fixtures["b2"].id)}, headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "forbidden-assignment"})
    assert response.status_code == 403
