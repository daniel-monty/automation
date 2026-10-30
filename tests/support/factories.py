"""Arrange-via-API data factories, built on Pydantic models.

Every test arranges state through these factories (never by hand), shared by both
API and UI tests. Every generated name goes through ``e2e_name()`` so leftovers from crashed
runs are recognisable and the nightly sweeper (``tests/support/sweep.py``) can delete them.
Add one factory per resource model as the suite grows, e.g.::

    from polyfactory import Use
    from polyfactory.factories.pydantic_factory import ModelFactory
    from tests.support.models.customer_account import CustomerAccount

    class CustomerAccountFactory(ModelFactory[CustomerAccount]):
        __model__ = CustomerAccount
        name = Use(e2e_name)
"""

from __future__ import annotations

from uuid import uuid4

E2E_PREFIX = "e2e-"


def e2e_name() -> str:
    """A unique, recognisable name for test data: ``e2e-<8 hex chars>``."""
    return f"{E2E_PREFIX}{uuid4().hex[:8]}"
