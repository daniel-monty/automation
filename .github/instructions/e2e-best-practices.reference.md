# E2E Authoring Reference — Templates

Copy-paste templates for every layer. They match the support layer in `tests/support/`
(`ApiClient`, `BasePage`, `ModelFactory`, `assert_status`). All templates are written to pass
`ruff` + `mypy --strict`. Replace `Resource`/`resource` with the real resource name.

> This file is loaded on demand by the `/add-*` prompts. The always-on rules live in
> [e2e-best-practices.instructions.md](e2e-best-practices.instructions.md).

---

## 1. Pydantic model (`tests/support/models/resource.py`)

```python
from __future__ import annotations

from pydantic import BaseModel


class Resource(BaseModel):
    name: str
    description: str | None = None
```

## 2. Factory (`tests/support/factories.py`)

```python
from polyfactory.factories.pydantic_factory import ModelFactory

from tests.support.models.resource import Resource


class ResourceFactory(ModelFactory[Resource]):
    __model__ = Resource
```

## 3. API client object (`tests/support/clients/resource_client.py`)

One client per resource. Encapsulates paths + serialization. Never used by tests directly
except through fixtures. Inherits the Allure-wrapped `ApiClient`.

```python
from __future__ import annotations

import httpx

from tests.support.api_client import ApiClient
from tests.support.models.resource import Resource


class ResourceClient:
    _BASE = "/day2api/api/v1/resource"

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def create(self, resource: Resource) -> httpx.Response:
        return self._client.request("POST", self._BASE, json=resource.model_dump())

    def get(self, resource_id: str) -> httpx.Response:
        return self._client.request("GET", f"{self._BASE}/{resource_id}")

    def delete(self, resource_id: str) -> httpx.Response:
        return self._client.request("DELETE", f"{self._BASE}/{resource_id}")
```

## 4. Domain assertion (`tests/support/assertions.py`)

```python
import allure
import httpx


@allure.step("Resource '{name}' is present in the listing")
def assert_resource_listed(response: httpx.Response, name: str) -> None:
    names = [item["name"] for item in response.json().get("items", [])]
    assert name in names, f"'{name}' not found in {names}"
```

## 5. API feature (`tests/features/api/<azure|aws>/resource_lifecycle.feature`)

Declarative. No mechanics. Tags drive run selection + Allure grouping. Pick the cloud
subdirectory (`azure` or `aws`) matching the journey — never mix providers in one file.

```gherkin
@api @azure @regression
Feature: Resource lifecycle
  As a subscribed user
  I want to manage resources via the API
  So that I can automate my cloud operations

  Background:
    Given I am an authenticated subscribed user

  @smoke @critical
  Scenario: Create and retrieve a resource
    When I create a resource named "billing-prod"
    Then the resource "billing-prod" can be retrieved

  Scenario: Creating a resource without a name is rejected
    When I create a resource with no name
    Then the request is rejected as invalid
```

## 6. API step defs (`tests/step_defs/api/<azure|aws>/test_resource_lifecycle.py`)

Thin glue: orchestrate the domain layer; no logic/HTTP/asserts of your own beyond calling
domain assertions. `pytest-bdd` binds the feature here. Mirror the same `azure`/`aws`
subdirectory as the feature file.

```python
from __future__ import annotations

from typing import Any

import allure
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.support.api_client import ApiClient
from tests.support.assertions import assert_status
from tests.support.clients.resource_client import ResourceClient
from tests.support.factories import ResourceFactory

scenarios("api/azure/resource_lifecycle.feature")

# Allure grouping — see "Allure grouping" section below for why pytestmark (not
# allure.dynamic.*) is required.
_allure: Any = allure
pytestmark = [
    _allure.label("cloud", "Azure"),
    _allure.epic("Resources"),
    _allure.feature("Resource Lifecycle"),
    _allure.story("Create and retrieve"),
]


@pytest.fixture
def resource_client(api_client: ApiClient) -> ResourceClient:
    return ResourceClient(api_client)


@pytest.fixture
def context() -> dict[str, object]:
    return {}


@given("I am an authenticated subscribed user")
def _authenticated() -> None:
    """Auth is provided by the api_client fixture (login via /auth/signin)."""


@when(parsers.parse('I create a resource named "{name}"'))
def _create_named(resource_client: ResourceClient, context: dict[str, object], name: str) -> None:
    resource = ResourceFactory.build(name=name)
    context["response"] = resource_client.create(resource)


@when("I create a resource with no name")
def _create_invalid(resource_client: ResourceClient, context: dict[str, object]) -> None:
    context["response"] = resource_client._client.request(
        "POST", ResourceClient._BASE, json={}
    )


@then(parsers.parse('the resource "{name}" can be retrieved'))
def _can_retrieve(resource_client: ResourceClient, name: str) -> None:
    assert_status(resource_client.get(name), 200)


@then("the request is rejected as invalid")
def _rejected(context: dict[str, object]) -> None:
    assert_status(context["response"], 400)  # type: ignore[arg-type]
```

