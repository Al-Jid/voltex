"""Enumerated types used across the application."""

from __future__ import annotations

from enum import Enum


class UserRole(str, Enum):
    PROMOTER = "promoter"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"


class RequestType(str, Enum):
    RESTOCK = "restock"
    RELOCATE = "relocate"


class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    CANCELLED = "cancelled"
    FULFILLED = "fulfilled"


class ReviewDecision(str, Enum):
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class ReviewTargetType(str, Enum):
    STOCK_REQUEST = "stock_request"
    SHELF_PHOTO = "shelf_photo"


class InventoryMovementType(str, Enum):
    SALE_DECREMENT = "sale_decrement"
    RESTOCK = "restock"
    COUNT_OBSERVATION = "count_observation"
    ADJUSTMENT = "adjustment"
    TRANSFER_OUT = "transfer_out"
    TRANSFER_IN = "transfer_in"


class SaleStatus(str, Enum):
    RECORDED = "recorded"
    CANCELLED = "cancelled"


class PhotoSource(str, Enum):
    CAMERA = "camera"
    LIBRARY = "library"


class TaskStatus(str, Enum):
    OPEN = "open"
    COMPLETED = "completed"


class TargetPeriodType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class NotificationType(str, Enum):
    REQUEST_STATUS = "request_status"
    TRAINING = "training"
    CHALLENGE = "challenge"
    SYSTEM = "system"


class RewardReferenceType(str, Enum):
    SALE = "sale"
    LESSON = "lesson"
    CHALLENGE = "challenge"
    MANUAL = "manual"


class AuditActor(str, Enum):
    PROMOTER = "promoter"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"
    SYSTEM = "system"