"""Review services."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import ReviewDecision, ReviewTargetType
from app.core.exceptions import NotFoundError, ValidationError
from app.models.identity import User
from app.models.reviews import Review
from app.models.requests import StockRequest
from app.models.photos import ShelfPhoto
from app.schemas.reviews import ReviewCreate
from app.dependencies.scope import require_manager, review_target


def create_review(
    db: Session,
    actor: User,
    payload: ReviewCreate,
    *,
    target_type: ReviewTargetType,
) -> Review:
    """Create a review for a stock request or shelf photo."""
    require_manager(actor)
    review_target(db, actor, target_type, payload.target_id)
    if len(payload.note.strip()) < 5:
        raise ValidationError("Note must be at least 5 characters")

    # Validate target exists and is eligible for review.
    if target_type == ReviewTargetType.STOCK_REQUEST:
        target = db.get(StockRequest, uuid.UUID(str(payload.target_id)))
        if target is None:
            raise NotFoundError("Stock request not found")
        if target.requested_by == actor.id:
            raise ValidationError("You cannot review your own request")
        from app.services.requests import review_request
        review_request(db, actor, target, payload.decision.value, payload.note)
        return db.scalars(select(Review).where(Review.target_type == target_type, Review.target_id == target.id, Review.is_current.is_(True))).first()
    elif target_type == ReviewTargetType.SHELF_PHOTO:
        photo = db.get(ShelfPhoto, uuid.UUID(str(payload.target_id)))
        if photo is None:
            raise NotFoundError("Shelf photo not found")
        db.scalar(select(ShelfPhoto).where(ShelfPhoto.id == photo.id).with_for_update())
        for previous in db.scalars(select(Review).where(Review.target_type == "shelf_photo", Review.target_id == photo.id, Review.is_current.is_(True))):
            previous.is_current = False
    else:
        raise ValidationError("Unsupported review target")

    review = Review(
        reviewer_id=actor.id,
        target_type=target_type,
        target_id=uuid.UUID(str(payload.target_id)),
        decision=payload.decision,
        note=payload.note,
    )
    db.add(review)
    db.flush()
    db.refresh(review)
    return review


def list_reviews_for_target(
    db: Session, target_type: ReviewTargetType, target_id: uuid.UUID
) -> list[Review]:
    return list(
        db.scalars(
            select(Review)
            .where(Review.target_type == target_type, Review.target_id == target_id)
            .order_by(Review.created_at.desc())
        )
    )

