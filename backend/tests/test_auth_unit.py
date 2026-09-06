"""Unit tests for token + hashing primitives (no DB)."""

from __future__ import annotations

import uuid

import pytest

from app.core.enums import UserRole
from app.core.exceptions import ExpiredTokenError, InvalidTokenError
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        digest = hash_password("correct horse battery staple")
        assert digest != "correct horse battery staple"
        assert verify_password("correct horse battery staple", digest) is True

    def test_wrong_password_rejected(self):
        digest = hash_password("right-password")
        assert verify_password("wrong-password", digest) is False

    def test_hash_is_unique_per_call(self):
        assert hash_password("same-pass") != hash_password("same-pass")


class TestRefreshTokenGeneration:
    def test_raw_and_hash(self):
        raw, digest = generate_refresh_token()
        assert raw != digest
        assert len(digest) == 64
        assert hash_token(raw) == digest


class TestAccessTokenRoundtrip:
    def test_roundtrip_preserves_claims(self):
        user_id = uuid.uuid4()
        token, payload = create_access_token(
            user_id=user_id, role=UserRole.PROMOTER, branch_id=uuid.UUID("10000000-0000-4000-8000-000000000001")
        )
        decoded = decode_access_token(token)
        assert decoded.sub == str(user_id)
        assert decoded.role == UserRole.PROMOTER
        assert decoded.jti == payload.jti

    def test_invalid_token_rejected(self):
        with pytest.raises(InvalidTokenError):
            decode_access_token("not-a-real-jwt")

    def test_tampered_token_rejected(self):
        token, _ = create_access_token(
            user_id=uuid.uuid4(), role=UserRole.ADMIN, branch_id=uuid.uuid4()
        )
        tampered = token[:-2] + ("aa" if not token.endswith("aa") else "bb")
        with pytest.raises((InvalidTokenError, ExpiredTokenError)):
            decode_access_token(tampered)