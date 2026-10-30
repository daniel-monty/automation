"""Base HTTP client. Tests and step defs NEVER touch raw httpx.

Per-resource client objects (added later, one per API resource) compose or extend this base;
they encapsulate base URL, auth, headers, and serialization. Every call is wrapped as an Allure
step. Auth headers come from the cached `Authenticator` (no per-request login).

Evidence: every call attaches its request and response to the Allure step (secrets masked,
bodies truncated) plus the AWS request id, so a failure can be traced to CloudWatch/X-Ray
logs. Each test's calls share one `X-Correlation-Id`.

Retries live here, so tests never retry by hand:
- connection failures: retried by the httpx transport (all methods; nothing reached the server);
- `429` / `502` / `503` / `504`: idempotent methods only, honouring `Retry-After`, else the
  shared exponential backoff (`polling.backoff_delays`);
- `401`: the token is refreshed once and the request re-sent.
Construct with `authenticated=False` for negative-auth tests (asserting 401/403).
"""

from __future__ import annotations

import json
import time
from types import TracebackType
from typing import Any

import allure
import httpx

from tests.support.auth import Authenticator
from tests.support.polling import backoff_delays

_RETRY_STATUSES = frozenset({429, 502, 503, 504})
_IDEMPOTENT = frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})
_MAX_ATTEMPTS = 3  # first try + 2 retries, backing off 1s then 2s
_MAX_RETRY_AFTER_SECONDS = 10.0
_MASKED_HEADERS = frozenset({"authorization", "x-api-key", "cookie", "set-cookie"})
_MAX_BODY_CHARS = 20_000
# API Gateway / Lambda request ids, in lookup order (CloudWatch, then X-Ray).
_AWS_ID_HEADERS = ("x-amzn-requestid", "x-amz-apigw-id", "x-amzn-trace-id")


class ApiClient:
    """Thin, Allure-wrapped wrapper over a single httpx session."""

    def __init__(
        self,
        base_url: str,
        auth: Authenticator,
        *,
        authenticated: bool = True,
        timeout: float = 30.0,
        correlation_id: str = "",
    ) -> None:
        self._auth = auth
        self._authenticated = authenticated
        self._correlation_id = correlation_id
        self._client = httpx.Client(
            base_url=base_url, timeout=timeout, transport=httpx.HTTPTransport(retries=2)
        )

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
        """Send a request as an Allure step, with the retries described in the module docstring."""
        extra_headers: dict[str, str] = kwargs.pop("headers", {})
        with allure.step(f"{method.upper()} {path}"):
            response = self._send_with_retries(method, path, extra_headers, **kwargs)
            if self._authenticated and response.status_code == httpx.codes.UNAUTHORIZED:
                self._auth.invalidate()
                response = self._send_with_retries(method, path, extra_headers, **kwargs)
            _attach_exchange(response)
            return response

    def _send_with_retries(
        self, method: str, path: str, extra_headers: dict[str, str], **kwargs: Any
    ) -> httpx.Response:
        attempts = _MAX_ATTEMPTS if method.upper() in _IDEMPOTENT else 1
        response = self._send(method, path, extra_headers, **kwargs)
        for attempt, delay in zip(range(1, attempts), backoff_delays(initial=1.0), strict=False):
            if response.status_code not in _RETRY_STATUSES:
                break
            wait = _retry_after(response) or delay
            with allure.step(
                f"Retry {attempt}/{attempts - 1} in {wait:g}s after {response.status_code}"
            ):
                time.sleep(wait)
            response = self._send(method, path, extra_headers, **kwargs)
        return response

    def _send(
        self, method: str, path: str, extra_headers: dict[str, str], **kwargs: Any
    ) -> httpx.Response:
        # Auth headers first so an explicit header (e.g. a bad token in a negative test) wins.
        headers = {"X-Correlation-Id": self._correlation_id} if self._correlation_id else {}
        if self._authenticated:
            headers.update(self._auth.headers())
        headers.update(extra_headers)
        return self._client.request(method, path, headers=headers, **kwargs)


def _retry_after(response: httpx.Response) -> float | None:
    """The server's numeric ``Retry-After`` in seconds (capped), or ``None`` to use backoff."""
    value = response.headers.get("Retry-After", "")
    return min(float(value), _MAX_RETRY_AFTER_SECONDS) if value.isdigit() else None


def _attach_exchange(response: httpx.Response) -> None:
    """Attach the request/response pair to the current Allure step (secrets masked)."""
    request = response.request
    aws_ids = {h: response.headers[h] for h in _AWS_ID_HEADERS if h in response.headers}
    exchange = {
        "request": {
            "method": request.method,
            "url": str(request.url),
            "headers": _masked(request.headers),
            "body": _truncated(request.content.decode("utf-8", "replace")),
        },
        "response": {
            "status": response.status_code,
            "elapsed_ms": round(response.elapsed.total_seconds() * 1000),
            "aws_request_ids": aws_ids,
            "headers": _masked(response.headers),
            "body": _truncated(response.text),
        },
    }
    allure.attach(
        json.dumps(exchange, indent=2),
        name=f"{request.method} {request.url.path} -> {response.status_code}",
        attachment_type=allure.attachment_type.JSON,
    )


def _masked(headers: httpx.Headers) -> dict[str, str]:
    return {k: "***" if k.lower() in _MASKED_HEADERS else v for k, v in headers.items()}


def _truncated(text: str) -> str:
    if len(text) <= _MAX_BODY_CHARS:
        return text
    return f"{text[:_MAX_BODY_CHARS]}... [truncated {len(text) - _MAX_BODY_CHARS} chars]"
