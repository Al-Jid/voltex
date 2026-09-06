"""Photo routes: upload, list, notes."""

from __future__ import annotations

from app.api.transactional import TransactionalRoute

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.enums import PhotoSource, UserRole
from app.core.exceptions import APIError, ValidationError
from app.core.config import get_settings
from app.db.session import get_db
from app.dependencies.auth import CurrentUserDep
from app.dependencies.scope import require_owner
from app.schemas.photos import NoteCreate, NoteOut, PhotoOut, PhotoUploadOut
from app.services import photos as photos_service
from app.utils.storage import build_storage

router = APIRouter(route_class=TransactionalRoute, prefix="/photos", tags=["photos"])


@router.get("/{photo_id}/content")
def content(photo_id: uuid.UUID, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    photo = photos_service.get_photo(db, photo_id)
    require_owner(db, current_user, photo.uploaded_by)
    settings = get_settings()
    if settings.storage_backend == "s3":
        return RedirectResponse(build_storage(settings).get_url(photo.object_key))
    root = Path(settings.storage_local_root).resolve()
    path = (root / photo.object_key).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise HTTPException(404, "Photo file unavailable")
    return FileResponse(path, media_type=photo.content_type, headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


@router.get("", response_model=list[PhotoOut])
def list_photos(
    current_user: CurrentUserDep,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    storage = build_storage(settings)
    rows = photos_service.list_photos(db, actor=current_user, limit=limit)
    return [
        PhotoOut(
            id=str(p.id),
            branch_id=str(p.branch_id),
            uploaded_by=str(p.uploaded_by),
            object_key=p.object_key,
            content_type=p.content_type,
            size_bytes=p.size_bytes,
            source=p.source,
            created_at=p.created_at,
            url=f"/api/v1/photos/{p.id}/content",
        )
        for p in rows
    ]


@router.post("/upload", response_model=PhotoOut, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    current_user: CurrentUserDep,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    source: PhotoSource | None = Form(default=None),
):
    content = await file.read(8 * 1024 * 1024 + 1)
    photo = photos_service.upload_photo(
        db,
        actor=current_user,
        filename=file.filename or "photo.jpg",
        content_type=file.content_type or "image/jpeg",
        content=content,
        source=source,
    )
    settings = get_settings()
    storage = build_storage(settings)
    return PhotoOut(
        id=str(photo.id),
        branch_id=str(photo.branch_id),
        uploaded_by=str(photo.uploaded_by),
        object_key=photo.object_key,
        content_type=photo.content_type,
        size_bytes=photo.size_bytes,
        source=photo.source,
        created_at=photo.created_at,
        url=f"/api/v1/photos/{photo.id}/content",
    )


@router.post("/notes", response_model=NoteOut)
def add_note(
    payload: NoteCreate,
    current_user: CurrentUserDep,
    db: Session = Depends(get_db),
):
    note = photos_service.add_note(
        db, current_user, payload.photo_id, payload.body
    )
    return NoteOut.model_validate(note)


@router.get("/{photo_id}/notes", response_model=list[NoteOut])
def list_notes(photo_id: uuid.UUID, current_user: CurrentUserDep, db: Session = Depends(get_db)):
    photo = photos_service.get_photo(db, photo_id)
    require_owner(db, current_user, photo.uploaded_by)
    return [NoteOut.model_validate(n) for n in photos_service.list_notes(db, photo_id)]


