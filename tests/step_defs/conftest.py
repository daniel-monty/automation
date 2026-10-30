"""Steps shared by API and UI step defs.

pytest-bdd finds steps defined in a conftest, so a step used by several features lives here once.
"""

from __future__ import annotations

from pytest_bdd import given


@given("I am an authenticated user")
def _authenticated() -> None:
    """Auth is supplied by the api_client fixture (login via /auth/signin -> ID token)."""
