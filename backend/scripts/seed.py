"""Deterministic development seed.

Run:  python -m scripts.seed

Uses fixed UUIDs so fixtures are reproducible across environments.
The script is self-contained and safe to re-run (idempotent via lookups).
"""

from __future__ import annotations

import sys
import uuid
from datetime import date, timedelta
from decimal import Decimal
from calendar import monthrange

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import TargetPeriodType
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.catalog import Product
from app.models.identity import User
from app.models.organization import Branch
from app.models.rewards import Challenge, Lesson, RewardRule
from app.models.targets import BranchTarget
from app.models.inventory import BranchStock

# --- Fixed identifiers -------------------------------------------------------
B1 = uuid.UUID("10000000-0000-4000-8000-000000000001")
B2 = uuid.UUID("10000000-0000-4000-8000-000000000002")
B3 = uuid.UUID("10000000-0000-4000-8000-000000000003")

A1 = uuid.UUID("20000000-0000-4000-8000-0000000000aa")  # admin
S1 = uuid.UUID("20000000-0000-4000-8000-0000000000a1")  # supervisor Citystars
S2 = uuid.UUID("20000000-0000-4000-8000-0000000000a2")  # supervisor CFC
U1 = uuid.UUID("20000000-0000-4000-8000-0000000000b1")  # promoter Citystars
U2 = uuid.UUID("20000000-0000-4000-8000-0000000000b2")  # promoter CFC
U3 = uuid.UUID("20000000-0000-4000-8000-0000000000b3")  # promoter MOA
U4 = uuid.UUID("20000000-0000-4000-8000-0000000000b4")  # promoter no supervisor

P1 = uuid.UUID("30000000-0000-4000-8000-000000000001")  # VX-AC12
P2 = uuid.UUID("30000000-0000-4000-8000-000000000002")  # VX-RF320
P3 = uuid.UUID("30000000-0000-4000-8000-000000000003")  # VX-WM8
P4 = uuid.UUID("30000000-0000-4000-8000-000000000004")  # VX-TV55

L1 = uuid.UUID("40000000-0000-4000-8000-000000000001")  # sales_conversation
L2 = uuid.UUID("40000000-0000-4000-8000-000000000002")  # shelf_photo_checklist

CH1 = uuid.UUID("50000000-0000-4000-8000-000000000001")  # ten_unit

RULE_SALE = uuid.UUID("60000000-0000-4000-8000-000000000001")
RULE_LESSON = uuid.UUID("60000000-0000-4000-8000-000000000002")

DEFAULT_PASSWORD = "password123"
ADMIN_PASSWORD = "admin12345"


