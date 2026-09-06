"""Sync routes (offline-first cursors)."""

from __future__ import annotations

from app.api.transactional import TransactionalRoute

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import CurrentUserDep
from app.services import sync as sync_service

router = APIRouter(route_class=TransactionalRoute, prefix="/sync", tags=["sync"])


@router.get("/snapshot")
def sync_snapshot(current_user: CurrentUserDep, db: Session = Depends(get_db)):
    """Return update cursors per entity for the caller's scope."""
    return sync_service.snapshot(db, current_user)
