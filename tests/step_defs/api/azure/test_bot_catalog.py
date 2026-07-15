"""Step definitions for the Azure bot catalog journey.

Layer: API E2E (httpx via BotCatalogClient — no raw httpx or Playwright).
Allure grouping: epic=Day2 Bots / feature=Azure Bot Catalog /
story=Azure bot catalog activation and targets.
"""

from __future__ import annotations

from typing import Any, cast

import allure
import httpx
import pytest
from pytest_bdd import given, scenarios, then, when

from tests.support.api_client import ApiClient
from tests.support.assertions import (
    assert_active_bot_with_targets,
    assert_bot_catalog_non_empty,
    assert_bot_catalog_schema,
    assert_status,
    assert_status_one_of,
)
from tests.support.clients.bot_catalog_client import BotCatalogClient

scenarios("api/azure/bot_catalog.feature")

# Allure grouping. Use markers (not allure.dynamic.* — that is unsupported by the
# allure-pytest-bdd adapter during fixture setup and raises AttributeError). pytestmark
# applies these labels to every scenario bound in this module.
_allure: Any = allure  # allure's decorators are untyped; access via Any to satisfy mypy strict
pytestmark = [
    _allure.label("cloud", "Azure"),
    _allure.epic("Day2 Bots"),
    _allure.feature("Azure Bot Catalog"),
    _allure.story("Azure bot catalog activation and targets"),
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def bot_catalog_client(api_client: ApiClient) -> BotCatalogClient:
    """Authenticated BotCatalogClient for positive-path scenarios."""
    return BotCatalogClient(api_client)


@pytest.fixture
def unauthenticated_bot_catalog_client(
    unauthenticated_api_client: ApiClient,
) -> BotCatalogClient:
    """BotCatalogClient with no auth headers — for asserting 401/403 rejection."""
    return BotCatalogClient(unauthenticated_api_client)


@pytest.fixture
def context() -> dict[str, Any]:
    """Per-test mutable state bag shared across step defs."""
    return {}


# ---------------------------------------------------------------------------
# Background
# ---------------------------------------------------------------------------


@given("I am an authenticated user")
def _authenticated() -> None:
    """Auth is supplied by the api_client fixture (login via /auth/signin -> ID token)."""


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------


@when("I retrieve the Azure bot catalog")
def _retrieve(bot_catalog_client: BotCatalogClient, context: dict[str, Any]) -> None:
    context["response"] = bot_catalog_client.list_bots()


@when("an unauthenticated user retrieves the Azure bot catalog")
def _retrieve_unauthenticated(
    unauthenticated_bot_catalog_client: BotCatalogClient,
    context: dict[str, Any],
) -> None:
    context["response"] = unauthenticated_bot_catalog_client.list_bots()


# ---------------------------------------------------------------------------
# Then — status
# ---------------------------------------------------------------------------


@then("the response status is 200")
def _assert_status_200(context: dict[str, Any]) -> None:
    assert_status(cast(httpx.Response, context["response"]), 200)


@then("the response status is 401 or 403")
def _assert_rejected(context: dict[str, Any]) -> None:
    assert_status_one_of(cast(httpx.Response, context["response"]), (401, 403))


# ---------------------------------------------------------------------------
# Then — bot catalog domain assertions
# ---------------------------------------------------------------------------


@then("at least one bot in the catalog is active with configured targets")
def _assert_active_with_targets(context: dict[str, Any]) -> None:
    items = assert_bot_catalog_non_empty(cast(httpx.Response, context["response"]))
    assert_active_bot_with_targets(items)


@then("every bot in the catalog matches the confirmed schema")
def _assert_schema(context: dict[str, Any]) -> None:
    items = assert_bot_catalog_non_empty(cast(httpx.Response, context["response"]))
    assert_bot_catalog_schema(items)
