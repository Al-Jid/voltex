"""API smoke tests via FastAPI TestClient (no DB needed for schema/boot)."""

from __future__ import annotations

from fastapi.testclient import TestClient

import pytest

from app.main import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    return TestClient(app)


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_health_ready(client, monkeypatch):
    class Unavailable:
        def __enter__(self):
            raise ConnectionError("Test database unavailable")
        def __exit__(self, *args):
            return False
    monkeypatch.setattr("app.main.SessionLocal", Unavailable)
    res = client.get("/health/ready")
    assert res.status_code == 503


def test_login_validation_envelope(client):
    """Login with a short password triggers our standard 422 validation envelope."""
    res = client.post("/api/v1/login", json={"email": "a@b.com", "password": "x"})
    assert res.status_code == 422
    assert "error" in res.json()
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_me_requires_auth(client):
    res = client.get("/api/v1/me")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHENTICATED"


def test_openapi_has_api_v1_paths(client):
    spec = client.get("/api/v1/openapi.json").json()
    paths = spec["paths"]
    assert "/api/v1/login" in paths
    assert "/api/v1/sales" in paths
    assert "/api/v1/inventory/counts" in paths
    assert "/api/v1/sync/snapshot" in paths
