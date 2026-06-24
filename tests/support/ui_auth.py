"""Build a Playwright `storage_state` that starts the app already-authenticated.

Arrange-via-API applied to login: mint tokens via /auth/signin, then inject them into browser
localStorage the way the app reads them, so UI tests skip the login form. Exactly one UI
test (the login journey itself) should log in through the form with a fresh, unauthenticated
context; every other UI test reuses this seeded state.

⚠️ VERIFY against the deployed app: this assumes AWS Amplify's default localStorage key
scheme (`CognitoIdentityServiceProvider.<clientId>.<user>.<token>`). If the app stores its
session differently (custom keys, cookies, a different auth library), adjust the keys here.
Confirm once dev1 UI access is available.
"""

from __future__ import annotations

import base64
import json
from typing import Any

from tests.support.auth import Authenticator
from tests.support.config import Settings


def _claims(token: str) -> dict[str, Any]:
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    claims: dict[str, Any] = json.loads(base64.urlsafe_b64decode(payload))
    return claims


def build_storage_state(settings: Settings, auth: Authenticator) -> dict[str, Any]:
    """Return a Playwright storage_state dict pre-seeded with the test user's Cognito session."""
    id_token = auth.id_token()
    claims = _claims(id_token)
    user = str(claims.get("cognito:username") or claims["sub"])
    client_id = str(claims["aud"])  # the app client id, read from the token (no config needed)
    prefix = f"CognitoIdentityServiceProvider.{client_id}"
    local_storage = [
        {"name": f"{prefix}.LastAuthUser", "value": user},
        {"name": f"{prefix}.{user}.idToken", "value": id_token},
        {"name": f"{prefix}.{user}.accessToken", "value": auth.access_token()},
        {"name": f"{prefix}.{user}.refreshToken", "value": auth.refresh_token()},
        {"name": f"{prefix}.{user}.clockDrift", "value": "0"},
    ]
    return {
        "cookies": [],
        "origins": [{"origin": settings.ui_base_url, "localStorage": local_storage}],
    }
