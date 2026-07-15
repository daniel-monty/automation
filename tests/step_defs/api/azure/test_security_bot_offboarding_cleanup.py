"""Placeholder step defs for the Azure security bot offboarding-cleanup flow.

Not implemented via the public API: there is no synchronous "delete account" endpoint in
this domain. Cleanup is triggered by EventBridge events (customeraccount.azureOffboardingSuccess
/ azureDay2OnlyAccountDisconnectionCompleted) consumed by Lambdas that hard-delete
azure_security_bot_findings/bot_scope rows — automating it needs either direct boto3
events.put_events publish rights or driving the real customeraccount offboarding flow, both out
of scope for this pytest/httpx-only suite for now. See
feature-spec/AZURE_SECURITY_BOT_E2E_STORY.html §6.

The scenario is allowed to genuinely start (rather than a blanket pytest.mark.skip) so it
surfaces as a tracked, skipped entry in the Allure report — tagged @manual to point at
manual/boto3-assisted verification — instead of being silently absent from collection. It then
skips from the first step, before any remaining (unimplemented) steps are looked up.
"""

from __future__ import annotations

from typing import Any

import allure
import pytest
from pytest_bdd import given, scenarios

scenarios("api/azure/security_bot_offboarding_cleanup.feature")

_allure: Any = allure  # allure's decorators are untyped; access via Any to satisfy mypy strict
pytestmark = [
    _allure.label("cloud", "Azure"),
    _allure.epic("Day2 Bots"),
    _allure.feature("Azure Security Bot"),
    _allure.story("Offboarding Cleanup"),
]

_SKIP_REASON = (
    "No synchronous delete-account API exists in this domain — cleanup is event-driven "
    "(EventBridge -> Lambda). Needs boto3 events.put_events publish rights or the real "
    "customeraccount offboarding flow; verified manually for now. See "
    "feature-spec/AZURE_SECURITY_BOT_E2E_STORY.html §6."
)


@given("an Azure subscription has been offboarded")
def _given_offboarded() -> None:
    pytest.skip(reason=_SKIP_REASON)