## 7. UI page object (`tests/support/pages/resource_page.py`)

Role-based locators live ONLY here. Small and composable.

```python
from __future__ import annotations

from playwright.sync_api import Page, expect

from tests.support.pages.base_page import BasePage


class ResourcePage(BasePage):
    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)
        self.heading = page.get_by_role("heading", name="Resources")

    def open(self) -> None:
        self.goto("/resources")

    def expect_loaded(self) -> None:
        expect(self.heading).to_be_visible()
```

## 8. UI feature (`tests/features/ui/<azure|aws>/resource_dashboard.feature`)

```gherkin
@ui @azure @critical
Feature: Resource dashboard renders real data

  @smoke
  Scenario: Subscribed user sees their seeded resources
    Given a resource "billing-prod" exists for me
    When I open the resources dashboard
    Then the dashboard structure matches the expected layout
```

## 9. UI step defs (`tests/step_defs/ui/<azure|aws>/test_resource_dashboard.py`)

State is **seeded via the API** (arrange-via-API); the browser only drives the user journey.
Structural assertion uses an **ARIA snapshot**, not brittle CSS. Mirror the same `azure`/`aws`
subdirectory as the feature file, and set the `cloud` Allure label as in §6.

```python
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect
from pytest_bdd import given, parsers, scenarios, then, when

from tests.support.api_client import ApiClient
from tests.support.clients.resource_client import ResourceClient
from tests.support.config import Settings
from tests.support.factories import ResourceFactory
from tests.support.pages.resource_page import ResourcePage

scenarios("ui/azure/resource_dashboard.feature")


@given(parsers.parse('a resource "{name}" exists for me'))
def _seed_via_api(api_client: ApiClient, name: str) -> None:
    ResourceClient(api_client).create(ResourceFactory.build(name=name))


@pytest.fixture
def resource_page(page: Page, settings: Settings) -> ResourcePage:
    return ResourcePage(page, settings.ui_base_url)


@when("I open the resources dashboard")
def _open(resource_page: ResourcePage) -> None:
    resource_page.open()
    resource_page.expect_loaded()


@then("the dashboard structure matches the expected layout")
def _aria_snapshot(page: Page) -> None:
    expect(page.get_by_role("main")).to_match_aria_snapshot(
        """
        - heading "Resources"
        - list
        """
    )
```

## 10. Contract test (`tests/contract/test_contract.py`)

schemathesis 4.x, driven from the live spec, authenticated. Marked `@contract` (nightly).

```python
from __future__ import annotations

import pytest
import schemathesis

from tests.support.auth import Authenticator
from tests.support.config import get_settings

settings = get_settings()
schema = schemathesis.openapi.from_url(settings.openapi_spec)


@pytest.mark.contract
@schema.parametrize()
def test_api_contract(case: schemathesis.Case) -> None:
    case.call_and_validate(headers=Authenticator(settings).headers())
```

---

## Allure grouping (stakeholder-readable)

`scenarios(...)` auto-generates the test functions, so you **cannot** decorate them, and
**`allure.dynamic.*` raises under `allure-pytest-bdd` at fixture setup** (`AttributeError:
'NoneType' object has no attribute 'labels'`). Set epic/feature/story with module-level
`pytestmark`:

```python
from typing import Any

import allure

# allure's decorators are untyped — alias via Any to satisfy mypy strict.
_allure: Any = allure
pytestmark = [
    _allure.label("cloud", "Azure"),  # or "AWS" — matches the feature's azure/aws subdir
    _allure.epic("Assessments"),
    _allure.feature("WAFR Workloads"),
    _allure.story("List"),
    _allure.link("https://montycloud.atlassian.net/browse/PRO-1234", name="PRO-1234"),
]
```

The Gherkin `Feature:` name already maps to an Allure feature automatically; the `pytestmark`
labels add the leadership `cloud`/epic/feature/story grouping + the requirement link. The
Allure report (`allure/allurerc.mjs`) groups by `["cloud", "epic", "feature", "story"]`, so the
`cloud` label must be set on every module or scenarios fall into an "Unknown" bucket.
