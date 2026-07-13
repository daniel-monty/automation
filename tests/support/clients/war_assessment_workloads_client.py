"""Client object for the AWS Well-Architected Review (war-assessment) workloads resource.

Wraps ``GET /war-assessment/workloads`` with typed query parameters. Never instantiated by
test code directly — exposed through the ``war_assessment_workloads_client`` /
``unauthenticated_war_assessment_workloads_client`` pytest fixtures.
"""

from __future__ import annotations

import json

import httpx

from tests.support.api_client import ApiClient


class WarAssessmentWorkloadsClient:
    """Single-resource client for ``/war-assessment/workloads``."""

    _BASE = "/war-assessment/workloads"

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def search_workloads(
        self,
        *,
        keyword: str | None = None,
        ftr_request: bool | None = None,
        status: str | None = None,
        limit: int = 10,
        page_number: int = 1,
    ) -> httpx.Response:
        """Search workloads by keyword/status/FTRRequest, with pagination.

        The API expects the filters bundled as a single JSON-encoded ``Filters`` query
        parameter (e.g. ``{"Keyword": "A", "FTRRequest": false, "Status": "PENDING"}``).
        """
        filters: dict[str, str | bool] = {}
        if keyword is not None:
            filters["Keyword"] = keyword
        if ftr_request is not None:
            filters["FTRRequest"] = ftr_request
        if status is not None:
            filters["Status"] = status

        params: dict[str, str | int] = {
            "Limit": limit,
            "PageNumber": page_number,
        }
        if filters:
            params["Filters"] = json.dumps(filters)
        return self._client.request("GET", self._BASE, params=params)
