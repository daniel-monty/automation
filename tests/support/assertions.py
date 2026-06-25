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
