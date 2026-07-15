"""Step definitions for the Azure security bot lifecycle journey.

Layer: API E2E (httpx via AzureSecurityBotClient/BotCatalogClient — no raw httpx).
Allure grouping: cloud=Azure / epic=Day2 Bots / feature=Azure Security Bot.

Scenario order in security_bot.feature mirrors the real lifecycle (activation -> scan ->
findings/suppression -> deactivation, per feature-spec/AZURE_SECURITY_BOT_E2E_STORY.html),
but each scenario still arranges its own precondition independently:

- Activation is NOT reset to a clean baseline first: the Azure Security Bot is a single,
  account-wide configuration (one BotConfiguration with a shared Targets list), not scoped
  per subscription — 409 ("already active") can fire even for a subscription that isn't yet
  in the active Targets list, whenever any other subscription in the account is active. There
  is no safe way to force a clean 200 without deactivating the whole account's bot (which would
  disrupt other subscriptions' monitoring on the shared dev1 account), so 409 is treated as a
  valid pre-existing state, not a failure. "Active" is asserted via the bot catalog (safe for
  both 200 and 409 responses), not the activate response body.
- Findings scenarios depend on real scan data existing (a bot already ACTIVE with a completed
  scan) — they don't activate/wait for a scan themselves. If no such subscription exists, or it
  has no unsuppressed findings, the scenario is skipped (not silently passed).
- Each deactivation scenario arranges its own activation so it never depends on another
  scenario's leftover state, and so activation/findings scenarios never pay the cost of a
  deactivate/reactivate cycle they didn't ask for.
"""

from __future__ import annotations

from typing import Any, cast

import allure
import httpx
import pytest
from pytest_bdd import given, scenarios, then, when

from tests.support.api_client import ApiClient
from tests.support.assertions import (
    assert_finding_is_suppressed,
    assert_findings_page_schema,
    assert_security_bot_inactive,
    assert_status,
    assert_status_one_of,
    assert_suppressed_count,
    find_first_unsuppressed_finding,
)
from tests.support.clients.azure_security_bot_client import AzureSecurityBotClient
from tests.support.clients.bot_catalog_client import BotCatalogClient
from tests.support.models.azure_security_bot import SecurityBotTarget

scenarios("api/azure/security_bot.feature")

