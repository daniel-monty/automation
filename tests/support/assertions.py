"""Reusable domain assertions, wrapped as Allure steps so reports read in
business terms. Step defs call these — they never inline raw asserts.

Skeleton: one generic example. Add domain-specific assertions as the suite grows.
"""

from __future__ import annotations

import allure
import httpx


@allure.step("Response status is {expected}")
def assert_status(response: httpx.Response, expected: int) -> None:
    """Assert an HTTP response status, surfacing the body on mismatch."""
    assert response.status_code == expected, (
        f"expected {expected}, got {response.status_code}: {response.text}"
    )
