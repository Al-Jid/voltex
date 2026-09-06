"""Commit a mutation and its replay response together, before returning HTTP success."""
import hashlib
import json
import uuid
from datetime import datetime, timezone

from fastapi import Request
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.exceptions import AuthenticationError, ValidationError
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.identity import User
from app.services import idempotency
from app.services.audit import record


class TransactionalRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def handler(request: Request):
            if request.method not in ("POST", "PATCH", "PUT", "DELETE"):
                return await original(request)
            auth = request.headers.get("authorization", "").split(" ", 1)
            if len(auth) != 2 or auth[0].lower() != "bearer":
                raise AuthenticationError("Authorization header is required")
            claims = decode_access_token(auth[1])
            key = idempotency.require_header(request.headers.get("idempotency-key"))
            # Bound body buffering, including multipart framing; upload validation is stricter.
            content = bytearray()
            async for chunk in request.stream():
                content.extend(chunk)
                if len(content) > 9 * 1024 * 1024:
                    raise ValidationError("Request exceeds the upload limit")
            request._body = bytes(content)
            fingerprint = idempotency.request_fingerprint(request.method, str(request.url.path) + "?" + request.url.query, request._body)
            with SessionLocal() as db:
                request.state.db = db
                try:
                    user = db.get(User, uuid.UUID(claims.sub))
                    if user is None or not user.is_active:
                        raise AuthenticationError("User not found or inactive")
                    if claims.auth_version != user.auth_version or user.branch is None or not user.branch.is_active:
                        raise AuthenticationError("Session or assignment is no longer active")
                    if user.must_change_password:
                        raise AuthenticationError("Password change is required")
                    # Serialize all retries of this identity/key until commit or rollback.
                    lock = int.from_bytes(hashlib.sha256(f"{user.id}:{key}".encode()).digest()[:8], "big", signed=True)
                    db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock})
                    stored = idempotency.lookup(db, user_id=user.id, key=key)
                    if stored and stored.expires_at <= datetime.now(timezone.utc):
                        db.delete(stored)
                        db.flush()
                    effective_fingerprint = hashlib.sha256(f"{fingerprint}:{user.role}:{user.branch_id}:{user.supervisor_id}:{user.auth_version}".encode()).hexdigest()
                    replay = idempotency.get_replay(db, user_id=user.id, key=key, fingerprint=effective_fingerprint)
                    if replay is not None:
                        db.commit()
                        if replay["status"] == 204:
                            from starlette.responses import Response
                            return Response(status_code=204)
                        return JSONResponse(replay["body"], status_code=replay["status"])
                    response = await original(request)
                    if response.status_code >= 400:
                        db.rollback()
                        return response
                    body = json.loads(response.body) if response.body else {}
                    idempotency.store(db, user_id=user.id, key=key, endpoint=request.url.path[:128], fingerprint=effective_fingerprint, status=response.status_code, body=body)
                    record(db, actor=user, action=f"{request.method} {self.path}"[:64])
                    db.commit()
                    return response
                except Exception:
                    db.rollback()
                    raise
                finally:
                    del request.state.db
        return handler
