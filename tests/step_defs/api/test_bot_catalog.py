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
from pytest_bdd import given, parsers, scenarios, then, when

from tests.support.api_client import ApiClient
from tests.support.assertions import (
    assert_active_bot_with_targets,
    assert_bot_catalog_non_empty,
    assert_bot_catalog_schema,
    assert_filter_options_schema,
    assert_security_bot_active_with_target,
    assert_security_bot_already_active,
    assert_security_bot_deactivated,
    assert_security_findings_schema,
    assert_security_insights_summary,
    assert_status,
    assert_status_one_of,
)
from tests.support.clients.bot_catalog_client import BotCatalogClient
from tests.support.models.security_bot import SecurityBotTarget

scenarios("api/bot_catalog.feature")

# Allure grouping. Use markers (not allure.dynamic.* — that is unsupported by the
# allure-pytest-bdd adapter during fixture setup and raises AttributeError). pytestmark
# applies these labels to every scenario bound in this module.
_allure: Any = allure  # allure's decorators are untyped; access via Any to satisfy mypy strict
pytestmark = [
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


@given("the Azure security bot is deactivated")
def _ensure_deactivated(bot_catalog_client: BotCatalogClient) -> None:
    bot_catalog_client.deactivate_security_bot()


@given("the Azure security bot is already active")
@given("the Azure security bot is active")
def _ensure_active(bot_catalog_client: BotCatalogClient) -> None:
    bot_catalog_client.activate_security_bot([bot_catalog_client.first_available_security_target()])


@when("I activate the Azure security bot against an available subscription")
def _activate_security_bot(bot_catalog_client: BotCatalogClient, context: dict[str, Any]) -> None:
    target = bot_catalog_client.first_available_security_target()
    context["security_bot_target"] = target
    context["response"] = bot_catalog_client.activate_security_bot([target])


@when("an unauthenticated user attempts to activate the Azure security bot")
def _activate_security_bot_unauthenticated(
    bot_catalog_client: BotCatalogClient,
    unauthenticated_bot_catalog_client: BotCatalogClient,
    context: dict[str, Any],
) -> None:
    target = bot_catalog_client.first_available_security_target()
    context["response"] = unauthenticated_bot_catalog_client.activate_security_bot([target])


@when("I deactivate the Azure security bot")
def _deactivate_security_bot(bot_catalog_client: BotCatalogClient, context: dict[str, Any]) -> None:
    context["response"] = bot_catalog_client.deactivate_security_bot()


@when(parsers.parse("I request the security bot's {dimension} filter options"))
def _request_filter_options(
    bot_catalog_client: BotCatalogClient, context: dict[str, Any], dimension: str
) -> None:
    # Stored under a per-dimension key (not "response") so it doesn't clobber the activation
    # response also captured in this same scenario.
    context[f"filter_options_response__{dimension}"] = (
        bot_catalog_client.security_insight_filter_options(dimension)
    )


@when("I request the security bot's insights summary")
def _request_insights_summary(
    bot_catalog_client: BotCatalogClient, context: dict[str, Any]
) -> None:
    context["insights_response"] = bot_catalog_client.security_insights_summary()


@when("I request the security bot's findings filtered by severity and status")
def _request_findings(bot_catalog_client: BotCatalogClient, context: dict[str, Any]) -> None:
    context["findings_response"] = bot_catalog_client.security_findings(
        page=1, page_size=50, severity=["Low", "Medium"], status=["Failed"]
    )


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


@then("the response status is 409")
def _assert_status_409(context: dict[str, Any]) -> None:
    assert_status(cast(httpx.Response, context["response"]), 409)


@then("the security bot configuration is active with the selected subscription target")
def _assert_security_bot_active(context: dict[str, Any]) -> None:
    target = cast(SecurityBotTarget, context["security_bot_target"])
    assert_security_bot_active_with_target(
        cast(httpx.Response, context["response"]),
        target.SubscriptionId,
        target.SubscriptionName,
        target.ResourceGroups,
    )


@then("the response indicates the security bot is already active")
def _assert_security_bot_conflict(context: dict[str, Any]) -> None:
    assert_security_bot_already_active(cast(httpx.Response, context["response"]))


@then("the security bot configuration is deactivated")
def _assert_security_bot_deactivated(context: dict[str, Any]) -> None:
    assert_security_bot_deactivated(cast(httpx.Response, context["response"]))


@then(parsers.parse("the security bot's {dimension} filter options are a well-formed values list"))
def _assert_filter_options(context: dict[str, Any], dimension: str) -> None:
    response = cast(httpx.Response, context[f"filter_options_response__{dimension}"])
    assert_status(response, 200)
    assert_filter_options_schema(response)


@then("the security bot's insights summary has a well-formed findings breakdown")
def _assert_insights_summary(context: dict[str, Any]) -> None:
    response = cast(httpx.Response, context["insights_response"])
    assert_status(response, 200)
    assert_security_insights_summary(response)


@then("the security bot's findings are a well-formed findings list")
def _assert_findings(context: dict[str, Any]) -> None:
    response = cast(httpx.Response, context["findings_response"])
    assert_status(response, 200)
    assert_security_findings_schema(response)
