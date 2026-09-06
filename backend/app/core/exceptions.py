"""Application-level exception hierarchy.

All exceptions raised by services are subclasses of `APIError`, which carries a
machine-readable `code`, an HTTP `status_code`, and optional `details`.
The global exception handler converts these into the standard error envelope.
"""

from __future__ import annotations

from typing import Any


class APIError(Exception):
    """Base class for all expected application errors."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_envelope(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class ValidationError(APIError):
    status_code = 422
    code = "VALIDATION_ERROR"


class AuthenticationError(APIError):
    status_code = 401
    code = "UNAUTHENTICATED"


class InvalidCredentialsError(AuthenticationError):
    code = "INVALID_CREDENTIALS"


class InvalidTokenError(AuthenticationError):
    code = "INVALID_TOKEN"


class ExpiredTokenError(AuthenticationError):
    code = "EXPIRED_TOKEN"


class RefreshInvalidError(AuthenticationError):
    code = "REFRESH_INVALID"


class RefreshExpiredError(AuthenticationError):
    code = "REFRESH_EXPIRED"


class UserInactiveError(AuthenticationError):
    status_code = 403
    code = "USER_INACTIVE"


class ForbiddenError(APIError):
    status_code = 403
    code = "FORBIDDEN"


class NotFoundError(APIError):
    status_code = 404
    code = "RESOURCE_NOT_FOUND"


class ConflictError(APIError):
    status_code = 409
    code = "CONFLICT"


class IdempotencyKeyMismatchError(ConflictError):
    code = "IDEMPOTENCY_KEY_MISMATCH"


class RateLimitedError(APIError):
    status_code = 429
    code = "RATE_LIMITED"


class BusinessRuleViolation(ConflictError):
    """Raised when a domain rule is violated (e.g. last admin)."""

    code = "BUSINESS_RULE_VIOLATION"


# --- Specific domain rule errors (kept here for easy discoverability) ---


class EmailAlreadyExistsError(ConflictError):
    code = "EMAIL_ALREADY_EXISTS"


class SkuAlreadyExistsError(ConflictError):
    code = "SKU_ALREADY_EXISTS"


class BranchNameAlreadyExistsError(ConflictError):
    code = "BRANCH_NAME_ALREADY_EXISTS"


class SelfApprovalForbiddenError(ConflictError):
    code = "SELF_APPROVAL_FORBIDDEN"


class InvalidStateTransitionError(ConflictError):
    code = "INVALID_STATE_TRANSITION"


class CountRequiresNoteError(ConflictError):
    code = "COUNT_REQUIRES_NOTE"


class LastAdminProtectionError(ConflictError):
    code = "LAST_ADMIN_PROTECTION"


class SupervisorHasActiveTeamError(ConflictError):
    code = "SUPERVISOR_HAS_ACTIVE_TEAM"


class BranchHasActiveStaffError(ConflictError):
    code = "BRANCH_HAS_ACTIVE_STAFF"


class ActiveShiftExistsError(ConflictError):
    code = "ACTIVE_SHIFT_EXISTS"


class AssigneeNotInTeamError(ConflictError):
    code = "ASSIGNEE_NOT_IN_TEAM"