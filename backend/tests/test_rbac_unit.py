"""Unit tests for the RBAC permission matrix (no DB)."""

from __future__ import annotations

import uuid

import pytest

from app.core.enums import UserRole
from app.core.exceptions import ForbiddenError
from app.core.security import TokenPayload
from app.dependencies.rbac import has_permission, permissions_for_role, require_branch_scope, require_permission


def _payload(role: UserRole) -> TokenPayload:
    return TokenPayload(
        sub=str(uuid.uuid4()),
        role=role,
        branch_id="10000000-0000-4000-8000-000000000001",
        jti="j",
        iat=0,
        exp=1,
    )


def test_admin_has_everything():
    perms = permissions_for_role(UserRole.ADMIN)
    for permission in (
        "user:manage",
        "branch:manage",
        "product:manage",
        "request:review",
        "sale:cancel",
        "audit:view",
        "target:manage",
    ):
        assert permission in perms


def test_promoter_has_self_permissions_only():
    perms = permissions_for_role(UserRole.PROMOTER)
    assert "sale:create" in perms
    assert "stock:count" in perms
    assert "request:create" in perms
    # Promoters cannot review/manage.
    assert "request:review" not in perms
    assert "user:manage" not in perms
    assert "audit:view" not in perms


def test_supervisor_review_but_not_admin():
    perms = permissions_for_role(UserRole.SUPERVISOR)
    assert "request:review" in perms
    assert "request:fulfill" in perms
    assert "task:create" in perms
    assert "user:manage" not in perms
    assert "branch:manage" not in perms


def test_require_permission_raises_for_missing():
    with pytest.raises(ForbiddenError):
        require_permission(_payload(UserRole.PROMOTER), "audit:view")


def test_require_branch_scope_enforces_branch():
    with pytest.raises(ForbiddenError):
        require_branch_scope(
            _payload(UserRole.PROMOTER), "20000000-0000-4000-8000-000000000002"
        )
    # Admin bypasses branch scoping.
    require_branch_scope(
        _payload(UserRole.ADMIN), "20000000-0000-4000-8000-000000000002"
    )


def test_has_permission_boolean():
    assert has_permission(_payload(UserRole.PROMOTER), "sale:create") is True
    assert has_permission(_payload(UserRole.PROMOTER), "branch:manage") is False