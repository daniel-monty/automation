"""Root fixtures wiring the support layer into pytest.

Auth is arranged once per session (cached + refreshing token provider). The `api_client`
fixture is authenticated; `unauthenticated_api_client` is for negative-auth tests. UI tests
start pre-authenticated via an injected Playwright `storage_state` (arrange-via-API login) —
the one exception is the login-journey test, which should request a fresh context without it.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from tests.support.api_client import ApiClient
from tests.support.auth import Authenticator
from tests.support.config import Settings, get_settings
from tests.support.ui_auth import build_storage_state


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def authenticator(settings: Settings) -> Authenticator:
    return Authenticator(settings)


@pytest.fixture
def api_client(settings: Settings, authenticator: Authenticator) -> Iterator[ApiClient]:
    """Per-test authenticated API client (tests never construct raw httpx)."""
    with ApiClient(settings.api_base_url, authenticator) as client:
        yield client


@pytest.fixture
def unauthenticated_api_client(
    settings: Settings, authenticator: Authenticator
) -> Iterator[ApiClient]:
    """API client with NO auth headers — for asserting 401/403 rejection."""
    with ApiClient(settings.api_base_url, authenticator, authenticated=False) as client:
        yield client


@pytest.fixture(scope="session")
def ui_storage_state(settings: Settings, authenticator: Authenticator) -> dict[str, Any]:
    """Playwright storage_state with the app pre-authenticated (arrange-via-API login)."""
    return build_storage_state(settings, authenticator)


@pytest.fixture
def browser_context_args(
    browser_context_args: dict[str, Any], ui_storage_state: dict[str, Any]
) -> dict[str, Any]:
    """Inject the seeded auth state into every UI browser context.

    Overrides pytest-playwright's fixture. The login-journey test should override this back
    to a clean context (no storage_state) so it exercises the real login form.
    """
    return {**browser_context_args, "storage_state": ui_storage_state}
