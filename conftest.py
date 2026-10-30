"""Root fixtures wiring the support layer into pytest.

Auth is arranged once per session (cached + refreshing token provider). The `api_client`
fixture is authenticated; `unauthenticated_api_client` is for negative-auth tests;
`api_client_as("read_only")` signs in as another configured user (`E2E_TEST_USERS`). UI tests
start pre-authenticated via an injected Playwright `storage_state` (arrange-via-API login) —
except scenarios tagged ``@logged_out`` (the login journey), which get a fresh context.

Failure evidence: API calls attach their request/response (see ApiClient); a failed UI test
attaches a screenshot + URL, and Playwright keeps its trace under ``test-results/``.
"""

from __future__ import annotations

import functools
import os
from collections.abc import Callable, Generator, Iterator
from pathlib import Path
from typing import Any
from uuid import uuid4

import allure
import pytest
from playwright.sync_api import Page
from tests.support.api_client import ApiClient
from tests.support.auth import Authenticator
from tests.support.config import Settings, get_settings
from tests.support.ui_auth import build_storage_state

_PAGE = pytest.StashKey[Page]()


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Derive Allure ``layer`` + ``severity`` labels from the tag taxonomy (drives the
    Testing pyramid and Severity charts). Authors keep tagging scenarios as usual.

    - ``layer = E2E`` on every test: this repo is E2E only. The pyramid's unit and integration
      layers come from the platform (pytest) and UI (Jest) repos' results, labelled there.
    - ``severity``: ``@smoke`` / ``@critical`` -> ``critical``; everything else -> ``normal``.
    """
    _allure: Any = allure  # allure decorators are untyped; access via Any for mypy strict
    for item in items:
        marker_names = {marker.name for marker in item.iter_markers()}
        item.add_marker(_allure.label("layer", "E2E"))
        is_gate = bool({"smoke", "critical"} & marker_names)
        severity = _allure.severity_level.CRITICAL if is_gate else _allure.severity_level.NORMAL
        item.add_marker(_allure.severity(severity))


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    """On a failed UI test, attach a full-page screenshot and the URL while the page is open."""
    report = yield
    page = item.stash.get(_PAGE, None)
    if report.when == "call" and report.failed and page is not None:
        allure.attach(
            page.screenshot(full_page=True),
            name="screenshot on failure",
            attachment_type=allure.attachment_type.PNG,
        )
        allure.attach(page.url, name="page url", attachment_type=allure.attachment_type.URI_LIST)
    return report


def pytest_sessionfinish(session: pytest.Session) -> None:
    """Write ``environment.properties`` so the report shows which env/commit produced it."""
    results = session.config.getoption("allure_report_dir", None)
    if not results or hasattr(session.config, "workerinput"):  # xdist workers: controller only
        return
    settings = get_settings()
    env = {
        "ENV": settings.env,
        "API_BASE_URL": settings.api_base_url,
        "UI_BASE_URL": settings.ui_base_url,
        "COMMIT": os.environ.get("GITHUB_SHA", "local"),
    }
    path = Path(results) / "environment.properties"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{k}={v}\n" for k, v in env.items()), encoding="utf-8")


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def authenticator(settings: Settings) -> Authenticator:
    return Authenticator(settings)


@pytest.fixture(scope="session")
def authenticator_for(settings: Settings) -> Callable[[str], Authenticator]:
    """Session-cached Authenticator per extra user named in ``E2E_TEST_USERS``."""

    @functools.cache
    def get(user: str) -> Authenticator:
        if user not in settings.test_users:
            known = ", ".join(settings.test_users) or "none"
            pytest.fail(f"test user {user!r} is not in E2E_TEST_USERS (configured: {known})")
        return Authenticator(settings, settings.test_users[user])

    return get


@pytest.fixture
def correlation_id() -> str:
    """One id per test, sent as ``X-Correlation-Id`` on every API call it makes."""
    return uuid4().hex


@pytest.fixture
def api_client(
    settings: Settings, authenticator: Authenticator, correlation_id: str
) -> Iterator[ApiClient]:
    """Per-test authenticated API client (tests never construct raw httpx)."""
    with ApiClient(settings.api_base_url, authenticator, correlation_id=correlation_id) as client:
        yield client


@pytest.fixture
def unauthenticated_api_client(
    settings: Settings, authenticator: Authenticator, correlation_id: str
) -> Iterator[ApiClient]:
    """API client with NO auth headers — for asserting 401/403 rejection."""
    with ApiClient(
        settings.api_base_url, authenticator, authenticated=False, correlation_id=correlation_id
    ) as client:
        yield client


@pytest.fixture
def api_client_as(
    settings: Settings,
    authenticator_for: Callable[[str], Authenticator],
    correlation_id: str,
) -> Iterator[Callable[[str], ApiClient]]:
    """Factory for API clients signed in as another user: ``api_client_as("read_only")``.

    For permission and tenant-isolation tests. Users come from ``E2E_TEST_USERS``; an unknown
    name fails the test (never silently skipped).
    """
    clients: list[ApiClient] = []

    def make(user: str) -> ApiClient:
        client = ApiClient(
            settings.api_base_url, authenticator_for(user), correlation_id=correlation_id
        )
        clients.append(client)
        return client

    yield make
    for client in clients:
        client.close()


@pytest.fixture(scope="session")
def ui_storage_state(settings: Settings, authenticator: Authenticator) -> dict[str, Any]:
    """Playwright storage_state with the app pre-authenticated (arrange-via-API login)."""
    return build_storage_state(settings, authenticator)


@pytest.fixture
def browser_context_args(
    browser_context_args: dict[str, Any], request: pytest.FixtureRequest
) -> dict[str, Any]:
    """Inject the seeded auth state into every UI browser context.

    Overrides pytest-playwright's fixture. ``@logged_out`` scenarios skip it (and the API
    sign-in behind it) so they exercise the real login form.
    """
    if request.node.get_closest_marker("logged_out"):
        return browser_context_args
    return {**browser_context_args, "storage_state": request.getfixturevalue("ui_storage_state")}


@pytest.fixture
def page(page: Page, request: pytest.FixtureRequest) -> Page:
    """pytest-playwright's page, registered so a failure can attach a screenshot of it."""
    request.node.stash[_PAGE] = page
    return page
