"""Authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import CurrentUserDep
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    MeResponse,
    PasswordChangeResponse,
    RefreshRequest,
    TokenPair,
    UserOut,
)
from app.services import auth

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return auth.login(db, payload)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    return auth.refresh(db, payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    auth.logout(db, payload.refresh_token)


@router.get("/me", response_model=MeResponse)
def me(user: CurrentUserDep):
    return MeResponse(user=UserOut.model_validate(user))


@router.post("/change-password", response_model=PasswordChangeResponse)
def change_password(
    payload: ChangePasswordRequest,
    user: CurrentUserDep,
    db: Session = Depends(get_db),
):
    auth.change_password(db, user, payload.current_password, payload.new_password)
    return PasswordChangeResponse(ok=True)