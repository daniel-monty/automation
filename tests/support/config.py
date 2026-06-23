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

    # Auth.
    api_key: SecretStr = SecretStr("")
    cognito_region: str = "us-east-1"
    cognito_user_pool_id: str = ""
    cognito_client_id: str = ""
    test_username: str = ""
    test_password: SecretStr = SecretStr("")

    # Contract / fuzz (schemathesis).
    openapi_spec: str = ""

    # AI failure triage (optional, off the gating path).
    llm_provider: str = ""
    llm_api_key: SecretStr = SecretStr("")
    llm_model: str = ""

    # Jira (requirement links + known-issues sync; optional).
    jira_base_url: str = ""
    jira_project_key: str = ""


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
