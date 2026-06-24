"""Base HTTP client. Tests and step defs NEVER touch raw httpx.

Per-resource client objects (added later, one per API resource) compose or extend this base;
they encapsulate base URL, auth, headers, retries, and serialization. Every call is wrapped as
an Allure step. Auth headers come from the cached `Authenticator` (no per-request login); on a
`401` the client refreshes the token once and retries. Construct with `authenticated=False` for
negative-auth tests (asserting 401/403).
"""

from __future__ import annotations

from types import TracebackType
from typing import Any

import allure
import httpx

from tests.support.auth import Authenticator


class ApiClient:
    """Thin, Allure-wrapped wrapper over a single httpx session."""

    def __init__(
        self,
        base_url: str,
        auth: Authenticator,
        *,
        authenticated: bool = True,
        timeout: float = 30.0,
    ) -> None:
        self._auth = auth
        self._authenticated = authenticated
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
        """Send a request as an Allure step; refresh+retry once on a 401 when authenticated."""
        extra_headers: dict[str, str] = kwargs.pop("headers", {})
        with allure.step(f"{method.upper()} {path}"):
            response = self._send(method, path, extra_headers, **kwargs)
            if self._authenticated and response.status_code == httpx.codes.UNAUTHORIZED:
                self._auth.invalidate()
                response = self._send(method, path, extra_headers, **kwargs)
            return response

    def _send(
        self, method: str, path: str, extra_headers: dict[str, str], **kwargs: Any
    ) -> httpx.Response:
        # Auth headers first so an explicit header (e.g. a bad token in a negative test) wins.
        if self._authenticated:
            headers = {**self._auth.headers(), **extra_headers}
        else:
            headers = extra_headers
        return self._client.request(method, path, headers=headers, **kwargs)
