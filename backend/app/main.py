"""FastAPI application entrypoint."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from starlette.exceptions import HTTPException
from sqlalchemy import text
from app.db.session import SessionLocal

from app.api.routes import (
    attendance,
    audit,
    auth,
    branches,
    inventory,
    notifications,
    photos,
    products,
    requests,
    reviews,
    rewards,
    sales,
    sync,
    targets,
    tasks,
    users,
)
from app.core.config import get_settings
from app.core.exceptions import APIError
from app.core.logging import configure_logging, get_logger

settings = get_settings()
configure_logging()
logger = get_logger("main")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/api/v1/openapi.json",
    )

    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(branches.router, prefix="/api/v1")
    app.include_router(products.router, prefix="/api/v1")
    app.include_router(inventory.router, prefix="/api/v1")
    app.include_router(sales.router, prefix="/api/v1")
    app.include_router(requests.router, prefix="/api/v1")
    app.include_router(reviews.router, prefix="/api/v1")
    app.include_router(attendance.router, prefix="/api/v1")
    app.include_router(photos.router, prefix="/api/v1")
    app.include_router(rewards.router, prefix="/api/v1")
    app.include_router(notifications.router, prefix="/api/v1")
    app.include_router(tasks.router, prefix="/api/v1")
    app.include_router(targets.router, prefix="/api/v1")
    app.include_router(audit.router, prefix="/api/v1")
    app.include_router(sync.router, prefix="/api/v1")

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["system"])
    def ready() -> dict[str, str]:
        try:
            with SessionLocal() as db:
                db.execute(text("SELECT 1"))
        except Exception:
            raise HTTPException(503, "Database unavailable")
        return {"status": "ready"}

    @app.exception_handler(APIError)
    async def api_error_handler(_: Request, exc: APIError) -> JSONResponse:
        logger.warning("api_error code=%s message=%s", exc.code, exc.message)
        return JSONResponse(status_code=exc.status_code, content=exc.to_envelope())

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [{k: v for k, v in error.items() if k not in ("input", "ctx")} for error in exc.errors()]
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {"errors": jsonable_encoder(details)},
                }
            },
        )

    @app.exception_handler(HTTPException)
    async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
        codes = {400: "BAD_REQUEST", 401: "UNAUTHENTICATED", 403: "FORBIDDEN", 404: "RESOURCE_NOT_FOUND", 409: "CONFLICT", 503: "UNAVAILABLE"}
        return JSONResponse(status_code=exc.status_code, headers=exc.headers, content={"error": {"code": codes.get(exc.status_code, "HTTP_ERROR"), "message": str(exc.detail), "details": {}}})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error",
                    "details": {},
                }
            },
        )

    return app


app = create_app()
