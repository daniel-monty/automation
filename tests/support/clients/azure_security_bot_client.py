"""Client object for the Azure security bot resource.

Wraps ``/bots/azure/api/v1/security*`` — subscriptions, activate/deactivate, findings, and
finding suppression. Never instantiated by test code directly — exposed through the
``azure_security_bot_client`` / ``unauthenticated_azure_security_bot_client`` pytest fixtures.

Discovery (``find_connected_target`` / ``list_connected_targets``) reads the real, already
connected Azure subscription(s) in the target environment rather than requiring hardcoded test
data — connecting a subscription is out of scope for this domain (see the story doc §2).
"""

from __future__ import annotations

from typing import Any, cast

import httpx

from tests.support.api_client import ApiClient
from tests.support.models.azure_security_bot import SecurityBotTarget


class AzureSecurityBotClient:
    """Single-resource client for ``/bots/azure/api/v1/security``."""

    _SUBSCRIPTIONS = "/bots/azure/api/v1/security/subscriptions"
    _CONFIG = "/bots/azure/api/v1/security"
    _FINDINGS = "/bots/azure/api/v1/security/findings"
    _SUPPRESS = "/bots/azure/api/v1/security/findings/suppress"

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list_subscriptions(self) -> httpx.Response:
        """List Azure subscriptions known to the security bot, with connection status."""
        return self._client.request("GET", self._SUBSCRIPTIONS)

    def list_connected_targets(self) -> list[SecurityBotTarget]:
        """Discover connected subscriptions with >=1 resource group, as activation targets.

        Fails loudly if the subscriptions envelope is not the confirmed shape (never returns
        an empty list to mask a broken response — that is distinct from a legitimate empty
        *result*, which callers handle explicitly via ``find_connected_target``).
        """
        body: Any = self.list_subscriptions().json()
        assert isinstance(body, dict), f"expected a JSON object, got {type(body).__name__}"
        subscriptions = body.get("Subscriptions")
        assert isinstance(subscriptions, list), (
            f"expected a 'Subscriptions' list in the response, got keys {list(body.keys())}"
        )
        targets = []
        for sub in cast(list[dict[str, Any]], subscriptions):
            if sub.get("ConnectionError"):
                continue
            resource_groups = [
                rg["ResourceGroupName"]
                for rg in sub.get("ResourceGroups", [])
                if rg.get("ResourceGroupName")
            ]
            if not resource_groups:
                continue
            targets.append(
                SecurityBotTarget(
                    SubscriptionId=sub["SubscriptionId"],
                    SubscriptionName=sub.get("SubscriptionName"),
                    ResourceGroups=resource_groups,
                )
            )
        return targets

    def find_connected_target(self) -> SecurityBotTarget | None:
        """Return the first connected subscription with resource groups, or None."""
        targets = self.list_connected_targets()
        return targets[0] if targets else None

    def activate(self, targets: list[SecurityBotTarget]) -> httpx.Response:
        """Activate the bot for the given targets (POST .../security)."""
        return self._client.request(
            "POST",
            self._CONFIG,
            json={"Targets": [t.model_dump(exclude_none=True) for t in targets]},
        )

    def deactivate(
        self, scope: str, targets: list[SecurityBotTarget] | None = None
    ) -> httpx.Response:
        """Deactivate the bot (DELETE .../security). Body is required even on DELETE."""
        return self._client.request(
            "DELETE",
            self._CONFIG,
            json={
                "DeactivationScope": scope,
                "Targets": [t.model_dump(exclude_none=True) for t in (targets or [])],
            },
        )

    def list_findings(
        self,
        *,
        page: int = 1,
        page_size: int = 25,
        sort_by: str = "risk_level_numeric",
        sort_order: str = "asc",
        status: str | None = "Failed",
    ) -> httpx.Response:
        """List security findings, paginated and sorted (GET .../security/findings)."""
        params: dict[str, str | int] = {
            "page": page,
            "pageSize": page_size,
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }
        if status is not None:
            params["status"] = status
        return self._client.request("GET", self._FINDINGS, params=params)

    def suppress_findings(self, finding_ids: list[str]) -> httpx.Response:
        """Suppress one or more findings by id (PATCH .../security/findings/suppress)."""
        return self._client.request("PATCH", self._SUPPRESS, json={"FindingIds": finding_ids})
