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
# Azure security bot (activation) assertions. Response shape confirmed against dev1:
#   POST/DELETE /bots/azure/api/v1/security return the Config object directly (no envelope):
#   {"BotConfigurationId", "BotMasterId", "Status", "FailedFindingsCount", "LastScanAt",
#    "Targets": [{"SubscriptionId", "SubscriptionName", "ResourceGroups": [str, ...]}],
#    "CreatedAt", "UpdatedAt"}
# A 409 conflict (already active) returns {"ErrorMessage": "..."} instead of the Config.
# ---------------------------------------------------------------------------


@allure.step("Security bot is active with the requested target {subscription_id}")
def assert_security_bot_active_with_target(
    response: httpx.Response,
    subscription_id: str,
    subscription_name: str,
    resource_groups: list[str],
) -> None:
    """Assert the activation response is ACTIVE and carries the requested target."""
    body: Any = response.json()
    assert isinstance(body, dict), f"expected a JSON object, got {type(body).__name__}"
    assert body.get("BotConfigurationId"), f"expected a BotConfigurationId, got: {body!r}"
    assert body.get("Status") == "ACTIVE", f"expected Status 'ACTIVE', got: {body.get('Status')!r}"
    targets = body.get("Targets")
    assert isinstance(targets, list) and targets, (
        f"expected a non-empty Targets list, got: {targets!r}"
    )
    matching = [t for t in targets if t.get("SubscriptionId") == subscription_id]
    assert matching, f"expected target {subscription_id!r} in Targets, got: {targets!r}"
    target = matching[0]
    assert target.get("SubscriptionName") == subscription_name, (
        f"expected SubscriptionName {subscription_name!r}, got: {target.get('SubscriptionName')!r}"
    )
    assert set(target.get("ResourceGroups") or []) == set(resource_groups), (
        f"expected ResourceGroups {resource_groups!r}, got: {target.get('ResourceGroups')!r}"
    )


@allure.step("Response indicates the security bot is already active")
def assert_security_bot_already_active(response: httpx.Response) -> None:
    """Assert the 409 conflict body carries the confirmed 'already active' error message."""
    body: Any = response.json()
    assert isinstance(body, dict), f"expected a JSON object, got {type(body).__name__}"
    assert body.get("ErrorMessage") == "Azure Security Bot configuration is already active", (
        f"expected the confirmed 'already active' conflict message, got: {body!r}"
    )


@allure.step("Security bot configuration is deactivated")
def assert_security_bot_deactivated(response: httpx.Response) -> None:
    """Assert the deactivation response carries Status 'NOT_CONFIGURED'.

    Confirmed against dev1: the DELETE response's ``Targets`` list is NOT cleared (it echoes
    the last-configured targets) even though ``Status`` flips to ``NOT_CONFIGURED`` — so only
    ``Status`` is asserted here, never ``Targets`` emptiness.
    """
    body: Any = response.json()
    assert isinstance(body, dict), f"expected a JSON object, got {type(body).__name__}"
    assert body.get("Status") == "NOT_CONFIGURED", (
        f"expected Status 'NOT_CONFIGURED', got: {body.get('Status')!r}"
    )


# ---------------------------------------------------------------------------
# Azure security bot insights assertions. Response shapes confirmed against dev1:
#   GET .../security/insights/filter-options/{resource-groups,regions,resource-types} ->
#     {"Values": [str, ...], "HasMore": bool, "NextOffset": int | None}
#   GET .../security/insights ->
#     {"TotalFailedFindings": int, "LastScanAt": str, "ScanStatus": "RUNNING" | "COMPLETED" | ...,
#      "FindingsBySubscription": [{"SubscriptionId", "SubscriptionName", "Count"}],
#      "FindingsBySeverity": [{"Severity", "Count"}],
#      "FindingsByResourceType": [{"ResourceType", "Count"}],
#      "TopViolatingResources": [{"ResourceId", "ResourceType", "ResourceName", "Count"}],
#      "TopViolationChecks": [{"CheckTitle", "CheckCode", "Count"}]}
#   These are checked right after activation, when the async Azure scan the activation
#   triggers is very likely still RUNNING — so only structure is asserted here (list-typed
#   breakdowns, a non-blank ScanStatus), never scan completion or non-empty findings.
# ---------------------------------------------------------------------------


@allure.step("Filter options response is a well-formed Values list")
def assert_filter_options_schema(response: httpx.Response) -> list[Any]:
    """Assert the envelope is well-formed and return the Values list (may be empty)."""
    body: Any = response.json()
    assert isinstance(body, dict), f"expected a JSON object, got {type(body).__name__}"
    values = body.get("Values")
    assert isinstance(values, list), f"expected a 'Values' list, got keys {list(body.keys())}"
    assert isinstance(body.get("HasMore"), bool), f"expected a boolean 'HasMore', got: {body!r}"
    return values


@allure.step("Security bot insights summary has a well-formed findings breakdown")
def assert_security_insights_summary(response: httpx.Response) -> None:
    """Assert the insights summary carries a ScanStatus and well-formed findings breakdowns.

    Scan completion is async (a real external Azure job that can take minutes) — this only
    asserts the response's *structure*, not that the scan has completed or that any breakdown
    is non-empty, so the test doesn't have to wait on external scan timing.
    """
    body: Any = response.json()
    assert isinstance(body, dict), f"expected a JSON object, got {type(body).__name__}"
    assert body.get("ScanStatus"), (
        f"expected a non-blank ScanStatus, got: {body.get('ScanStatus')!r}"
    )
    for key in (
        "FindingsBySubscription",
        "FindingsBySeverity",
        "FindingsByResourceType",
        "TopViolatingResources",
        "TopViolationChecks",
    ):
        assert isinstance(body.get(key), list), f"expected a '{key}' list, got: {body.get(key)!r}"


@allure.step("Security findings response is a well-formed findings list")
def assert_security_findings_schema(response: httpx.Response) -> list[Any]:
    """Assert the findings envelope is well-formed and return the Findings list.

    Response shape confirmed against dev1:
      {"Total": int, "Page": int, "PageSize": int,
       "Findings": [{"FindingId", "CheckCode", "ResourceId", "ResourceName", "ResourceType",
                      "SubscriptionId", "Region", "RiskLevel", "Status", "Source",
                      "DetailedDescription", "PotentialBenefits", "LearnMoreLink", ...}]}
    Findings are populated by the same async Azure scan as the insights summary, so an empty
    list right after activation is expected here too — this only asserts structure (every
    finding that IS present carries the confirmed fields), never that the list is non-empty.
    Some fields (e.g. Region, Source) are legitimately null, so presence is checked, not
    truthiness.
    """
    body: Any = response.json()
    assert isinstance(body, dict), f"expected a JSON object, got {type(body).__name__}"
    findings = body.get("Findings")
    assert isinstance(findings, list), f"expected a 'Findings' list, got keys {list(body.keys())}"
    for finding in findings:
        for key in (
            "FindingId",
            "CheckCode",
            "ResourceId",
            "ResourceName",
            "ResourceType",
            "SubscriptionId",
            "Region",
            "RiskLevel",
            "Status",
            "Source",
            "DetailedDescription",
            "PotentialBenefits",
            "LearnMoreLink",
        ):
            assert key in finding, f"finding missing '{key}': {finding}"
    return findings


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
