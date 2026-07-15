"""Client object for the Azure bot catalog resource.

Wraps ``GET /bots/azure/api/v1/bot-catalog`` — a read-only, unfiltered listing (no
query/path params, no request body). Never instantiated by test code directly — exposed
through the ``bot_catalog_client`` / ``unauthenticated_bot_catalog_client`` pytest fixtures.

Also exposes bounded polling helpers for the security bot's async scan-completion signal
(``wait_for_scan``) — the activate call only publishes an event; the actual scan runs on an
ECS task consumed via EventBridge/SQS, so completion must be observed by polling the catalog.
"""

from __future__ import annotations

import time
from typing import Any, cast

import httpx

from tests.support.api_client import ApiClient


class BotCatalogClient:
    """Single-resource client for ``/bots/azure/api/v1/bot-catalog``."""

    _BASE = "/bots/azure/api/v1/bot-catalog"

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list_bots(self) -> httpx.Response:
        """List the full Azure bot catalog (no params — full listing)."""
        return self._client.request("GET", self._BASE)

    def find_security_bot_config(self, subscription_id: str) -> dict[str, Any] | None:
        """Return the Config of the catalog bot whose Targets include *subscription_id*."""
        body: Any = self.list_bots().json()
        bots = cast(list[dict[str, Any]], body.get("Bots", []))
        for bot in bots:
            config = bot.get("Config")
            if not config:
                continue
            targets = cast(list[dict[str, Any]], config.get("Targets", []))
            if any(t.get("SubscriptionId") == subscription_id for t in targets):
                return cast(dict[str, Any], config)
        return None

    def has_completed_scan(self, subscription_id: str) -> bool:
        """Check (single GET, no polling) whether a scan has already completed.

        Only checks LastScanAt is non-null — a stale scan from long before this test run
        satisfies this. Use for preconditions where any prior scan is acceptable (e.g. the
        findings journey). To confirm a *new* scan triggered by *this* activation, use
        ``wait_for_scan(subscription_id, since=...)`` instead.
        """
        config = self.find_security_bot_config(subscription_id)
        return bool(config and config.get("Status") == "ACTIVE" and config.get("LastScanAt"))

    def get_last_scan_at(self, subscription_id: str) -> str | None:
        """Return the current LastScanAt timestamp for the subscription, or None."""
        config = self.find_security_bot_config(subscription_id)
        return config.get("LastScanAt") if config else None

    def wait_for_scan(
        self,
        subscription_id: str,
        *,
        since: str | None = None,
        max_attempts: int = 6,
        initial_delay: float = 2.0,
        backoff: float = 2.0,
    ) -> bool:
        """Poll the catalog with exponential backoff until a scan completes.

        Bounded, purposeful polling for a genuinely async/event-driven backend signal (not a
        flaky-test workaround) — mirrors the story doc's recommended retry/backoff pattern.
        Returns False (does not raise) if the scan hasn't completed within the attempt budget,
        so the caller can assert/skip with a clear message.

        Pass ``since`` (the LastScanAt observed *before* triggering activation) to require a
        *fresh* scan — otherwise a subscription that was already active with an old completed
        scan would pass on the very first poll without a new scan ever running.
        """

        def _completed() -> bool:
            config = self.find_security_bot_config(subscription_id)
            last_scan_at = config.get("LastScanAt") if config else None
            return bool(
                config
                and config.get("Status") == "ACTIVE"
                and last_scan_at
                and last_scan_at != since
            )

        delay = initial_delay
        for _ in range(max_attempts):
            if _completed():
                return True
            time.sleep(delay)
            delay *= backoff
        return _completed()

    def is_deactivated(self, subscription_id: str) -> bool:
        """Check whether the given subscription is no longer an active bot target."""
        config = self.find_security_bot_config(subscription_id)
        return config is None or config.get("Status") in ("NOT_CONFIGURED", "INACTIVE")

    def is_active(self, subscription_id: str) -> bool:
        """Check (single GET, no polling) whether the subscription is an ACTIVE bot target."""
        config = self.find_security_bot_config(subscription_id)
        return bool(config and config.get("Status") == "ACTIVE")

    def wait_for_deactivation(
        self,
        subscription_id: str,
        *,
        max_attempts: int = 6,
        initial_delay: float = 1.0,
        backoff: float = 2.0,
    ) -> bool:
        """Poll the catalog with backoff until the subscription is confirmed deactivated."""
        delay = initial_delay
        for _ in range(max_attempts):
            if self.is_deactivated(subscription_id):
                return True
            time.sleep(delay)
            delay *= backoff
        return self.is_deactivated(subscription_id)
