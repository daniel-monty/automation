"""Contract / fuzz E2E (schemathesis), driven from a live OpenAPI spec.

Runs in the NIGHTLY suite only (mark: `contract`). Skeleton — no tests yet.
Wire against `E2E_OPENAPI_SPEC` once the richer spec is provided. schemathesis 4.x
shape (enable when the spec lands)::

    import schemathesis
    from tests.support.auth import Authenticator
    from tests.support.config import get_settings

    settings = get_settings()
    schema = schemathesis.openapi.from_url(settings.openapi_spec)

    @schema.parametrize()
    def test_api_contract(case: schemathesis.Case) -> None:
        headers = Authenticator(settings).headers()
        case.call_and_validate(headers=headers)
"""

from __future__ import annotations
