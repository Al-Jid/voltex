"""Integration tests: full auth service flow against a real DB."""

from __future__ import annotations

import pytest

from app.core.exceptions import InvalidCredentialsError
from app.models.identity import RefreshToken, User
from app.schemas.auth import LoginRequest
from app.services import auth

pytestmark = pytest.mark.integration


def test_login_success(db, fixtures):
    tokens = auth.login(db, LoginRequest(email="u1@voltex.app", password="password123"))
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"


def test_login_unknown_email(db, fixtures):
    with pytest.raises(InvalidCredentialsError):
        auth.login(db, LoginRequest(email="nobody@voltex.app", password="password123"))


def test_login_wrong_password(db, fixtures):
    with pytest.raises(InvalidCredentialsError):
        auth.login(db, LoginRequest(email="u1@voltex.app", password="notthepassword"))


def test_refresh_rotation_invalidates_old(db, fixtures):
    tokens = auth.login(db, LoginRequest(email="u1@voltex.app", password="password123"))
    refreshed = auth.refresh(db, tokens["refresh_token"])

    # Old token is now revoked and must not be reusable.
    with pytest.raises(Exception):
        auth.refresh(db, tokens["refresh_token"])

    # New token works.
    assert refreshed["access_token"]


def test_logout_then_refresh_fails(db, fixtures):
    tokens = auth.login(db, LoginRequest(email="u1@voltex.app", password="password123"))
    auth.logout(db, tokens["refresh_token"])
    with pytest.raises(Exception):
        auth.refresh(db, tokens["refresh_token"])


def test_me_and_change_password(db, fixtures):
    user: User = fixtures["pro1"]
    from app.services import auth as auth_service

    auth_service.change_password(db, user, "password123", "newpassword1")
    # Old password fails now.
    with pytest.raises(InvalidCredentialsError):
        auth.login(db, LoginRequest(email="u1@voltex.app", password="password123"))
    # New password works.
    tokens = auth.login(db, LoginRequest(email="u1@voltex.app", password="newpassword1"))
    assert tokens["access_token"]