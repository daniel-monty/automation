"""Client object for the assessment workloads resource.

Wraps ``GET /assessment/api/v1/workloads`` with typed query parameters.
Never instantiated by test code directly — exposed through the
``workloads_client`` / ``unauthenticated_workloads_client`` pytest fixtures.
"""

from __future__ import annotations

import httpx

from tests.support.api_client import ApiClient


class WorkloadsClient:
    """Single-resource client for ``/assessment/api/v1/workloads``."""

    _BASE = "/assessment/api/v1/workloads"

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list_workloads(
        self,
        *,
        provider: str = "Azure",
        assessment_type: str = "azure_wafr",
        status: str | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> httpx.Response:
        """List workloads, optionally filtered by provider, assessment type, and status.

        Query parameters use PascalCase to match the API convention.
        """
        params: dict[str, str | int] = {
            "Provider": provider,
            "AssessmentType": assessment_type,
            "Offset": offset,
            "Limit": limit,
        }
        if status is not None:
            params["Status"] = status
        return self._client.request("GET", self._BASE, params=params)
