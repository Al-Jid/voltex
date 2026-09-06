"""Storage backend abstraction.

Photo binaries are never stored in PostgreSQL. They live on a pluggable
storage backend; the DB holds only metadata (`object_key`, content type, hash).
"""

from __future__ import annotations

import hashlib
import io
import uuid
from pathlib import Path
from typing import Any, Protocol


class StorageBackend(Protocol):
    """Minimal storage interface."""

    def put(self, *, key: str, data: bytes, content_type: str) -> None:
        ...

    def get_url(self, key: str) -> str:
        ...

    def delete(self, key: str) -> None:
        ...


class LocalDiskStorage:
    """Store files under `STORAGE_LOCAL_ROOT` (dev default)."""

    def __init__(self, root: str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, *, key: str, data: bytes, content_type: str) -> None:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as handle:
            handle.write(data)

    def get_url(self, key: str) -> str:
        return f"/files/{key}"

    def delete(self, key: str) -> None:
        path = self.root / key
        if path.exists():
            path.unlink()


class S3Storage:
    """S3-backed storage. Configure via STORAGE_S3_* env vars.

    Requires the `boto3` dependency (added only when S3 is enabled).
    Imports are deferred so dev runs never require boto3.
    """

    def __init__(
        self,
        *,
        bucket: str,
        region: str,
        endpoint: str = "",
        access_key: str = "",
        secret_key: str = "",
    ) -> None:
        import boto3

        session_kwargs: dict[str, Any] = {"region_name": region}
        if access_key and secret_key:
            session_kwargs["aws_access_key_id"] = access_key
            session_kwargs["aws_secret_access_key"] = secret_key
        client_kwargs: dict[str, Any] = {}
        if endpoint:
            client_kwargs["endpoint_url"] = endpoint
        self._client = boto3.client("s3", **session_kwargs, **client_kwargs)
        self._bucket = bucket

    def put(self, *, key: str, data: bytes, content_type: str) -> None:
        self._client.put_object(
            Bucket=self._bucket, Key=key, Body=data, ContentType=content_type
        )

    def get_url(self, key: str) -> str:
        return self._client.generate_presigned_url("get_object", Params={"Bucket": self._bucket, "Key": key}, ExpiresIn=300)

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)


def build_storage(settings: Any) -> StorageBackend:
    if settings.storage_backend == "s3":
        return S3Storage(
            bucket=settings.storage_s3_bucket,
            region=settings.storage_s3_region,
            endpoint=settings.storage_s3_endpoint,
            access_key=settings.storage_s3_access_key,
            secret_key=settings.storage_s3_secret_key,
        )
    return LocalDiskStorage(settings.storage_local_root)


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_object_key(*, folder: str, filename: str, content: bytes, content_type: str) -> str:
    digest = sha256_of(content)
    ext = _extension_for(content_type)
    return f"{folder}/{uuid.uuid4().hex[:16]}/{digest[:16]}{ext}"


def _extension_for(content_type: str) -> str:
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/heic": ".heic",
    }.get(content_type, "")
