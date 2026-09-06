"""Rewards services: points ledger, lessons, challenges."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import RewardReferenceType
from app.core.exceptions import NotFoundError, ValidationError
from app.models.catalog import Product
from app.models.identity import User
from app.models.rewards import (
    Challenge,
    ChallengeEnrollment,
    Lesson,
    LessonCompletion,
    PointLedger,
    RewardRule,
)
from app.models.sales import Sale
from app.schemas.rewards import (
    ChallengeEnrollRequest,
    LessonCompleteRequest,
    RewardRuleCreate,
    RewardRuleUpdate,
    RewardSummary,
)


def get_active_rules(db: Session) -> list[RewardRule]:
    return list(db.scalars(select(RewardRule).where(RewardRule.is_active.is_(True))))


def create_rule(db: Session, payload: RewardRuleCreate) -> RewardRule:
    if db.scalar(select(RewardRule).where(RewardRule.code == payload.code)) is not None:
        raise ValidationError("A rule with this code already exists")
    rule = RewardRule(
        name=payload.name,
        code=payload.code,
        metric=payload.metric,
        reward_points=payload.reward_points,
        period=payload.period,
    )
    db.add(rule)
    db.flush()
    db.refresh(rule)
    return rule


def update_rule(db: Session, rule: RewardRule, payload: RewardRuleUpdate) -> RewardRule:
    for field in ("name", "metric", "reward_points", "period", "is_active"):
        value = getattr(payload, field)
        if value is not None:
            setattr(rule, field, value)
    db.flush()
    db.refresh(rule)
    return rule


def _ledger_add(
    db: Session,
    *,
    user: User,
    delta: Decimal,
    reason: str,
    reference_type: RewardReferenceType,
    reference_id: uuid.UUID | None = None,
    metadata_json: dict | None = None,
) -> PointLedger | None:
    if delta == 0:
        return None
    db.scalar(select(User).where(User.id == user.id).with_for_update())
    db.flush()
    balance = current_balance(db, user) + delta
    row = PointLedger(
        user_id=user.id,
        points_delta=delta,
        balance_after=balance,
        reason=reason,
        reference_type=reference_type,
        reference_id=reference_id,
        metadata_json=metadata_json,
    )
    db.add(row)
    return row


def current_balance(db: Session, user: User) -> Decimal:
    value = db.scalar(
        select(func.sum(PointLedger.points_delta)).where(PointLedger.user_id == user.id)
    )
    return Decimal(str(value or 0))


def list_ledger(db: Session, user_id: uuid.UUID, *, limit: int = 50) -> list[PointLedger]:
    return list(
        db.scalars(
            select(PointLedger)
            .where(PointLedger.user_id == user_id)
            .order_by(PointLedger.created_at.desc())
            .limit(limit)
        )
    )


def award_sale_points(db: Session, user: User, sale: Sale, *, quantity: int) -> PointLedger | None:
    """Award points for a recorded sale according to the `sale_unit` rule."""
    rule = db.scalar(
        select(RewardRule).where(
            RewardRule.code == "sale_unit", RewardRule.is_active.is_(True)
        )
    )
    if rule is None:
        return None
    delta = rule.reward_points * quantity
    return _ledger_add(
        db,
        user=user,
        delta=delta,
        reason=f"Sale {quantity} units",
        reference_type=RewardReferenceType.SALE,
        reference_id=sale.id,
        metadata_json={"quantity": quantity, "product_price": str(sale.unit_price)},
    )


def reverse_sale_points(db: Session, sale: Sale) -> None:
    """Reverse the points awarded for a cancelled sale."""
    rows = list(
        db.scalars(
            select(PointLedger).where(
                PointLedger.reference_type == RewardReferenceType.SALE,
                PointLedger.reference_id == sale.id,
                PointLedger.points_delta > 0,
            )
        )
    )
    for row in rows:
        user = db.get(User, row.user_id)
        if user is not None:
            _ledger_add(
                db,
                user=user,
                delta=-row.points_delta,
                reason="Sale cancelled — points reversed",
                reference_type=RewardReferenceType.SALE,
                reference_id=sale.id,
            )


# --- Lessons -----------------------------------------------------------------


def list_lessons(db: Session, *, active_only: bool = True) -> list[Lesson]:
    stmt = select(Lesson).order_by(Lesson.order_index)
    if active_only:
        stmt = stmt.where(Lesson.is_active.is_(True))
    return list(db.scalars(stmt))


def complete_lesson(
    db: Session, user: User, payload: LessonCompleteRequest
) -> LessonCompletion:
    lesson = db.get(Lesson, uuid.UUID(str(payload.lesson_id)))
    if lesson is None or not lesson.is_active:
        raise NotFoundError("Lesson not found")

    existing = db.scalar(
        select(LessonCompletion).where(
            LessonCompletion.user_id == user.id,
            LessonCompletion.lesson_id == lesson.id,
        )
    )
    if existing is not None:
        raise ValidationError("Lesson already completed")

    completion = LessonCompletion(user_id=user.id, lesson_id=lesson.id)
    db.add(completion)
    db.flush()

    rule = db.scalar(
        select(RewardRule).where(
            RewardRule.code == "lesson_complete", RewardRule.is_active.is_(True)
        )
    )
    if rule is not None:
        _ledger_add(
            db,
            user=user,
            delta=rule.reward_points,
            reason=f"Lesson: {lesson.title}",
            reference_type=RewardReferenceType.LESSON,
            reference_id=completion.id,
        )

    db.flush()
    db.refresh(completion)
    return completion


def list_lesson_completions(db: Session, user_id: uuid.UUID) -> list[LessonCompletion]:
    return list(
        db.scalars(
            select(LessonCompletion)
            .where(LessonCompletion.user_id == user_id)
            .order_by(LessonCompletion.completed_at.desc())
        )
    )


# --- Challenges ---------------------------------------------------------------


def list_challenges(db: Session, *, active_only: bool = True) -> list[Challenge]:
    stmt = select(Challenge).order_by(Challenge.starts_on)
    if active_only:
        stmt = stmt.where(Challenge.is_active.is_(True))
    return list(db.scalars(stmt))


def enroll_challenge(db: Session, user: User, payload: ChallengeEnrollRequest) -> ChallengeEnrollment:
    challenge = db.get(Challenge, uuid.UUID(str(payload.challenge_id)))
    if challenge is None or not challenge.is_active:
        raise NotFoundError("Challenge not found")
    if date.today() < challenge.starts_on or date.today() > challenge.ends_on:
        raise ValidationError("Challenge is not open for enrollment")

    existing = db.scalar(
        select(ChallengeEnrollment).where(
            ChallengeEnrollment.challenge_id == challenge.id,
            ChallengeEnrollment.user_id == user.id,
        )
    )
    if existing is not None:
        raise ValidationError("Already enrolled")

    enrollment = ChallengeEnrollment(
        challenge_id=challenge.id,
        user_id=user.id,
        progress_units=0,
    )
    db.add(enrollment)
    db.flush()
    db.refresh(enrollment)
    return enrollment


def challenge_progress(
    db: Session, challenge: Challenge, user: User
) -> int:
    """Compute progress units from recorded (non-cancelled) sales within window."""
    from app.core.enums import SaleStatus

    sum_units = db.scalar(
        select(func.sum(Sale.quantity))
        .where(
            Sale.promoter_id == user.id,
            Sale.status == SaleStatus.RECORDED,
            Sale.sold_at >= challenge.starts_on,
            Sale.sold_at <= challenge.ends_on,
        )
    )
    return int(sum_units or 0)


def refresh_enrollment_progress(
    db: Session, challenge: Challenge, user: User
) -> ChallengeEnrollment:
    enrollment = db.scalar(
        select(ChallengeEnrollment).where(
            ChallengeEnrollment.challenge_id == challenge.id,
            ChallengeEnrollment.user_id == user.id,
        )
    )
    units = challenge_progress(db, challenge, user)
    if enrollment is not None:
        enrollment.progress_units = units
        if enrollment.completed_at is None and units >= challenge.target_units:
            enrollment.completed_at = datetime.now(tz=timezone.utc)
        db.flush()
    return enrollment


def leaderboard(db: Session, challenge_id: uuid.UUID, *, limit: int = 20) -> dict:
    challenge = db.get(Challenge, challenge_id)
    if challenge is None:
        raise NotFoundError("Challenge not found")
    enrollments = list(
        db.scalars(
            select(ChallengeEnrollment)
            .where(ChallengeEnrollment.challenge_id == challenge.id)
            .order_by(ChallengeEnrollment.progress_units.desc())
            .limit(limit)
        )
    )
    rows = []
    for index, enrollment in enumerate(enrollments, start=1):
        user = db.get(User, enrollment.user_id)
        rows.append(
            {
                "rank": index,
                "user_id": str(enrollment.user_id),
                "display_name": user.display_name if user else "Unknown",
                "units": enrollment.progress_units,
            }
        )
    return {"challenge_id": str(challenge_id), "target_units": challenge.target_units, "rows": rows}


def summary_for(db: Session, user: User) -> RewardSummary:
    balance = current_balance(db, user)
    completions = list_lesson_completions(db, user.id)
    enrollments = list(
        db.scalars(select(ChallengeEnrollment).where(ChallengeEnrollment.user_id == user.id))
    )
    return RewardSummary(
        balance=balance,
        lessons_completed=len(completions),
        challenges_enrolled=len(enrollments),
    )

