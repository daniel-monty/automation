"""Base HTTP client. Tests and step defs NEVER touch raw httpx.

Per-resource client objects (added later, one per API resource) compose or extend
this base; they encapsulate base URL, auth, headers, retries, and serialization.
Every call is wrapped as an Allure step so the report reads in business terms.
"""

from __future__ import annotations

from types import TracebackType
from typing import Any

import allure
import httpx

from tests.support.auth import Authenticator


class ApiClient:
    """Thin, Allure-wrapped wrapper over a single httpx session."""

    def __init__(self, base_url: str, auth: Authenticator, timeout: float = 30.0) -> None:
        self._auth = auth
        self._client = httpx.Client(base_url=base_url, timeout=timeout)

    def __enter__(self) -> ApiClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """Send an authenticated request, recorded as an Allure step."""
        headers = {**self._auth.headers(), **kwargs.pop("headers", {})}
        with allure.step(f"{method.upper()} {path}"):
            return self._client.request(method, path, headers=headers, **kwargs)
