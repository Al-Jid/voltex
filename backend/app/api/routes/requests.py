"""Stock request routes."""

from __future__ import annotations

from app.api.transactional import TransactionalRoute

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.enums import UserRole, RequestStatus
from app.db.session import get_db
from app.dependencies.auth import CurrentUserDep
from app.dependencies.scope import require_owner
from app.schemas.requests import (
    RequestCancel,
    RequestCreate,
    RequestFulfill,
    RequestList,
    RequestOut,
    RequestReview,
)
from app.services import requests as requests_service

router = APIRouter(route_class=TransactionalRoute, prefix="/requests", tags=["requests"])


@router.post("/{request_id}/resubmit", response_model=RequestOut)
def resubmit(request_id: uuid.UUID, payload: RequestCreate, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    from sqlalchemy import select
    from app.models.requests import StockRequest
    from app.models.catalog import Product
    from app.core.exceptions import ValidationError
    req = db.scalar(select(StockRequest).where(StockRequest.id == request_id).with_for_update())
    if req is None or req.requested_by != current_user.id:
        raise HTTPException(404, "Request not found")
    if req.status != "changes_requested":
        raise ValidationError("Only requests awaiting changes can be resubmitted")
    product = db.get(Product, payload.product_id)
    if product is None or not product.is_active:
        raise ValidationError("Product unavailable")
    req.type, req.product_id, req.quantity, req.reason = payload.type, payload.product_id, payload.quantity, payload.reason
    req.status, req.reviewed_by, req.reviewed_at, req.review_comment = "pending", None, None, None
    from app.models.reviews import Review
    for previous in db.scalars(select(Review).where(Review.target_type == "stock_request", Review.target_id == req.id)):
        previous.is_current = False
    db.flush()
    return RequestOut.model_validate(req)


@router.get("", response_model=RequestList)
def list_requests(
    current_user: CurrentUserDep,
    status_filter: RequestStatus | None = Query(default=None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    import app.core.enums as enums

    status_value = status_filter
    requester_id = current_user.id if current_user.role == UserRole.PROMOTER.value else None
    rows = requests_service.list_requests(
        db,
        actor=current_user,
        requester_id=requester_id,
        status=status_value,
        offset=(page - 1) * page_size,
        limit=page_size,
    )
    from sqlalchemy import select, func
    from app.models.requests import StockRequest
    from app.dependencies.scope import owner_ids
    count = select(func.count()).select_from(StockRequest).where(StockRequest.requested_by.in_(owner_ids(current_user)))
    if status_value is not None:
        count = count.where(StockRequest.status == status_value)
    return RequestList(items=[RequestOut.model_validate(r) for r in rows], total=db.scalar(count) or 0)


@router.get("/{request_id}", response_model=RequestOut)
def get_request(request_id: uuid.UUID, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    req = requests_service.get_request(db, request_id)
    require_owner(db, current_user, req.requested_by)
    return req


@router.post("", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
def create_request(payload: RequestCreate, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    return RequestOut.model_validate(requests_service.create_request(db, current_user, payload))


@router.post("/{request_id}/review", response_model=RequestOut)
def review_request(
    request_id: uuid.UUID,
    payload: RequestReview,
    current_user: CurrentUserDep,
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.PROMOTER.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Promoters cannot review requests")
    req = requests_service.get_request(db, request_id)
    return RequestOut.model_validate(
        requests_service.review_request(
            db, current_user, req, payload.decision.value, payload.note
        )
    )


@router.post("/{request_id}/cancel", response_model=RequestOut)
def cancel_request(
    request_id: uuid.UUID,
    payload: RequestCancel,
    current_user: CurrentUserDep,
    db: Session = Depends(get_db),
):
    req = requests_service.get_request(db, request_id)
    return RequestOut.model_validate(
        requests_service.cancel_request(db, current_user, req, payload.reason)
    )


@router.post("/{request_id}/fulfill", response_model=RequestOut)
def fulfill_request(
    request_id: uuid.UUID,
    payload: RequestFulfill,
    current_user: CurrentUserDep,
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.PROMOTER.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Promoters cannot fulfill requests")
    req = requests_service.get_request(db, request_id)
    return RequestOut.model_validate(requests_service.fulfill_request(db, current_user, req, payload))


