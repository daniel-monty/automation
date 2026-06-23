"""Root fixtures wiring the support layer into pytest.

Skeleton: session config + auth + API client fixtures are live. UI artifact capture
is stubbed until the first UI journey is authored.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from tests.support.api_client import ApiClient
from tests.support.auth import Authenticator
from tests.support.config import Settings, get_settings


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def authenticator(settings: Settings) -> Authenticator:
    return Authenticator(settings)


@pytest.fixture
def api_client(settings: Settings, authenticator: Authenticator) -> Iterator[ApiClient]:
    """Per-test API client (tests never construct raw httpx)."""
    with ApiClient(settings.api_base_url, authenticator) as client:
        yield client
