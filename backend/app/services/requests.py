"""Stock request services with the status state machine.

pending -> approved | changes_requested | cancelled
approved -> fulfilled (by supervisor) | cancelled
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.dependencies.scope import owner_ids

from app.core.enums import RequestStatus
from app.core.exceptions import (
    InvalidStateTransitionError,
    NotFoundError,
    SelfApprovalForbiddenError,
    ValidationError,
)
from app.models.catalog import Product
from app.models.identity import User
from app.models.requests import StockRequest
from app.dependencies.scope import require_manager, require_owner
from app.schemas.requests import (
    RequestCreate,
    RequestFulfill,
    RequestReview,
)


def create_request(db: Session, actor: User, payload: RequestCreate) -> StockRequest:
    if not (1 <= payload.quantity <= 9999):
        raise ValidationError("Quantity must be between 1 and 9999")
    if len(payload.reason.strip()) < 5:
        raise ValidationError("Reason must be at least 5 characters")

    product = db.get(Product, uuid.UUID(str(payload.product_id)))
    if product is None or not product.is_active:
        raise NotFoundError("Product not found")

    request = StockRequest(
        branch_id=actor.branch_id,
        requested_by=actor.id,
        type=payload.type,
        product_id=product.id,
        quantity=payload.quantity,
        reason=payload.reason,
        status=RequestStatus.PENDING,
    )
    db.add(request)
    db.flush()
    db.refresh(request)
    return request


def get_request(db: Session, request_id: uuid.UUID) -> StockRequest:
    request = db.get(StockRequest, request_id)
    if request is None:
        raise NotFoundError("Request not found")
    return request


def list_requests(
    db: Session,
    *,
    branch_id: uuid.UUID | None = None,
    actor: User | None = None,
    requester_id: uuid.UUID | None = None,
    status: RequestStatus | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[StockRequest]:
    stmt = select(StockRequest).order_by(StockRequest.created_at.desc())
    if actor is not None:
        stmt = stmt.where(StockRequest.requested_by.in_(owner_ids(actor)))
    if branch_id is not None:
        stmt = stmt.where(StockRequest.branch_id == branch_id)
    if requester_id is not None:
        stmt = stmt.where(StockRequest.requested_by == requester_id)
    if status is not None:
        stmt = stmt.where(StockRequest.status == status)
    return list(db.scalars(stmt.offset(offset).limit(limit)))


def review_request(
    db: Session, actor: User, request: StockRequest, decision: str, note: str | None
) -> StockRequest:
    """Approve or request changes. Reviewer cannot review own request."""
    require_manager(actor)
    require_owner(db, actor, request.requested_by)
    request = db.scalar(select(StockRequest).where(StockRequest.id == request.id).with_for_update().execution_options(populate_existing=True))
    if request.requested_by == actor.id:
        raise SelfApprovalForbiddenError("You cannot review your own request")
    if request.status != RequestStatus.PENDING:
        raise InvalidStateTransitionError(
            f"Cannot review a request in state {request.status}"
        )
    if decision not in (RequestStatus.APPROVED.value, RequestStatus.CHANGES_REQUESTED.value):
        raise ValidationError("Decision must be 'approved' or 'changes_requested'")
    if decision == RequestStatus.CHANGES_REQUESTED.value and (note is None or len(note.strip()) < 5):
        raise ValidationError("A note of at least 5 characters is required to request changes")

    request.status = RequestStatus(decision)
    request.reviewed_by = actor.id
    request.reviewed_at = datetime.now(tz=timezone.utc)
    request.review_comment = note
    from app.models.reviews import Review
    for previous in db.scalars(select(Review).where(Review.target_type == "stock_request", Review.target_id == request.id, Review.is_current.is_(True))):
        previous.is_current = False
    from app.services.notifications import notify
    from app.core.enums import NotificationType
    db.add(Review(reviewer_id=actor.id, target_type="stock_request", target_id=request.id, decision=decision, note=note or "Approved"))
    notify(db, user_id=request.requested_by, type=NotificationType.REQUEST_STATUS, title="Stock request reviewed", body=note or "Your request was approved", payload={"request_id": str(request.id), "status": decision})
    db.flush()
    db.refresh(request)
    return request


def cancel_request(db: Session, actor: User, request: StockRequest, reason: str | None) -> StockRequest:
    """The requester (or their supervisor) may cancel a pending/approved request."""
    request = db.scalar(select(StockRequest).where(StockRequest.id == request.id).with_for_update().execution_options(populate_existing=True))
    if request.status not in (RequestStatus.PENDING, RequestStatus.APPROVED):
        raise InvalidStateTransitionError(
            f"Cannot cancel a request in state {request.status}"
        )
    if request.requested_by != actor.id:
        raise ValidationError("Only the requester can cancel this request")
    request.status = RequestStatus.CANCELLED
    db.flush()
    db.refresh(request)
    return request


def fulfill_request(
    db: Session, actor: User, request: StockRequest, payload: RequestFulfill
) -> StockRequest:
    """Fulfill an approved request: add the requested quantity to branch stock."""
    require_manager(actor)
    require_owner(db, actor, request.requested_by)
    request = db.scalar(select(StockRequest).where(StockRequest.id == request.id).with_for_update().execution_options(populate_existing=True))
    if request.status != RequestStatus.APPROVED:
        raise InvalidStateTransitionError(
            f"Cannot fulfill a request in state {request.status}"
        )

    from app.services.inventory import _apply_delta
    from app.core.enums import InventoryMovementType

    if request.type == "relocate":
        from app.models.organization import Branch
        from app.services.inventory import _get_or_create_stock
        from app.dependencies.scope import require_branch
        source = payload.source_branch_id
        if source is None or source == request.branch_id:
            raise ValidationError("Select a distinct source branch for relocation")
        require_branch(db, actor, source)
        branch = db.get(Branch, source)
        if branch is None or not branch.is_active:
            raise ValidationError("Source branch is unavailable")
        for branch_id in sorted((source, request.branch_id), key=str):
            _get_or_create_stock(db, branch_id, request.product_id)
        _apply_delta(db, branch_id=source, product_id=request.product_id, delta=-request.quantity, movement_type=InventoryMovementType.TRANSFER_OUT, actor_id=actor.id, reference_type="stock_request", reference_id=request.id, note=payload.note)
        request.source_branch_id = source

    _apply_delta(
        db,
        branch_id=request.branch_id,
        product_id=request.product_id,
        delta=request.quantity,
        movement_type=InventoryMovementType.TRANSFER_IN if request.type == "relocate" else InventoryMovementType.RESTOCK,
        actor_id=actor.id,
        reference_type="stock_request",
        reference_id=request.id,
        note=payload.note or "Request fulfilled",
    )

    request.status = RequestStatus.FULFILLED
    request.fulfilled_by = actor.id
    request.fulfilled_at = datetime.now(tz=timezone.utc)
    from app.services.notifications import notify
    from app.core.enums import NotificationType
    notify(db, user_id=request.requested_by, type=NotificationType.REQUEST_STATUS, title="Stock request fulfilled", body=payload.note or "Stock has been received", payload={"request_id": str(request.id), "status": "fulfilled"})
    db.flush()
    db.refresh(request)
    return request


