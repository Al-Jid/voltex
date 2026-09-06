"""Audit routes."""

from __future__ import annotations

from app.api.transactional import TransactionalRoute

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.db.session import get_db
from app.dependencies.auth import CurrentUserDep
from app.services import audit as audit_service

router = APIRouter(route_class=TransactionalRoute, prefix="/audit", tags=["audit"])


class AuditEventOut(BaseModel):
    id: str
    actor_type: str
    actor_user_id: str | None = None
    action: str
    entity_type: str | None = None
    entity_id: str | None = None
    payload: dict | None = None
    created_at: str


@router.get("", response_model=list[AuditEventOut])
def list_events(
    current_user: CurrentUserDep,
    action: str | None = None,
    entity_type: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(403, "Only administrators can view the organization audit log")
    rows = audit_service.list_events(
        db, action=action, entity_type=entity_type, limit=limit
    )
    return [
        AuditEventOut(
            id=str(r.id),
            actor_type=r.actor_type,
            actor_user_id=str(r.actor_user_id) if r.actor_user_id else None,
            action=r.action,
            entity_type=r.entity_type,
            entity_id=str(r.entity_id) if r.entity_id else None,
            payload=r.payload,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]

