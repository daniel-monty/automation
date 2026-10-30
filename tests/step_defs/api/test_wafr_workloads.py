"""Step definitions for the Azure WAFR workload listing journey.

Layer: API E2E (httpx via WorkloadsClient — no raw httpx or Playwright).
Allure grouping: epic=Assessments / feature=WAFR Workloads / story=List.
"""

from __future__ import annotations

from typing import Any, cast

import allure
import httpx
import pytest
from pytest_bdd import parsers, scenarios, then, when

from tests.support.api_client import ApiClient
from tests.support.assertions import (
    assert_at_most_n_workloads,
    assert_each_workload_has_id,
    assert_pages_do_not_overlap,
    assert_paginated_workload_list,
    assert_status,
    assert_status_one_of,
    assert_workloads_non_empty,
)
from tests.support.clients.workloads_client import WorkloadsClient

scenarios("api/wafr_workloads.feature")

# Allure grouping. Use markers (not allure.dynamic.* — that is unsupported by the
# allure-pytest-bdd adapter during fixture setup and raises AttributeError). pytestmark
# applies these labels to every scenario bound in this module.
_allure: Any = allure  # allure's decorators are untyped; access via Any to satisfy mypy strict
pytestmark = [
    _allure.epic("Assessments"),
    _allure.feature("WAFR Workloads"),
    _allure.story("List"),
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def workloads_client(api_client: ApiClient) -> WorkloadsClient:
    """Authenticated WorkloadsClient for positive-path scenarios."""
    return WorkloadsClient(api_client)


@pytest.fixture
def unauthenticated_workloads_client(
    unauthenticated_api_client: ApiClient,
) -> WorkloadsClient:
    """WorkloadsClient with no auth headers — for asserting 401/403 rejection."""
    return WorkloadsClient(unauthenticated_api_client)


@pytest.fixture
def context() -> dict[str, Any]:
    """Per-test mutable state bag shared across step defs."""
    return {}


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------


@when(parsers.parse('I list Azure WAFR workloads with status "{status}"'))
def _list_by_status(
    workloads_client: WorkloadsClient,
    context: dict[str, Any],
    status: str,
) -> None:
    context["response"] = workloads_client.list_workloads(status=status)


@when(parsers.parse("I list Azure WAFR workloads with limit {limit:d} and offset {offset:d}"))
def _list_with_limit_offset(
    workloads_client: WorkloadsClient,
    context: dict[str, Any],
    limit: int,
    offset: int,
) -> None:
    context["response"] = workloads_client.list_workloads(limit=limit, offset=offset)


@when("an unauthenticated user lists Azure WAFR workloads")
def _list_unauthenticated(
    unauthenticated_workloads_client: WorkloadsClient,
    context: dict[str, Any],
) -> None:
    context["response"] = unauthenticated_workloads_client.list_workloads()


@when(parsers.parse("I list page {page:d} of Azure WAFR workloads with page size {size:d}"))
def _list_page(
    workloads_client: WorkloadsClient,
    context: dict[str, Any],
    page: int,
    size: int,
) -> None:
    offset = (page - 1) * size
    resp = workloads_client.list_workloads(offset=offset, limit=size)
    pages = cast(list[httpx.Response], context.setdefault("page_responses", []))
    pages.append(resp)


# ---------------------------------------------------------------------------
# Then — status
# ---------------------------------------------------------------------------


@then(parsers.parse("the response status is {expected:d}"))
def _assert_status(context: dict[str, Any], expected: int) -> None:
    assert_status(cast(httpx.Response, context["response"]), expected)


@then("the response status is 401 or 403")
def _assert_rejected(context: dict[str, Any]) -> None:
    assert_status_one_of(cast(httpx.Response, context["response"]), (401, 403))


@then("both page requests succeeded with status 200")
def _assert_page_statuses(context: dict[str, Any]) -> None:
    for resp in cast(list[httpx.Response], context["page_responses"]):
        assert_status(resp, 200)


# ---------------------------------------------------------------------------
# Then — workload domain assertions
# ---------------------------------------------------------------------------


@then("the response is a well-formed paginated workload list")
def _assert_paginated_list(context: dict[str, Any]) -> None:
    items = assert_paginated_workload_list(cast(httpx.Response, context["response"]))
    context["workload_items"] = items


@then("at least one workload is returned")
def _assert_non_empty(context: dict[str, Any]) -> None:
    assert_workloads_non_empty(cast(list[dict[str, Any]], context["workload_items"]))


@then("every workload has a workload id")
def _assert_each_has_id(context: dict[str, Any]) -> None:
    assert_each_workload_has_id(cast(list[dict[str, Any]], context["workload_items"]))


@then(parsers.parse("the response contains at most {limit:d} workloads"))
def _assert_at_most(context: dict[str, Any], limit: int) -> None:
    assert_at_most_n_workloads(cast(httpx.Response, context["response"]), limit)


@then("the two workload pages do not overlap")
def _assert_no_overlap(context: dict[str, Any]) -> None:
    pages = cast(list[httpx.Response], context["page_responses"])
    assert_pages_do_not_overlap(pages[0], pages[1])