_allure: Any = allure  # allure's decorators are untyped; access via Any to satisfy mypy strict
pytestmark = [
    _allure.label("cloud", "Azure"),
    _allure.epic("Day2 Bots"),
    _allure.feature("Azure Security Bot"),
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def azure_security_bot_client(api_client: ApiClient) -> AzureSecurityBotClient:
    return AzureSecurityBotClient(api_client)


@pytest.fixture
def unauthenticated_azure_security_bot_client(
    unauthenticated_api_client: ApiClient,
) -> AzureSecurityBotClient:
    return AzureSecurityBotClient(unauthenticated_api_client)


@pytest.fixture
def bot_catalog_client(api_client: ApiClient) -> BotCatalogClient:
    return BotCatalogClient(api_client)


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
# Given — discovery / arrangement (no baseline reset — see module docstring)
# ---------------------------------------------------------------------------


@given("a connected Azure subscription with resource groups is available")
def _discover_target(
    azure_security_bot_client: AzureSecurityBotClient, context: dict[str, Any]
) -> None:
    target = azure_security_bot_client.find_connected_target()
    if target is None:
        pytest.skip(
            "no connected Azure subscription with resource groups found in this environment"
        )
    context["target"] = target


@given("a connected subscription with completed scan findings is available")
def _require_scan_data(
    azure_security_bot_client: AzureSecurityBotClient,
    bot_catalog_client: BotCatalogClient,
    context: dict[str, Any],
) -> None:
    target = azure_security_bot_client.find_connected_target()
    if target is None or not bot_catalog_client.has_completed_scan(target.SubscriptionId):
        pytest.skip("no active bot with a completed scan found — run the activation flow first")
    context["target"] = target


@given("the security bot is activated for that subscription")
def _arrange_active(
    azure_security_bot_client: AzureSecurityBotClient, context: dict[str, Any]
) -> None:
    target = cast(SecurityBotTarget, context["target"])
    response = azure_security_bot_client.activate([target])
    assert_status_one_of(response, (200, 409))


# ---------------------------------------------------------------------------
# When — activation
# ---------------------------------------------------------------------------


@when("I activate the Azure security bot for that subscription")
def _activate(
    azure_security_bot_client: AzureSecurityBotClient,
    bot_catalog_client: BotCatalogClient,
    context: dict[str, Any],
) -> None:
    target = cast(SecurityBotTarget, context["target"])
    # Captured before activation so "eventually shows a completed scan" (below) can require a
    # *fresh* LastScanAt when this call actually triggers a new scan (200) — a 409 means the
    # bot was already active, the backend does not publish a new scan-trigger event for it, and
    # the existing LastScanAt is legitimate evidence a scan already ran, not a fresh one.
    context["previous_last_scan_at"] = bot_catalog_client.get_last_scan_at(target.SubscriptionId)
    response = azure_security_bot_client.activate([target])
    context["activation_was_fresh"] = response.status_code == httpx.codes.OK
    context["response"] = response


@when("I activate the Azure security bot for that subscription with no resource groups")
def _activate_invalid(
    azure_security_bot_client: AzureSecurityBotClient, context: dict[str, Any]
) -> None:
    target = cast(SecurityBotTarget, context["target"])
    invalid_target = SecurityBotTarget(
        SubscriptionId=target.SubscriptionId, SubscriptionName=target.SubscriptionName
    )
    context["response"] = azure_security_bot_client.activate([invalid_target])


@when("an unauthenticated user activates the Azure security bot")
def _activate_unauthenticated(
    unauthenticated_azure_security_bot_client: AzureSecurityBotClient, context: dict[str, Any]
) -> None:
    target = SecurityBotTarget(SubscriptionId="unused", ResourceGroups=["unused"])
    context["response"] = unauthenticated_azure_security_bot_client.activate([target])


# ---------------------------------------------------------------------------
# When — findings / suppression
# ---------------------------------------------------------------------------


@when("I fetch failed findings")
def _fetch_failed(
    azure_security_bot_client: AzureSecurityBotClient, context: dict[str, Any]
) -> None:
    context["response"] = azure_security_bot_client.list_findings(status="Failed")


@when("I suppress the first unsuppressed finding")
def _suppress_first(
    azure_security_bot_client: AzureSecurityBotClient, context: dict[str, Any]
) -> None:
    items = assert_findings_page_schema(cast(httpx.Response, context["response"]))
    finding = find_first_unsuppressed_finding(items)
    if finding is None:
        pytest.skip("no unsuppressed failed findings available to suppress")
    context["finding_id"] = finding["FindingId"]
    context["response"] = azure_security_bot_client.suppress_findings([finding["FindingId"]])


@when("I suppress the same finding again")
def _suppress_again(
    azure_security_bot_client: AzureSecurityBotClient, context: dict[str, Any]
) -> None:
    context["response"] = azure_security_bot_client.suppress_findings([context["finding_id"]])


# ---------------------------------------------------------------------------
# When — deactivation
# ---------------------------------------------------------------------------


@when("I deactivate the Azure security bot for all subscriptions")
def _deactivate_all(
    azure_security_bot_client: AzureSecurityBotClient, context: dict[str, Any]
) -> None:
    context["response"] = azure_security_bot_client.deactivate("all")


# ---------------------------------------------------------------------------
# Then — shared status assertions
# ---------------------------------------------------------------------------


@then("the response status is 200")
def _assert_status_200(context: dict[str, Any]) -> None:
    assert_status(cast(httpx.Response, context["response"]), 200)


@then("the response status is 200 or 409")
def _assert_status_200_or_409(context: dict[str, Any]) -> None:
    assert_status_one_of(cast(httpx.Response, context["response"]), (200, 409))


@then("the response status is 400")
def _assert_status_400(context: dict[str, Any]) -> None:
    assert_status(cast(httpx.Response, context["response"]), 400)


@then("the response status is 401 or 403")
def _assert_rejected(context: dict[str, Any]) -> None:
    assert_status_one_of(cast(httpx.Response, context["response"]), (401, 403))


# ---------------------------------------------------------------------------
# Then — activation
# ---------------------------------------------------------------------------


@then("the security bot is active for that subscription")
def _assert_active(bot_catalog_client: BotCatalogClient, context: dict[str, Any]) -> None:
    target = cast(SecurityBotTarget, context["target"])
    with allure.step(f"Bot catalog shows {target.SubscriptionId} as ACTIVE"):
        assert bot_catalog_client.is_active(target.SubscriptionId), (
            f"subscription {target.SubscriptionId} is not shown as ACTIVE in the catalog"
        )


@then("the bot catalog eventually shows a completed scan for that subscription")
def _assert_scan_completed(bot_catalog_client: BotCatalogClient, context: dict[str, Any]) -> None:
    target = cast(SecurityBotTarget, context["target"])
    # Only require a *fresh* LastScanAt when this call's activation actually triggered one
    # (200) — a 409 no-op never publishes a new scan-trigger event, so the pre-existing
    # LastScanAt from whenever the bot was first activated is legitimate, not stale test slop.
    since = (
        cast("str | None", context.get("previous_last_scan_at"))
        if context.get("activation_was_fresh")
        else None
    )
    with allure.step(f"Bot catalog eventually shows a completed scan for {target.SubscriptionId}"):
        completed = bot_catalog_client.wait_for_scan(target.SubscriptionId, since=since)
        assert completed, (
            f"scan did not complete for {target.SubscriptionId} within the retry budget"
        )


# ---------------------------------------------------------------------------
# Then — findings / suppression
# ---------------------------------------------------------------------------


@then("the suppressed finding count is 1")
def _assert_count_1(context: dict[str, Any]) -> None:
    assert_suppressed_count(cast(httpx.Response, context["response"]), 1)


@then("re-fetching findings shows it as suppressed")
def _assert_refetched_suppressed(
    azure_security_bot_client: AzureSecurityBotClient, context: dict[str, Any]
) -> None:
    response = azure_security_bot_client.list_findings(status="Failed")
    assert_finding_is_suppressed(response, cast(str, context["finding_id"]))


@then("the second suppression has a suppressed count of 0")
def _assert_count_0(context: dict[str, Any]) -> None:
    assert_suppressed_count(cast(httpx.Response, context["response"]), 0)


# ---------------------------------------------------------------------------
# Then — deactivation
# ---------------------------------------------------------------------------


@then("the security bot is inactive")
def _assert_inactive(context: dict[str, Any]) -> None:
    assert_security_bot_inactive(cast(httpx.Response, context["response"]))


@then("the bot catalog confirms the subscription is deactivated")
def _assert_catalog_deactivated(
    bot_catalog_client: BotCatalogClient, context: dict[str, Any]
) -> None:
    target = cast(SecurityBotTarget, context["target"])
    with allure.step(f"Bot catalog confirms {target.SubscriptionId} is deactivated"):
        assert bot_catalog_client.wait_for_deactivation(target.SubscriptionId), (
            f"subscription {target.SubscriptionId} still shows as active in the catalog"
        )
