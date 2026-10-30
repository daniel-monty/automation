"""Authentication for the E2E suite.

Logs in via the platform's HTTP `POST /auth/signin` (the same endpoint the app uses) ONCE per
session, caches the tokens, and renews them via `POST /auth/refresh-token` shortly before expiry
— so the hot path (`headers()`) makes no network calls. Pure `httpx`: needs only the API base URL
and a no-MFA test user's username/password.
"""

from __future__ import annotations

import base64
import json
import time
from typing import Any

import httpx

from tests.support.config import Settings, TestUser

# Renew when fewer than this many seconds remain on the token.
_REFRESH_SKEW_SECONDS = 120


def _jwt_expiry(token: str) -> int:
    """Read the `exp` claim from a JWT without verifying the signature."""
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    claims: dict[str, Any] = json.loads(base64.urlsafe_b64decode(payload))
    return int(claims["exp"])


class Authenticator:
    """Caching token provider backed by the platform's HTTP `/auth/signin` endpoint."""

    def __init__(self, settings: Settings, user: TestUser | None = None) -> None:
        """Sign in as ``user``, or as the default ``E2E_TEST_USERNAME`` user when omitted."""
        self._settings = settings
        self._user = user or TestUser(
            username=settings.test_username, password=settings.test_password
        )
        self._http = httpx.Client(base_url=settings.api_base_url, timeout=30.0)
        self._id_token = ""
        self._access_token = ""
        self._refresh_token = ""
        self._expiry = 0

    # -- public API ---------------------------------------------------------

    def token(self) -> str:
        """Return a valid ID token, logging in or refreshing as needed."""
        if not self._id_token:
            self._login()
        elif time.time() >= self._expiry - _REFRESH_SKEW_SECONDS:
            self._refresh()
        return self._id_token

    def headers(self) -> dict[str, str]:
        """Auth headers for every authenticated request (cached; no network on the hot path)."""
        token = self.token()
        scheme = self._settings.auth_header_scheme
        headers = {"Authorization": f"{scheme} {token}" if scheme else token}
        api_key = self._settings.api_key.get_secret_value()
        if api_key:  # only some APIs require x-api-key; omit when unset
            headers["x-api-key"] = api_key
        return headers

    def invalidate(self) -> None:
        """Force a refresh on the next call — used by the client after a 401."""
        self._expiry = 0

    def id_token(self) -> str:
        self.token()
        return self._id_token

    def access_token(self) -> str:
        self.token()
        return self._access_token

    def refresh_token(self) -> str:
        self.token()
        return self._refresh_token

    # -- internals ----------------------------------------------------------

    def _login(self) -> None:
        response = self._http.post(
            self._settings.auth_signin_path,
            json={
                "Username": self._user.username,
                "Password": self._user.password.get_secret_value(),
            },
        )
        response.raise_for_status()
        self._consume(response.json())

    def _refresh(self) -> None:
        try:
            response = self._http.post(
                self._settings.auth_refresh_path,
                json={"RefreshToken": self._refresh_token},
            )
            response.raise_for_status()
            self._consume(response.json())
        except (httpx.HTTPError, KeyError, RuntimeError):
            self._login()  # any refresh problem -> full re-login

    def _consume(self, body: dict[str, Any]) -> None:
        challenge = body.get("ChallengeName")
        if challenge:
            raise RuntimeError(
                f"/auth/signin returned challenge {challenge!r}; use a plain no-MFA test user "
                "with a permanent password."
            )
        self._id_token = str(body["Token"])
        self._access_token = str(body.get("AccessToken", ""))
        if body.get("RefreshToken"):  # refresh responses may omit it — keep the existing one
            self._refresh_token = str(body["RefreshToken"])
        self._expiry = _jwt_expiry(self._id_token)