def seed(db: Session) -> dict[str, int]:
    from app.core.config import get_settings
    if get_settings().environment == "production":
        raise RuntimeError("Development seed is disabled in production")
    counters = {"created": 0}

    def add(obj):
        db.add(obj)
        counters["created"] += 1

    # --- Branches ------------------------------------------------------------
    for bid, code, name, address in [
        (B1, "BS-CITYSTARS", "Citystars Mall", "Nasr City"),
        (B2, "BS-CFC", "Cairo Festival City", "New Cairo"),
        (B3, "BS-MOA", "Mall of Arabia", "Sheikh Zayed"),
    ]:
        if db.get(Branch, bid) is None:
            add(Branch(id=bid, code=code, name=name, address=address))

    # --- Products ------------------------------------------------------------
    product_rows = [
        (P1, "VX-AC12", "Voltex Air Conditioner 1.5Hp", "فولتكس تكييف 1.5 حصان", "18500", 8),
        (P2, "VX-RF320", "فولتكس ثلاجة 320 لتر", "فولتكس ثلاجة 320 لتر", "24900", 8),
        (P3, "VX-WM8", "Voltex Washing Machine 8Kg", "فولتكس غسالة 8 كجم", "15750", 6),
        (P4, "VX-TV55", "Voltex Smart TV 55 inch", "فولتكس تلفزيون 55 بوصة", "21200", 5),
    ]
    for pid, sku, name, name_ar, price, daily_target in product_rows:
        if db.get(Product, pid) is None:
            add(
                Product(
                    id=pid,
                    sku=sku,
                    name=name,
                    name_ar=name_ar,
                    price=Decimal(price),
                    daily_target=daily_target,
                )
            )

    # --- Users ---------------------------------------------------------------
    user_rows = [
        (A1, "admin@voltex.app", "System Admin", "admin", B1, None),
        (S1, "s1.ahmed@voltex.app", "Ahmed Ali", "supervisor", B1, None),
        (S2, "s2.mona@voltex.app", "Mona Hassan", "supervisor", B2, None),
        (U1, "u1.hassan@voltex.app", "Hassan Gamal", "promoter", B1, S1),
        (U2, "u2.omar@voltex.app", "Omar Khalil", "promoter", B2, S2),
        (U3, "u3.laila@voltex.app", "Laila Mostafa", "promoter", B3, S2),
        (U4, "u4.maria@voltex.app", "Maria Fouad", "promoter", B3, S2),
    ]
    for uid, email, name, role, branch_id, supervisor_id in user_rows:
        if db.get(User, uid) is None:
            password = ADMIN_PASSWORD if role == "admin" else DEFAULT_PASSWORD
            add(
                User(
                    id=uid,
                    email=email,
                    display_name=name,
                    role=role,
                    branch_id=branch_id,
                    supervisor_id=supervisor_id,
                    password_hash=hash_password(password),
                )
            )

    # --- Reward rules --------------------------------------------------------
    db.flush()
    for product_id, quantity in [(P1, 18), (P2, 4), (P3, 12), (P4, 0)]:
        if db.scalar(select(BranchStock).where(BranchStock.branch_id == B1, BranchStock.product_id == product_id)) is None:
            add(BranchStock(branch_id=B1, product_id=product_id, quantity=quantity))
    if db.get(RewardRule, RULE_SALE) is None:
        add(
            RewardRule(
                id=RULE_SALE,
                name="Points per sale unit",
                code="sale_unit",
                metric="sale_unit",
                reward_points=Decimal("10"),
            )
        )
    if db.get(RewardRule, RULE_LESSON) is None:
        add(
            RewardRule(
                id=RULE_LESSON,
                name="Points per completed lesson",
                code="lesson_complete",
                metric="lesson_complete",
                reward_points=Decimal("20"),
            )
        )

    # --- Lessons --------------------------------------------------------------
    if db.get(Lesson, L1) is None:
        add(
            Lesson(
                id=L1,
                code="sales_conversation",
                title="Sales conversation essentials",
                description="How to open, pitch, close.",
                order_index=1,
            )
        )
    if db.get(Lesson, L2) is None:
        add(
            Lesson(
                id=L2,
                code="shelf_photo_checklist",
                title="Shelf photo checklist",
                description="What a valid shelf photo contains.",
                order_index=2,
            )
        )

    # --- Challenge ------------------------------------------------------------
    today = date.today()
    if db.get(Challenge, CH1) is None:
        add(
            Challenge(
                id=CH1,
                code="ten_unit",
                title="10 units in 14 days",
                description="Sell 10 units before the deadline.",
                starts_on=today,
                ends_on=today + timedelta(days=14),
                target_units=10,
                reward_points=Decimal("200"),
            )
        )

    # --- Branch targets -------------------------------------------------------
    month_start = today.replace(day=1)
    if db.scalar(
        select(BranchTarget).where(
            BranchTarget.branch_id == B1,
            BranchTarget.period_start == month_start,
        )
    ) is None:
        add(
            BranchTarget(
                branch_id=B1,
                period_type=TargetPeriodType.MONTHLY.value,
                period_start=month_start,
                period_end=today.replace(day=monthrange(today.year, today.month)[1]),
                target_amount=75000,
            )
        )
    if db.scalar(
        select(BranchTarget).where(
            BranchTarget.branch_id == B2,
            BranchTarget.period_start == month_start,
        )
    ) is None:
        add(
            BranchTarget(
                branch_id=B2,
                period_type=TargetPeriodType.MONTHLY.value,
                period_start=month_start,
                period_end=today.replace(day=monthrange(today.year, today.month)[1]),
                target_amount=60000,
            )
        )
    if db.scalar(
        select(BranchTarget).where(
            BranchTarget.branch_id == B3,
            BranchTarget.period_start == month_start,
        )
    ) is None:
        add(
            BranchTarget(
                branch_id=B3,
                period_type=TargetPeriodType.MONTHLY.value,
                period_start=month_start,
                period_end=today.replace(day=monthrange(today.year, today.month)[1]),
                target_amount=50000,
            )
        )

    db.commit()
    return counters


def main() -> None:
    db = SessionLocal()
    try:
        counters = seed(db)
        print(f"Seed complete: {counters['created']} rows created")
    finally:
        db.close()


if __name__ == "__main__":
    main()

