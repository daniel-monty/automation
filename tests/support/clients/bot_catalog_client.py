"""Client object for the Azure bot catalog resource.

Wraps ``GET /bots/azure/api/v1/bot-catalog`` — a read-only, unfiltered listing (no
query/path params, no request body). Never instantiated by test code directly — exposed
through the ``bot_catalog_client`` / ``unauthenticated_bot_catalog_client`` pytest fixtures.
"""

from __future__ import annotations

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
