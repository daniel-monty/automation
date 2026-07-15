"""Step definitions for the AWS WAR workload search journey.

Layer: API E2E (httpx via WarAssessmentWorkloadsClient — no raw httpx or Playwright).
Allure grouping: cloud=AWS / epic=Assessments / feature=WAR Workloads / story=Search.
"""

from __future__ import annotations

from typing import Any, cast

import allure
import httpx
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.support.api_client import ApiClient
from tests.support.assertions import (
    assert_all_workloads_match_keyword,
    assert_at_most_n_war_workloads,
    assert_status,
    assert_status_one_of,
    assert_war_workloads_empty,
    assert_war_workloads_non_empty,
)
from tests.support.clients.war_assessment_workloads_client import WarAssessmentWorkloadsClient

scenarios("api/aws/war_workloads.feature")

# Allure grouping. Use markers (not allure.dynamic.* — that is unsupported by the
# allure-pytest-bdd adapter during fixture setup and raises AttributeError). pytestmark
# applies these labels to every scenario bound in this module.
_allure: Any = allure  # allure's decorators are untyped; access via Any to satisfy mypy strict
pytestmark = [
    _allure.label("cloud", "AWS"),
    _allure.epic("Assessments"),
    _allure.feature("WAR Workloads"),
    _allure.story("Search"),
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def war_workloads_client(api_client: ApiClient) -> WarAssessmentWorkloadsClient:
    """Authenticated WarAssessmentWorkloadsClient for positive-path scenarios."""
    return WarAssessmentWorkloadsClient(api_client)


@pytest.fixture
def unauthenticated_war_workloads_client(
    unauthenticated_api_client: ApiClient,
) -> WarAssessmentWorkloadsClient:
    """WarAssessmentWorkloadsClient with no auth headers — for asserting 401/403 rejection."""
    return WarAssessmentWorkloadsClient(unauthenticated_api_client)


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


@when(parsers.parse('I search WAR workloads for keyword "{keyword}" with status "{status}"'))
def _search_war_by_keyword_and_status(
    war_workloads_client: WarAssessmentWorkloadsClient,
    context: dict[str, Any],
    keyword: str,
    status: str,
) -> None:
    context["response"] = war_workloads_client.search_workloads(keyword=keyword, status=status)


@when(parsers.parse('I search WAR workloads for keyword "{keyword}" with limit {limit:d}'))
def _search_war_with_limit(
    war_workloads_client: WarAssessmentWorkloadsClient,
    context: dict[str, Any],
    keyword: str,
    limit: int,
) -> None:
    context["response"] = war_workloads_client.search_workloads(keyword=keyword, limit=limit)


@when(parsers.parse('an unauthenticated user searches WAR workloads for keyword "{keyword}"'))
def _search_war_unauthenticated(
    unauthenticated_war_workloads_client: WarAssessmentWorkloadsClient,
    context: dict[str, Any],
    keyword: str,
) -> None:
    context["response"] = unauthenticated_war_workloads_client.search_workloads(keyword=keyword)


# ---------------------------------------------------------------------------
# Then — status
# ---------------------------------------------------------------------------


@then(parsers.parse("the response status is {expected:d}"))
def _assert_status(context: dict[str, Any], expected: int) -> None:
    assert_status(cast(httpx.Response, context["response"]), expected)


@then("the response status is 401 or 403")
def _assert_rejected(context: dict[str, Any]) -> None:
    assert_status_one_of(cast(httpx.Response, context["response"]), (401, 403))


# ---------------------------------------------------------------------------
# Then — AWS WAR-assessment workload search domain assertions
# ---------------------------------------------------------------------------


@then("at least one WAR workload is returned")
def _assert_war_non_empty(context: dict[str, Any]) -> None:
    items = assert_war_workloads_non_empty(cast(httpx.Response, context["response"]))
    context["war_workload_items"] = items


@then("no WAR workloads are returned")
def _assert_war_empty(context: dict[str, Any]) -> None:
    assert_war_workloads_empty(cast(httpx.Response, context["response"]))


@then(
    parsers.parse('every returned workload has the keyword "{keyword}" in its name or description')
)
def _assert_war_keyword_match(context: dict[str, Any], keyword: str) -> None:
    assert_all_workloads_match_keyword(
        cast(list[dict[str, Any]], context["war_workload_items"]), keyword
    )


@then(parsers.parse("the response contains at most {limit:d} WAR workloads"))
def _assert_war_at_most(context: dict[str, Any], limit: int) -> None:
    assert_at_most_n_war_workloads(cast(httpx.Response, context["response"]), limit)
