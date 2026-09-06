"""Shared pytest fixtures.

Integration tests require a PostgreSQL database. To keep the suite runnable
without Docker/installs we use SQLAlchemy `create_all` against a scratch DB
when `DATABASE_URL` is provided; otherwise the integration tests are skipped.
"""

from __future__ import annotations

import os
import uuid
from datetime import date

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.enums import TargetPeriodType
from app.core.security import hash_password
from app.db.base import Base
import app.models  # noqa: F401  (registers models on Base.metadata)
from app.models.catalog import Product
from app.models.identity import User
from app.models.organization import Branch
from app.models.rewards import Challenge, Lesson, RewardRule
from app.models.targets import BranchTarget

_DB_ENV = os.environ.get("TEST_DATABASE_URL")


def _make_engine():
    if not _DB_ENV:
        raise RuntimeError("TEST_DATABASE_URL not set for integration tests")
    if not (make_url(_DB_ENV).database or "").endswith("_test"):
        raise RuntimeError("Integration tests require a dedicated database ending in _test")
    return create_engine(_DB_ENV, poolclass=__import__("sqlalchemy").pool.NullPool)


def pytest_configure(config):
    if not _DB_ENV:
        config.addinivalue_line("markers", "integration")


@pytest.fixture(scope="session")
def session_factory():
    if not _DB_ENV:
        pytest.skip("TEST_DATABASE_URL not set; skipping integration tests", allow_module_level=True)
    engine = _make_engine()
    schema = "voltex_test_" + uuid.uuid4().hex
    with engine.connect() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        connection.execute(text(f'SET search_path TO "{schema}", public'))
        Base.metadata.create_all(connection)
        connection.commit()
        factory = sessionmaker(bind=connection, autoflush=False, expire_on_commit=False, join_transaction_mode="create_savepoint")
        try:
            yield factory
        finally:
            connection.rollback()
            connection.execute(text('SET search_path TO public'))
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            connection.commit()
    engine.dispose()


@pytest.fixture
def db(session_factory):
    connection = session_factory.kw["bind"]
    transaction = connection.begin()
    session: Session = session_factory()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()


@pytest.fixture
def fixtures(db: Session):
    """Deterministic test rows; mirrors scripts/seed.py IDs."""

    b1 = Branch(id=uuid.UUID("10000000-0000-4000-8000-000000000001"), code="B1", name="Branch One")
    b2 = Branch(id=uuid.UUID("10000000-0000-4000-8000-000000000002"), code="B2", name="Branch Two")
    db.add_all([b1, b2])

    admin = User(
        id=uuid.UUID("20000000-0000-4000-8000-0000000000aa"),
        email="admin@voltex.app",
        display_name="System Admin",
        role="admin",
        branch_id=b1.id,
        password_hash=hash_password("admin12345"),
    )
    sup1 = User(
        id=uuid.UUID("20000000-0000-4000-8000-0000000000a1"),
        email="s1@voltex.app",
        display_name="Ahmed Ali",
        role="supervisor",
        branch_id=b1.id,
        password_hash=hash_password("password123"),
    )
    pro1 = User(
        id=uuid.UUID("20000000-0000-4000-8000-0000000000b1"),
        email="u1@voltex.app",
        display_name="Hassan Gamal",
        role="promoter",
        branch_id=b1.id,
        supervisor_id=sup1.id,
        password_hash=hash_password("password123"),
    )
    pro2 = User(
        id=uuid.UUID("20000000-0000-4000-8000-0000000000b2"),
        email="u2@voltex.app",
        display_name="Omar Khalil",
        role="promoter",
        branch_id=b2.id,
        supervisor_id=None,
        password_hash=hash_password("password123"),
    )
    db.add_all([admin, sup1, pro1, pro2])

    p1 = Product(
        id=uuid.UUID("30000000-0000-4000-8000-000000000001"),
        sku="VX-TEST1",
        name="Test Product 1",
        price=100,
    )
    p2 = Product(
        id=uuid.UUID("30000000-0000-4000-8000-000000000002"),
        sku="VX-TEST2",
        name="Test Product 2",
        price=200,
    )
    db.add_all([p1, p2])

    rule = RewardRule(
        id=uuid.UUID("60000000-0000-4000-8000-000000000001"),
        name="Per unit",
        code="sale_unit",
        metric="sale_unit",
        reward_points=10,
    )
    lesson = Lesson(
        id=uuid.UUID("40000000-0000-4000-8000-000000000001"),
        code="lesson_1",
        title="Lesson one",
        order_index=1,
    )
    db.add_all([rule, lesson])

    db.commit()

    return {
        "b1": b1,
        "b2": b2,
        "admin": admin,
        "sup1": sup1,
        "pro1": pro1,
        "pro2": pro2,
        "p1": p1,
        "p2": p2,
        "rule": rule,
        "lesson": lesson,
    }
