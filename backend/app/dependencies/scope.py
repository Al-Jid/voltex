"""Resource policies based on the current database identity, never client claims."""
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.identity import User


def require_manager(actor: User) -> None:
    if actor.role not in ("admin", "supervisor"):
        raise ForbiddenError("This operation requires a manager")


def owner_ids(actor: User):
    statement = select(User.id)
    if actor.role == "admin":
        return statement
    if actor.role == "supervisor":
        return statement.where(or_(User.id == actor.id, (User.supervisor_id == actor.id) & (User.role == "promoter")))
    return statement.where(User.id == actor.id)


def require_owner(db: Session, actor: User, owner_id) -> None:
    if actor.role == "admin" or actor.id == owner_id:
        return
    owner = db.get(User, owner_id)
    if actor.role == "supervisor" and owner and owner.role == "promoter" and owner.supervisor_id == actor.id:
        return
    raise ForbiddenError("Resource is outside your assigned scope")


def require_branch(db: Session, actor: User, branch_id) -> None:
    if actor.role == "admin" or actor.branch_id == branch_id:
        return
    if actor.role == "supervisor" and db.scalar(select(User.id).where(User.supervisor_id == actor.id, User.role == "promoter", User.is_active.is_(True), User.branch_id == branch_id).limit(1)):
        return
    raise ForbiddenError("Branch is outside your assigned scope")


def branch_ids(actor: User):
    from app.models.organization import Branch
    if actor.role == "admin":
        return select(Branch.id)
    if actor.role == "supervisor":
        return select(Branch.id).where(or_(Branch.id == actor.branch_id, Branch.id.in_(select(User.branch_id).where(User.supervisor_id == actor.id, User.role == "promoter", User.is_active.is_(True)))))
    return select(Branch.id).where(Branch.id == actor.branch_id)


def review_target(db: Session, actor: User, kind, target_id):
    from app.models.requests import StockRequest
    from app.models.photos import ShelfPhoto
    if kind == "stock_request":
        target = db.get(StockRequest, target_id)
        owner = target.requested_by if target else None
    elif kind == "shelf_photo":
        target = db.get(ShelfPhoto, target_id)
        owner = target.uploaded_by if target else None
    else:
        raise NotFoundError("Unknown target type")
    if target is None:
        raise NotFoundError("Review target not found")
    require_owner(db, actor, owner)
    return target
