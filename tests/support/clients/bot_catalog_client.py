"""Client object for the Azure bot catalog resource.

Wraps ``GET /bots/azure/api/v1/bot-catalog`` — a read-only, unfiltered listing (no
query/path params, no request body) — plus the Azure security bot's activation lifecycle
(``/bots/azure/api/v1/security[/subscriptions]``), a sibling resource under the same Azure
bots namespace. Never instantiated by test code directly — exposed through the
``bot_catalog_client`` / ``unauthenticated_bot_catalog_client`` pytest fixtures.
"""

from __future__ import annotations

import json
from typing import Any, cast

import httpx

from tests.support.api_client import ApiClient
from tests.support.models.security_bot import SecurityBotTarget


class BotCatalogClient:
    """Single-resource client for ``/bots/azure/api/v1/bot-catalog`` + the security bot."""

    _BASE = "/bots/azure/api/v1/bot-catalog"
    _SECURITY_BASE = "/bots/azure/api/v1/security"
    _SECURITY_BOT_CODE = "AZURE_SECURITY_BOT"

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list_bots(self) -> httpx.Response:
        """List the full Azure bot catalog (no params — full listing)."""
        return self._client.request("GET", self._BASE)

    def list_security_subscriptions(self) -> httpx.Response:
        """List the Azure subscriptions eligible for the security bot (no params)."""
        return self._client.request("GET", f"{self._SECURITY_BASE}/subscriptions")

    def first_available_security_target(self) -> SecurityBotTarget:
        """Return the first eligible subscription, mapped to an activation target.

        The subscriptions listing nests resource groups as objects (``{"ResourceGroupName",
        "IsSelected"}``); the activation body wants a flat list of names — this is where that
        mapping happens, so step defs stay thin.
        """
        subscriptions = self.list_security_subscriptions().json()["Subscriptions"]
        first = subscriptions[0]
        return SecurityBotTarget(
            SubscriptionId=first["SubscriptionId"],
            SubscriptionName=first["SubscriptionName"],
            ResourceGroups=[rg["ResourceGroupName"] for rg in first["ResourceGroups"]],
        )

    def activate_security_bot(self, targets: list[SecurityBotTarget]) -> httpx.Response:
        """Activate the Azure security bot against the given subscription targets."""
        body = {"Targets": [target.model_dump() for target in targets]}
        return self._client.request("POST", self._SECURITY_BASE, json=body)

    def deactivate_security_bot(self) -> httpx.Response:
        """Deactivate the Azure security bot for all subscriptions and resource groups."""
        body = {"DeactivationScope": "all", "Targets": []}
        return self._client.request("DELETE", self._SECURITY_BASE, json=body)

    def current_security_targets(self) -> list[dict[str, Any]]:
        """Return the security bot's currently configured Targets (empty if not configured).

        Used to snapshot state before a test mutates it, so it can be restored afterward —
        the security bot config is a tenant-wide singleton on the shared dev1 environment.
        """
        bots = self.list_bots().json()["Bots"]
        security_bot = next(
            (bot for bot in bots if bot.get("BotCode") == self._SECURITY_BOT_CODE), None
        )
        if security_bot is None:
            return []
        targets = (security_bot.get("Config") or {}).get("Targets") or []
        return cast(list[dict[str, Any]], targets)

    def security_insight_filter_options(self, dimension: str) -> httpx.Response:
        """List the security bot's insight filter options for one dimension (no params).

        ``dimension`` is a URL path segment: ``"resource-groups"``, ``"regions"``, or
        ``"resource-types"``.
        """
        return self._client.request(
            "GET", f"{self._SECURITY_BASE}/insights/filter-options/{dimension}"
        )

    def security_insights_summary(self) -> httpx.Response:
        """Get the security bot's insights summary (findings breakdowns, no query params)."""
        return self._client.request("GET", f"{self._SECURITY_BASE}/insights")

    def security_findings(
        self, *, page: int, page_size: int, severity: list[str], status: list[str]
    ) -> httpx.Response:
        """Query the security bot's findings, filtered by severity and status.

        ``Severity``/``Status`` are separate, JSON-encoded-array query params (confirmed
        against dev1) — unlike ``WarAssessmentWorkloadsClient``, which bundles its filters
        into a single JSON-encoded ``Filters`` param.
        """
        params = {
            "Page": page,
            "PageSize": page_size,
            "Severity": json.dumps(severity),
            "Status": json.dumps(status),
        }
        return self._client.request("GET", f"{self._SECURITY_BASE}/findings", params=params)
