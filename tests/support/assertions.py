"""Reusable domain assertions, wrapped as Allure steps so reports read in
business terms. Step defs call these — they never inline raw asserts.
"""

from __future__ import annotations

from typing import Any, cast

import allure
import httpx


@allure.step("Response status is {expected}")
def assert_status(response: httpx.Response, expected: int) -> None:
    """Assert an HTTP response status, surfacing the body on mismatch."""
    assert response.status_code == expected, (
        f"expected {expected}, got {response.status_code}: {response.text}"
    )


@allure.step("Response status is one of {expected}")
def assert_status_one_of(response: httpx.Response, expected: tuple[int, ...]) -> None:
    """Assert the response status is in an allowable set (e.g. 401 or 403)."""
    assert response.status_code in expected, (
        f"expected one of {expected}, got {response.status_code}: {response.text}"
    )


# ---------------------------------------------------------------------------
# Workload assertions. Response shape confirmed against dev1:
#   {"Workloads": [{"WorkloadId", "WorkloadName", "ScanStatus", ...}], "Offset": int}
# NOTE: Provider / AssessmentType / Status are *query filters*, not response fields.
# ---------------------------------------------------------------------------


def _workload_items(response: httpx.Response) -> list[dict[str, Any]]:
    """Return the 'Workloads' list, failing loudly if the envelope is wrong."""
    body: Any = response.json()
    assert isinstance(body, dict), f"expected a JSON object, got {type(body).__name__}"
    workloads = body.get("Workloads")
    assert isinstance(workloads, list), (
        f"expected a 'Workloads' list in the response, got keys {list(body.keys())}"
    )
    return cast(list[dict[str, Any]], workloads)


@allure.step("Response is a well-formed paginated workload list")
def assert_paginated_workload_list(response: httpx.Response) -> list[dict[str, Any]]:
    """Assert the body is the documented paginated envelope and return the items."""
    body: Any = response.json()
    assert isinstance(body, dict) and "Offset" in body, (
        f"expected a paginated object with an 'Offset', got: {body!r}"
    )
    return _workload_items(response)


@allure.step("At least one workload is returned")
def assert_workloads_non_empty(items: list[dict[str, Any]]) -> None:
    """Guard against a vacuous pass — the listing must actually return workloads."""
    assert items, "expected at least one workload, got an empty list"


@allure.step("Every workload has a WorkloadId")
def assert_each_workload_has_id(items: list[dict[str, Any]]) -> None:
    """Assert each returned workload carries a non-empty WorkloadId."""
    for workload in items:
        assert workload.get("WorkloadId"), f"workload missing WorkloadId: {workload}"


@allure.step("Response contains at most {limit} workloads")
def assert_at_most_n_workloads(response: httpx.Response, limit: int) -> None:
    """Assert the response contains no more than *limit* workloads."""
    items = _workload_items(response)
    assert len(items) <= limit, f"expected at most {limit} workloads, got {len(items)}"


@allure.step("The two workload pages do not overlap")
def assert_pages_do_not_overlap(
    page1_response: httpx.Response, page2_response: httpx.Response
) -> None:
    """Assert page 1 and page 2 return disjoint workloads (by WorkloadId)."""
    page1 = _workload_items(page1_response)
    page2 = _workload_items(page2_response)
    assert page1 and page2, "both pages must return workloads to verify non-overlap"
    overlap = {w.get("WorkloadId") for w in page1} & {w.get("WorkloadId") for w in page2}
    assert not overlap, f"pages overlap: {len(overlap)} duplicate workload(s)"


# ---------------------------------------------------------------------------
# Azure bot catalog assertions. Response shape confirmed against dev1:
#   {"Bots": [{"BotId", "BotCode", "BotName", "BotDescription", "PermissionURL",
#              "CloudProvider", "Status", "Metadata": {"Avatar", "TargetType"},
#              "Config": {"BotConfigurationId", "BotMasterId", "Status",
#                         "FailedFindingsCount", "LastScanAt",
#                         "Targets": [{"SubscriptionId", "SubscriptionName",
#                                      "ResourceGroups"}],
#                         "CreatedAt", "UpdatedAt"}}]}
# No query/filter params exist on this endpoint, so there is nothing to confuse with a
# response field here.
# ---------------------------------------------------------------------------


def _bot_catalog_items(response: httpx.Response) -> list[dict[str, Any]]:
    """Return the 'Bots' list, failing loudly if the envelope is wrong."""
    body: Any = response.json()
    assert isinstance(body, dict), f"expected a JSON object, got {type(body).__name__}"
    bots = body.get("Bots")
    assert isinstance(bots, list), (
        f"expected a 'Bots' list in the response, got keys {list(body.keys())}"
    )
    return cast(list[dict[str, Any]], bots)


