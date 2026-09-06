"""RBAC permission definitions and helper functions.

Design notes (see docs/authorization.md):

- Roles: admin (platform-wide), supervisor (branch-scoped team), promoter (create/read own data).
- Permission-style declarations, enforced by FastAPI dependencies (`require_role`, `require_permission`).
- Branch-scoping is applied per resource: a supervisor can interact with records that
  belong to their own `branch_id`; admins can interact with any branch unless restricted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from app.core.enums import UserRole
from app.core.exceptions import ForbiddenError
from app.core.security import TokenPayload


# --- Permission constants ----------------------------------------------------

# Identity
PERM_USER_READ = "user:read"
PERM_USER_MANAGE = "user:manage"
PERM_USER_DEACTIVATE = "user:deactivate"
PERM_USER_CREATE = "user:create"

# Branches
PERM_BRANCH_READ = "branch:read"
PERM_BRANCH_MANAGE = "branch:manage"

# Catalog
PERM_PRODUCT_READ = "product:read"
PERM_PRODUCT_MANAGE = "product:manage"

# Inventory
PERM_INVENTORY_READ = "inventory:read"
PERM_INVENTORY_RESTOCK = "inventory:restock"
PERM_INVENTORY_ADJUST = "inventory:adjust"
PERM_STOCK_COUNT = "stock:count"

# Requests
PERM_REQUEST_CREATE = "request:create"
PERM_REQUEST_READ = "request:read"
PERM_REQUEST_REVIEW = "request:review"
PERM_REQUEST_FULFILL = "request:fulfill"

# Reviews
PERM_REVIEW_CREATE = "review:create"
PERM_REVIEW_READ = "review:read"

# Sales
PERM_SALE_CREATE = "sale:create"
PERM_SALE_READ = "sale:read"
PERM_SALE_CANCEL = "sale:cancel"

# Attendance
PERM_ATTENDANCE_SELF = "attendance:self"
PERM_ATTENDANCE_VIEW = "attendance:view"

# Photos
PERM_PHOTO_UPLOAD = "photo:upload"
PERM_PHOTO_VIEW = "photo:view"

# Rewards
PERM_REWARD_VIEW = "reward:view"
PERM_LESSON_COMPLETE = "lesson:complete"
PERM_CHALLENGE_ENROLL = "challenge:enroll"

# Notifications
PERM_NOTIFICATION_VIEW = "notification:view"
PERM_NOTIFICATION_MANAGE = "notification:manage"

# Tasks
PERM_TASK_CREATE = "task:create"
PERM_TASK_VIEW = "task:view"
PERM_TASK_MANAGE = "task:manage"

# Targets
PERM_TARGET_VIEW = "target:view"
PERM_TARGET_MANAGE = "target:manage"

# Audit
PERM_AUDIT_VIEW = "audit:view"


@dataclass(frozen=True)
class RolePermissions:
    role: UserRole
    permissions: frozenset[str]


# --- Role→permission matrix ---------------------------------------------------

_PERMISSIONS_BY_ROLE: dict[UserRole, frozenset[str]] = {
    UserRole.ADMIN: frozenset(
        {
            # identity
            PERM_USER_READ,
            PERM_USER_MANAGE,
            PERM_USER_DEACTIVATE,
            PERM_USER_CREATE,
            # branches
            PERM_BRANCH_READ,
            PERM_BRANCH_MANAGE,
            # catalog
            PERM_PRODUCT_READ,
            PERM_PRODUCT_MANAGE,
            # inventory
            PERM_INVENTORY_READ,
            PERM_INVENTORY_RESTOCK,
            PERM_INVENTORY_ADJUST,
            PERM_STOCK_COUNT,
            # requests
            PERM_REQUEST_CREATE,
            PERM_REQUEST_READ,
            PERM_REQUEST_REVIEW,
            PERM_REQUEST_FULFILL,
            # reviews
            PERM_REVIEW_CREATE,
            PERM_REVIEW_READ,
            # sales
            PERM_SALE_CREATE,
            PERM_SALE_READ,
            PERM_SALE_CANCEL,
            # attendance
            PERM_ATTENDANCE_SELF,
            PERM_ATTENDANCE_VIEW,
            # photos
            PERM_PHOTO_UPLOAD,
            PERM_PHOTO_VIEW,
            # rewards
            PERM_REWARD_VIEW,
            PERM_LESSON_COMPLETE,
            PERM_CHALLENGE_ENROLL,
            # notifications
            PERM_NOTIFICATION_VIEW,
            PERM_NOTIFICATION_MANAGE,
            # tasks
            PERM_TASK_CREATE,
            PERM_TASK_VIEW,
            PERM_TASK_MANAGE,
            # targets
            PERM_TARGET_VIEW,
            PERM_TARGET_MANAGE,
            # audit
            PERM_AUDIT_VIEW,
        }
    ),
    UserRole.SUPERVISOR: frozenset(
        {
            PERM_BRANCH_READ,
            PERM_PRODUCT_READ,
            PERM_INVENTORY_READ,
            PERM_INVENTORY_RESTOCK,
            PERM_INVENTORY_ADJUST,
            PERM_REQUEST_READ,
            PERM_REQUEST_REVIEW,
            PERM_REQUEST_FULFILL,
            PERM_REVIEW_CREATE,
            PERM_REVIEW_READ,
            PERM_SALE_READ,
            PERM_SALE_CANCEL,
            PERM_ATTENDANCE_SELF,
            PERM_ATTENDANCE_VIEW,
            PERM_PHOTO_UPLOAD,
            PERM_PHOTO_VIEW,
            PERM_REWARD_VIEW,
            PERM_TASK_CREATE,
            PERM_TASK_VIEW,
            PERM_TASK_MANAGE,
            PERM_NOTIFICATION_VIEW,
            PERM_TARGET_VIEW,
            PERM_AUDIT_VIEW,
        }
    ),
    UserRole.PROMOTER: frozenset(
        {
            PERM_BRANCH_READ,
            PERM_PRODUCT_READ,
            PERM_INVENTORY_READ,
            PERM_STOCK_COUNT,
            PERM_REQUEST_CREATE,
            PERM_REQUEST_READ,
            PERM_SALE_CREATE,
            PERM_SALE_READ,
            PERM_ATTENDANCE_SELF,
            PERM_PHOTO_UPLOAD,
            PERM_PHOTO_VIEW,
            PERM_REWARD_VIEW,
            PERM_LESSON_COMPLETE,
            PERM_CHALLENGE_ENROLL,
            PERM_NOTIFICATION_VIEW,
            PERM_TARGET_VIEW,
        }
    ),
}


def permissions_for_role(role: UserRole) -> frozenset[str]:
    """Return the permission set for a role."""
    return _PERMISSIONS_BY_ROLE[role]


def has_permission(payload: TokenPayload, permission: str) -> bool:
    """True if the token's role grants `permission`."""
    return permission in permissions_for_role(payload.role)


def require_permission(payload: TokenPayload, permission: str) -> None:
    """Raise ForbiddenError if the token lacks `permission`."""
    if not has_permission(payload, permission):
        raise ForbiddenError("Insufficient permissions")


def require_branch_scope(payload: TokenPayload, branch_id: str) -> None:
    """Enforce that a non-admin can only act within their own branch."""
    if payload.role == UserRole.ADMIN:
        return
    if payload.branch_id != branch_id:
        raise ForbiddenError("Cannot access resources outside your branch")


def check_same_user_or_self(payload: TokenPayload, target_user_id: str) -> bool:
    """True if the caller is acting on their own user record, or is an admin."""
    if payload.role == UserRole.ADMIN:
        return True
    return payload.sub == target_user_id