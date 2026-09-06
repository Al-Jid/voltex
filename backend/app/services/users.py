"""User management services."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.exceptions import (
    EmailAlreadyExistsError,
    LastAdminProtectionError,
    NotFoundError,
    SupervisorHasActiveTeamError,
    ValidationError,
)
from app.core.security import hash_password
from app.models.identity import User
from app.models.organization import Branch
from app.schemas.auth import UserOut
from app.schemas.users import UserCreate, UserUpdate


def get_user(db: Session, user_id: uuid.UUID) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found")
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def list_users(
    db: Session,
    *,
    role: UserRole | None = None,
    branch_id: uuid.UUID | None = None,
    active_only: bool = False,
) -> list[User]:
    stmt = select(User).order_by(User.created_at.desc())
    if role is not None:
        role_value = role.value if isinstance(role, UserRole) else role
        stmt = stmt.where(User.role == role_value)
    if branch_id is not None:
        stmt = stmt.where(User.branch_id == branch_id)
    if active_only:
        stmt = stmt.where(User.is_active.is_(True))
    return list(db.scalars(stmt))


def _validate_supervisor(db: Session, supervisor_id: uuid.UUID, branch_id: uuid.UUID) -> None:
    """A promoter's supervisor must exist, be active, and belong to the same branch."""
    supervisor = db.scalar(select(User).where(User.id == supervisor_id).with_for_update().execution_options(populate_existing=True))
    if supervisor is None or supervisor.role != UserRole.SUPERVISOR.value:
        raise ValidationError("Supervisor must be a supervisor")
    if not supervisor.is_active:
        raise ValidationError("Supervisor is not active")
    if supervisor.branch is None or not supervisor.branch.is_active:
        raise ValidationError("Branch is not active")


def create_user(db: Session, payload: UserCreate) -> User:
    """Create a user. `password` placeholder hash is set; admins send `password`."""
    email = payload.email.lower()
    if get_user_by_email(db, email) is not None:
        raise EmailAlreadyExistsError("An account with this email already exists")

    branch = db.get(Branch, payload.branch_id)
    if branch is None or not branch.is_active:
        raise ValidationError("Branch does not exist or is not active")

    if payload.role == UserRole.PROMOTER.value:
        if payload.supervisor_id is None:
            raise ValidationError("Promoters require a supervisor")
        _validate_supervisor(db, payload.supervisor_id, payload.branch_id)
    else:
        if payload.supervisor_id is not None:
            raise ValidationError("Only promoters have a supervisor assignment")

    user = User(
        email=email,
        display_name=payload.display_name,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=payload.role.value,
        branch_id=payload.branch_id,
        supervisor_id=payload.supervisor_id,
        is_active=payload.is_active,
        must_change_password=payload.must_change_password,
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, payload: UserUpdate) -> User:
    """Update non-immutable user fields (role, branch, supervisor, phone, name)."""
    previous_assignment = (user.role, user.branch_id, user.supervisor_id)
    list(db.scalars(select(User).where(User.role == "admin", User.is_active.is_(True)).order_by(User.id).with_for_update()))
    if payload.role is not None and payload.role != user.role:
        if user.role == "admin" and _is_last_active_admin(db, user):
            raise LastAdminProtectionError("Keep at least one active administrator")
        if user.role == "supervisor" and _has_active_promoters(db, user.id):
            raise SupervisorHasActiveTeamError("Reassign the active team before changing this role")
        user.role = payload.role.value
        if user.role != "promoter":
            user.supervisor_id = None
    if payload.email is not None and payload.email.lower() != user.email:
        if get_user_by_email(db, payload.email.lower()) is not None:
            raise EmailAlreadyExistsError("An account with this email already exists")
        user.email = payload.email.lower()

    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.phone is not None:
        user.phone = payload.phone

    if payload.branch_id is not None and payload.branch_id != user.branch_id:
        branch = db.get(Branch, payload.branch_id)
        if branch is None or not branch.is_active:
            raise ValidationError("Branch does not exist or is not active")
        user.branch_id = payload.branch_id

    if payload.supervisor_id is not None and payload.supervisor_id != user.supervisor_id:
        _validate_supervisor(db, payload.supervisor_id, user.branch_id)
        user.supervisor_id = payload.supervisor_id
    if payload.clear_supervisor and user.role == UserRole.PROMOTER.value:
        raise ValidationError("Promoters must retain an assigned supervisor")
    if user.role == UserRole.PROMOTER.value:
        if user.supervisor_id is None:
            raise ValidationError("Promoters require a supervisor")
        _validate_supervisor(db, user.supervisor_id, user.branch_id)
    elif user.supervisor_id is not None:
        raise ValidationError("Only promoters can have a supervisor")
    if previous_assignment != (user.role, user.branch_id, user.supervisor_id):
        user.auth_version += 1
        from app.services.auth import revoke_all_user_tokens
        revoke_all_user_tokens(db, user.id)

    db.flush()
    db.refresh(user)
    return user


def _has_active_promoters(db: Session, supervisor_id: uuid.UUID) -> bool:
    count = db.scalar(
        select(func.count())
        .select_from(User)
        .where(
            User.supervisor_id == supervisor_id,
            User.is_active.is_(True),
            User.role == UserRole.PROMOTER.value,
        )
    )
    return bool(count and count > 0)


def _is_last_active_admin(db: Session, user: User) -> bool:
    if user.role != UserRole.ADMIN.value:
        return False
    count = db.scalar(
        select(func.count())
        .select_from(User)
        .where(User.role == UserRole.ADMIN.value, User.is_active.is_(True))
    )
    return bool(count and count <= 1)


def deactivate_user(db: Session, actor: User, target: User, reason: str | None = None) -> User:
    """Soft-deactivate a user, guarding platform invariants."""
    list(db.scalars(select(User).where(User.role == "admin", User.is_active.is_(True)).order_by(User.id).with_for_update()))
    db.scalar(select(User).where(User.id == target.id).with_for_update())
    if not target.is_active:
        return target

    if _is_last_active_admin(db, target):
        raise LastAdminProtectionError("Cannot deactivate the last active admin")

    if target.role == UserRole.SUPERVISOR.value and _has_active_promoters(db, target.id):
        raise SupervisorHasActiveTeamError(
            "Supervisor has active promoters; reassign or deactivate them first"
        )

    target.is_active = False
    target.auth_version += 1
    target.deactivated_at = datetime.now(tz=timezone.utc)
    from app.services.auth import revoke_all_user_tokens
    revoke_all_user_tokens(db, target.id)
    db.flush()
    db.refresh(target)
    return target


def reactivate_user(db: Session, target: User) -> User:
    branch = db.get(Branch, target.branch_id)
    if branch is None or not branch.is_active:
        raise ValidationError("Assign an active branch before reactivation")
    if target.role == "promoter":
        if target.supervisor_id is None:
            raise ValidationError("Assign a supervisor before reactivation")
        _validate_supervisor(db, target.supervisor_id, target.branch_id)
    target.is_active = True
    target.deactivated_at = None
    db.flush()
    db.refresh(target)
    return target


def delete_user(db: Session, target: User) -> None:
    """Hard-delete a user (admin utility; restricted). Removal is normally soft."""
    db.delete(target)
    db.flush()


def user_to_schema(user: User) -> UserOut:
    return UserOut(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        phone=user.phone,
        role=user.role,
        branch_id=str(user.branch_id),
        supervisor_id=str(user.supervisor_id) if user.supervisor_id else None,
        is_active=user.is_active,
        must_change_password=user.must_change_password,
        last_login_at=user.last_login_at,
    )

