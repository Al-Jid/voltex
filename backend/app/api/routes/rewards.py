"""Reward routes: rules, ledger, lessons, challenges."""

from __future__ import annotations

from app.api.transactional import TransactionalRoute

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.db.session import get_db
from app.dependencies.auth import CurrentUserDep
from app.models.rewards import Challenge, RewardRule
from app.schemas.rewards import (
    ChallengeEnrollRequest,
    ChallengeEnrollmentOut,
    ChallengeOut,
    LessonCompleteRequest,
    LessonCompletionOut,
    LessonOut,
    RewardRuleCreate,
    RewardRuleOut,
    RewardRuleUpdate,
    RewardSummary,
)
from app.services import rewards as rewards_service

router = APIRouter(route_class=TransactionalRoute, prefix="/rewards", tags=["rewards"])


class MonetaryBalance(BaseModel):
    balance: float


@router.get("/summary", response_model=RewardSummary)
def my_summary(current_user: CurrentUserDep, db: Session = Depends(get_db)):
    return rewards_service.summary_for(db, current_user)


@router.get("/balance", response_model=MonetaryBalance)
def my_balance(current_user: CurrentUserDep, db: Session = Depends(get_db)):
    return MonetaryBalance(balance=float(rewards_service.current_balance(db, current_user)))


@router.get("/ledger")
def my_ledger(current_user: CurrentUserDep, db: Session = Depends(get_db)):
    rows = rewards_service.list_ledger(db, current_user.id)
    return [
        {
            "points_delta": float(r.points_delta),
            "balance_after": float(r.balance_after),
            "reason": r.reason,
            "reference_type": r.reference_type,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.get("/rules", response_model=list[RewardRuleOut])
def list_rules(current_user: CurrentUserDep, db: Session = Depends(get_db)):
    return rewards_service.get_active_rules(db)


@router.post("/rules", response_model=RewardRuleOut, status_code=status.HTTP_201_CREATED)
def create_rule(payload: RewardRuleCreate, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admins manage reward rules")
    return RewardRuleOut.model_validate(rewards_service.create_rule(db, payload))


@router.patch("/rules/{rule_id}", response_model=RewardRuleOut)
def update_rule(rule_id: uuid.UUID, payload: RewardRuleUpdate, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admins manage reward rules")
    rule = db.get(RewardRule, rule_id)
    if rule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rule not found")
    return RewardRuleOut.model_validate(rewards_service.update_rule(db, rule, payload))


@router.get("/lessons", response_model=list[LessonOut])
def list_lessons(current_user: CurrentUserDep, db: Session = Depends(get_db)):
    return rewards_service.list_lessons(db)


@router.post("/lessons/{lesson_id}/complete", response_model=LessonCompletionOut)
def complete_lesson(lesson_id: uuid.UUID, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    completion = rewards_service.complete_lesson(
        db, current_user, LessonCompleteRequest(lesson_id=str(lesson_id))
    )
    return LessonCompletionOut.model_validate(completion)


@router.get("/challenges", response_model=list[ChallengeOut])
def list_challenges(current_user: CurrentUserDep, db: Session = Depends(get_db)):
    return rewards_service.list_challenges(db, active_only=True)


@router.post("/challenges/enroll", response_model=ChallengeEnrollmentOut)
def enroll_challenge(payload: ChallengeEnrollRequest, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    enrollment = rewards_service.enroll_challenge(db, current_user, payload)
    return ChallengeEnrollmentOut.model_validate(enrollment)


@router.get("/challenges/{challenge_id}/progress")
def challenge_progress(challenge_id: uuid.UUID, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    challenge = db.get(Challenge, challenge_id)
    if challenge is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Challenge not found")
    enrollment = rewards_service.refresh_enrollment_progress(db, challenge, current_user)
    return {
        "challenge_id": str(challenge_id),
        "target_units": challenge.target_units,
        "progress_units": enrollment.progress_units if enrollment else 0,
        "completed_at": enrollment.completed_at if enrollment else None,
    }


@router.get("/challenges/{challenge_id}/leaderboard")
def challenge_leaderboard(challenge_id: uuid.UUID, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    return rewards_service.leaderboard(db, challenge_id)
