"""FastAPI dependencies package."""

from app.dependencies.auth import (
    CurrentTokenDep,
    CurrentUserDep,
    DB_ANNOTATED,
    RoleDependency,
    get_current_token_payload,
    get_current_user,
)
from app.dependencies.rbac import (
    has_permission,
    require_branch_scope,
    require_permission,
)
from app.dependencies.pagination import (
    PageParamsDep,
    get_pagination,
)

__all__ = [
    "DB_ANNOTATED",
    "CurrentTokenDep",
    "CurrentUserDep",
    "RoleDependency",
    "get_current_token_payload",
    "get_current_user",
    "has_permission",
    "require_permission",
    "require_branch_scope",
    "PageParamsDep",
    "get_pagination",
]