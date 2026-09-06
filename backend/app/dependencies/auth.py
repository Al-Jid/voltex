"""FastAPI dependencies for authentication and RBAC."""

from __future__ import annotations

import uuid
from typing import Annotated, Callable, ParamSpec

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.exceptions import AuthenticationError, ForbiddenError
from app.core.security import TokenPayload, decode_access_token
from app.db.session import get_db
from app.dependencies.rbac import require_permission, require_branch_scope
from app.models.identity import User

_bearer = HTTPBearer(auto_error=False)

DB_ANNOTATED = Annotated[Session, Depends(get_db)]


def get_current_token_payload(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> TokenPayload:
    """Resolve the JWT from the Authorization header and decode it."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError("Authorization header is required")
    return decode_access_token(credentials.credentials)


def get_current_user(
    request: Request,
    payload: Annotated[TokenPayload, Depends(get_current_token_payload)],
    db: DB_ANNOTATED,
) -> User:
    """Fetch the active user for the current token payload."""
    user = db.get(User, uuid.UUID(payload.sub))
    if user is None or not user.is_active:
        raise AuthenticationError("User not found or inactive")
    if payload.auth_version != user.auth_version:
        raise AuthenticationError("Session has been revoked")
    if user.branch is None or not user.branch.is_active:
        raise ForbiddenError("Assigned branch is inactive")
    if user.must_change_password and request.url.path not in ("/api/v1/me", "/api/v1/change-password"):
        raise ForbiddenError("Password change is required")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
CurrentTokenDep = Annotated[TokenPayload, Depends(get_current_token_payload)]


def _require_permissions(payload: TokenPayload, *permissions: str) -> None:
    for permission in permissions:
        require_permission(payload, permission)


def RoleDependency(*roles: UserRole) -> Callable[..., TokenPayload]:
    """Dependency factory restricting the token payload's role to one of `roles`."""

    def dependency(payload: CurrentTokenDep) -> TokenPayload:
        if payload.role not in roles:
            raise ForbiddenError("Role not authorized for this operation")
        return payload

    return dependency
