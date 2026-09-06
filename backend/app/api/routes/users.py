"""User management routes."""

from __future__ import annotations

from app.api.transactional import TransactionalRoute

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.exceptions import APIError
from app.db.session import get_db
from app.dependencies.auth import CurrentUserDep
from app.dependencies.scope import require_owner
from sqlalchemy import select
from app.models.identity import User
from app.schemas.users import (
    UserCreate,
    UserDeactivateRequest,
    UserOut,
    UserUpdate,
    UsersList,
)
from app.services import users as users_service

router = APIRouter(route_class=TransactionalRoute, prefix="/users", tags=["users"])


@router.get("", response_model=UsersList)
def list_users(
    current_user: CurrentUserDep,
    role: UserRole | None = None,
    db: Session = Depends(get_db),
):
    from app.dependencies.scope import owner_ids
    statement = select(User).where(User.id.in_(owner_ids(current_user))).order_by(User.created_at.desc())
    if role is not None:
        statement = statement.where(User.role == role.value)
    rows = list(db.scalars(statement))
    return UsersList(items=[UserOut.model_validate(u) for u in rows], total=len(rows))


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: uuid.UUID, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    user = users_service.get_user(db, user_id)
    require_owner(db, current_user, user.id)
    return user


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate, current_user: CurrentUserDep, db: Session = Depends(get_db)
):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admins create users")
    return UserOut.model_validate(users_service.create_user(db, payload))


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    current_user: CurrentUserDep,
    db: Session = Depends(get_db),
):
    user = users_service.get_user(db, user_id)
    if current_user.role != UserRole.ADMIN.value and user.id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed")
    if current_user.role != UserRole.ADMIN.value and payload.model_fields_set - {"display_name", "phone"}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only administrators can change identity or assignments")
    return UserOut.model_validate(users_service.update_user(db, user, payload))


@router.post("/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(
    user_id: uuid.UUID,
    payload: UserDeactivateRequest,
    current_user: CurrentUserDep,
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admins deactivate users")
    if current_user.id == user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot deactivate yourself")
    user = users_service.get_user(db, user_id)
    return UserOut.model_validate(users_service.deactivate_user(db, current_user, user, payload.reason))


@router.post("/{user_id}/reactivate", response_model=UserOut)
def reactivate_user(
    user_id: uuid.UUID, current_user: CurrentUserDep, db: Session = Depends(get_db)
):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admins reactivate users")
    user = users_service.get_user(db, user_id)
    return UserOut.model_validate(users_service.reactivate_user(db, user))

