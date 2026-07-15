"""Placeholder step defs for the Azure security bot report-scheduling flow.

Not implemented: the backend contract for POST /reports/schedule with platformReportType
"AzureSecurityBotReport" is explicitly flagged as an open/unconfirmed question (PRD-9 §5.8;
see feature-spec/AZURE_SECURITY_BOT_E2E_STORY.html §4). Automating against a guessed shape
would risk asserting the wrong contract — confirm the real request/response shape against a
live environment before implementing.

Each scenario is allowed to genuinely start (rather than a blanket pytest.mark.skip) so it
surfaces as a tracked, skipped entry in the Allure report — tagged @manual to point at manual
verification — instead of being silently absent from collection. It then skips from its first
scenario-specific step, before any remaining (unimplemented) steps are looked up.
"""

from __future__ import annotations

from typing import Any

import allure
import pytest
from pytest_bdd import given, scenarios

scenarios("api/azure/security_bot_report_schedule.feature")

_allure: Any = allure  # allure's decorators are untyped; access via Any to satisfy mypy strict
pytestmark = [
    _allure.label("cloud", "Azure"),
    _allure.epic("Day2 Bots"),
    _allure.feature("Azure Security Bot"),
    _allure.story("Report Scheduling"),
]

_SKIP_REASON = (
    "Backend contract for POST /reports/schedule with platformReportType "
    "'AzureSecurityBotReport' is an open/unconfirmed question (PRD-9 §5.8) — verified "
    "manually for now. See feature-spec/AZURE_SECURITY_BOT_E2E_STORY.html §4."
)


@given("I am an authenticated user")
def _authenticated() -> None:
    """Auth is supplied by the api_client fixture (unused here — flow not implemented)."""


@given("filter options for subscriptions, regions, and resource groups are available")
def _skip_schedule() -> None:
    pytest.skip(reason=_SKIP_REASON)


@given("a security bot report schedule exists")
def _skip_delete() -> None:
    pytest.skip(reason=_SKIP_REASON)
