"""Contract / fuzz E2E: schemathesis generates requests from the OpenAPI spec and checks every
response against it. Nightly only (``@contract``). Read-only operations only: fuzzing writes
would litter the shared dev1 environment.

Reported to Allure via JUnit XML (nightly workflow), since allure-pytest-bdd only reports
Gherkin scenarios. Run locally with ``--junitxml=allure-results/contract-junit.xml`` to see it
in the report.
"""

from __future__ import annotations

from typing import Any

import pytest
import schemathesis

from tests.support.auth import Authenticator
from tests.support.config import get_settings

pytestmark = pytest.mark.contract

settings = get_settings()
if not settings.openapi_spec:
    pytest.skip("E2E_OPENAPI_SPEC is not set", allow_module_level=True)

_load = (
    schemathesis.openapi.from_url
    if settings.openapi_spec.startswith(("http://", "https://"))
    else schemathesis.openapi.from_path
)
schema = _load(settings.openapi_spec).include(method=["GET", "HEAD", "OPTIONS"])
_auth = Authenticator(settings)


@schema.parametrize()
def test_api_contract(case: schemathesis.Case[Any]) -> None:
    case.call_and_validate(base_url=settings.api_base_url, headers=_auth.headers())
