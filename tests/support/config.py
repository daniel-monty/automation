"""Typed configuration — the single source of truth, loaded from env / .env.

No magic strings or hardcoded URLs anywhere else in the suite.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All suite configuration. Env vars are prefixed `E2E_` (see `.env.example`)."""

    model_config = SettingsConfigDict(
        env_prefix="E2E_",
        env_file=".env",
        extra="ignore",
    )

    # Target environment (default: dev1).
    env: str = "dev1"
    api_base_url: str = ""
    ui_base_url: str = ""

    # Auth — HTTP /auth/signin (the platform's Cognito proxy).
    auth_signin_path: str = "/auth/signin"
    auth_refresh_path: str = "/auth/refresh-token"
    test_username: str = ""
    test_password: SecretStr = SecretStr("")
    # Authorization header scheme: "" sends the raw token; e.g. "Bearer" sends "Bearer <token>".
    auth_header_scheme: str = ""
    # x-api-key header — only if the target endpoints require it.
    api_key: SecretStr = SecretStr("")

    # Contract / fuzz (schemathesis).
    openapi_spec: str = ""


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
