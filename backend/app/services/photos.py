"""Photo upload/note services."""

from __future__ import annotations

import uuid
from io import BytesIO

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.dependencies.scope import owner_ids

from app.core.config import get_settings
from app.core.enums import PhotoSource
from app.core.exceptions import NotFoundError, ValidationError
from app.models.identity import User
from app.models.photos import PhotoNote, ShelfPhoto
from app.utils.storage import build_storage, make_object_key, sha256_of
from app.dependencies.scope import require_owner


def _content_type_is_image(content_type: str) -> bool:
    return content_type.startswith("image/")


def upload_photo(
    db: Session,
    *,
    actor: User,
    filename: str,
    content_type: str,
    content: bytes,
    source: PhotoSource | None,
) -> ShelfPhoto:
    if not content:
        raise ValidationError("Uploaded file is empty")
    signatures = {
        "image/jpeg": content.startswith(b"\xff\xd8\xff"),
        "image/png": content.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": content.startswith(b"RIFF") and content[8:12] == b"WEBP",
        "image/heic": content[4:8] == b"ftyp" and content[8:12] in (b"heic", b"heix", b"mif1"),
    }
    if not signatures.get(content_type, False):
        raise ValidationError("Upload a supported JPEG, PNG, WebP or HEIC image with matching content type")
    if len(content) > 8 * 1024 * 1024:  # 8 MB cap
        raise ValidationError("Image is larger than the 8 MB limit")

    settings = get_settings()
    storage = build_storage(settings)
    key = make_object_key(folder="shelf_photos", filename=filename, content=content, content_type=content_type)
    storage.put(key=key, data=content, content_type=content_type)

    photo = ShelfPhoto(
        branch_id=actor.branch_id,
        uploaded_by=actor.id,
        object_key=key,
        content_type=content_type,
        size_bytes=len(content),
        sha256=sha256_of(content),
        source=source or PhotoSource.CAMERA,
    )
    db.add(photo)
    db.flush()
    db.refresh(photo)
    return photo


def get_photo(db: Session, photo_id: uuid.UUID) -> ShelfPhoto:
    photo = db.get(ShelfPhoto, photo_id)
    if photo is None:
        raise NotFoundError("Photo not found")
    return photo


def list_photos(
    db: Session, *, branch_id: uuid.UUID | None = None, actor: User | None = None, offset: int = 0, limit: int = 50
) -> list[ShelfPhoto]:
    return list(
        db.scalars(
            select(ShelfPhoto)
            .where(ShelfPhoto.uploaded_by.in_(owner_ids(actor)) if actor is not None else ShelfPhoto.branch_id == branch_id)
            .order_by(ShelfPhoto.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    )


def add_note(db: Session, actor: User, photo_id: uuid.UUID, body: str) -> PhotoNote:
    """Add a note to a shelf photo. Author may only note photos in their branch."""
    photo = get_photo(db, photo_id)
    db.scalar(select(ShelfPhoto).where(ShelfPhoto.id == photo_id).with_for_update())
    require_owner(db, actor, photo.uploaded_by)
    if len(body.strip()) < 5:
        raise ValidationError("Note must be at least 5 characters")

    # Editing a note invalidates any existing open review for that photo.
    from app.models.reviews import Review

    reviews = list(
        db.scalars(
            select(Review).where(
                Review.target_type == "shelf_photo", Review.target_id == photo.id
            )
        )
    )
    for review in reviews:
        review.is_current = False

    note = PhotoNote(shelf_photo_id=photo.id, author_id=actor.id, body=body)
    db.add(note)
    db.flush()
    db.refresh(note)
    return note


def list_notes(db: Session, photo_id: uuid.UUID) -> list[PhotoNote]:
    return list(
        db.scalars(
            select(PhotoNote)
            .where(PhotoNote.shelf_photo_id == photo_id)
            .order_by(PhotoNote.created_at.desc())
        )
    )