@allure.step("Bot catalog is non-empty")
def assert_bot_catalog_non_empty(response: httpx.Response) -> list[dict[str, Any]]:
    """Assert the catalog envelope is well-formed and non-empty, returning the items."""
    items = _bot_catalog_items(response)
    assert items, "expected at least one bot in the catalog, got an empty list"
    return items


@allure.step("At least one active bot has configured targets")
def assert_active_bot_with_targets(items: list[dict[str, Any]]) -> None:
    """Assert at least one ACTIVE bot has a non-empty, well-formed Targets list.

    Each qualifying target must carry a non-blank SubscriptionId and a non-empty
    ResourceGroups list.
    """
    assert items, "expected a non-empty bot list — call assert_bot_catalog_non_empty first"
    for bot in items:
        if bot.get("Status") != "ACTIVE":
            continue
        targets = bot.get("Config", {}).get("Targets")
        if not targets:
            continue
        if all(target.get("SubscriptionId") and target.get("ResourceGroups") for target in targets):
            return
    raise AssertionError(
        "expected at least one ACTIVE bot with well-formed targets "
        "(non-blank SubscriptionId and non-empty ResourceGroups), found none"
    )


@allure.step("Every bot in the catalog matches the confirmed schema")
def assert_bot_catalog_schema(items: list[dict[str, Any]]) -> None:
    """Assert every bot carries the confirmed top-level and nested fields."""
    assert items, "expected a non-empty bot list — call assert_bot_catalog_non_empty first"
    for bot in items:
        for key in ("BotId", "BotCode", "BotName", "Status"):
            assert bot.get(key), f"bot missing '{key}': {bot}"
        metadata = bot.get("Metadata")
        assert isinstance(metadata, dict) and metadata.get("TargetType"), (
            f"bot missing 'Metadata.TargetType': {bot}"
        )
        config = bot.get("Config")
        assert isinstance(config, dict), f"bot missing 'Config': {bot}"
        for key in ("BotConfigurationId", "Status"):
            assert config.get(key), f"bot Config missing '{key}': {bot}"
        assert isinstance(config.get("Targets"), list), f"bot Config missing 'Targets' list: {bot}"


# ---------------------------------------------------------------------------
# AWS WAR-assessment workload search assertions. Response shape confirmed against dev:
#   {"Limit": int, "PageNumber": int,
#    "WorkloadSummaries": [{"WorkloadId", "WorkloadName", "Description", "Status", ...}]}
# NOTE: "Keyword"/"FTRRequest" are request *filters*, not response fields — never asserted as
# such here. "Status" happens to also be echoed per item, so it is safe to assert directly.
# ---------------------------------------------------------------------------


def _war_workload_items(response: httpx.Response) -> list[dict[str, Any]]:
    """Return the 'WorkloadSummaries' list, failing loudly if the envelope is wrong."""
    body: Any = response.json()
    assert isinstance(body, dict), f"expected a JSON object, got {type(body).__name__}"
    summaries = body.get("WorkloadSummaries")
    assert isinstance(summaries, list), (
        f"expected a 'WorkloadSummaries' list in the response, got keys {list(body.keys())}"
    )
    return cast(list[dict[str, Any]], summaries)


@allure.step("At least one WAR workload is returned")
def assert_war_workloads_non_empty(response: httpx.Response) -> list[dict[str, Any]]:
    """Assert the search returned a non-empty list of workloads, returning the items."""
    items = _war_workload_items(response)
    assert items, "expected at least one workload, got an empty list"
    return items


@allure.step("No WAR workloads are returned")
def assert_war_workloads_empty(response: httpx.Response) -> None:
    """Assert the search returned an empty result set (used for a no-match keyword)."""
    items = _war_workload_items(response)
    assert items == [], f"expected no workloads, got {len(items)}"


@allure.step("Every returned workload has the keyword '{keyword}' in its name or description")
def assert_all_workloads_match_keyword(items: list[dict[str, Any]], keyword: str) -> None:
    """Assert every workload's WorkloadName or Description contains the keyword.

    Case-insensitive substring match. Guards against a vacuous pass by requiring a non-empty
    list first (call `assert_war_workloads_non_empty` before this).
    """
    assert items, "expected a non-empty workload list — call assert_war_workloads_non_empty first"
    needle = keyword.lower()
    for workload in items:
        name = str(workload.get("WorkloadName") or "")
        description = str(workload.get("Description") or "")
        assert needle in name.lower() or needle in description.lower(), (
            f"keyword '{keyword}' not found in WorkloadName or Description: {workload}"
        )


@allure.step("Response contains at most {limit} WAR workloads")
def assert_at_most_n_war_workloads(response: httpx.Response, limit: int) -> None:
    """Assert the response contains no more than *limit* workloads."""
    items = _war_workload_items(response)
    assert len(items) <= limit, f"expected at most {limit} workloads, got {len(items)}"
