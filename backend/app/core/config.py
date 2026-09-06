"""Application configuration loaded from environment variables.

Single source of truth — all settings live here. Read once via `get_settings()`.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process-wide configuration.

    All values are loaded from environment variables (see `.env.example`).
    Do not place secrets in source code.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="voltex-backend")
    app_version: str = Field(default="0.1.0")
    environment: Literal["development", "staging", "production", "test"] = "development"
    log_level: str = "INFO"

    # Database
    database_url: str = Field(
        default="postgresql+psycopg://voltex:voltex@localhost:5432/voltex",
        description="SQLAlchemy database URL.",
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_echo: bool = False

    # JWT
    jwt_secret: str = Field(
        default="change-me-in-production",
        description="HMAC secret for signing access tokens.",
    )
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "voltex-backend"
    jwt_audience: str = "voltex-mobile"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 14

    # Passwords
    password_hash_rounds: int = 12

    # Storage backend
    storage_backend: Literal["local_disk", "s3"] = "local_disk"
    storage_local_root: str = "./storage"
    storage_s3_bucket: str = ""
    storage_s3_region: str = ""
    storage_s3_endpoint: str = ""
    storage_s3_access_key: str = ""
    storage_s3_secret_key: str = ""

    # CORS
    cors_origins: str = ""

    # Idempotency
    idempotency_ttl_hours: int = 24

    @model_validator(mode="after")
    def validate_production(self):
        if self.environment == "production" and (self.jwt_secret == "change-me-in-production" or len(self.jwt_secret) < 32):
            raise ValueError("Production requires an independently configured JWT secret of at least 32 characters")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached settings instance."""
    return Settings()
