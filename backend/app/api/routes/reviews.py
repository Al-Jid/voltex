"""Review routes."""

from __future__ import annotations

from app.api.transactional import TransactionalRoute

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import ReviewTargetType, UserRole
from app.db.session import get_db
from app.dependencies.auth import CurrentUserDep
from app.dependencies.scope import review_target
from app.schemas.reviews import ReviewCreate, ReviewList, ReviewOut
from app.services import reviews as reviews_service

router = APIRouter(route_class=TransactionalRoute, prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(
    payload: ReviewCreate,
    target_type: ReviewTargetType,
    current_user: CurrentUserDep,
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.PROMOTER.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Promoters cannot create reviews")
    review = reviews_service.create_review(
        db, current_user, payload, target_type=target_type
    )
    return ReviewOut.model_validate(review)


@router.get("/{target_type}/{target_id}", response_model=ReviewList)
def list_reviews(
    target_type: ReviewTargetType,
    target_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: Session = Depends(get_db),
):
    review_target(db, current_user, target_type, target_id)
    rows = reviews_service.list_reviews_for_target(db, target_type, target_id)
    return ReviewList(items=[ReviewOut.model_validate(r) for r in rows], total=len(rows))

