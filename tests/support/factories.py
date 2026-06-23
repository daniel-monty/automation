"""Arrange-via-API data factories, built on Pydantic models.

Every test arranges state through these factories (never by hand), shared by both
API and UI tests. Add one factory per resource model as the suite grows, e.g.::

    from polyfactory.factories.pydantic_factory import ModelFactory
    from tests.support.models import CustomerAccount

    class CustomerAccountFactory(ModelFactory[CustomerAccount]):
        __model__ = CustomerAccount

Skeleton: no factories yet — they are added alongside the resource models they build.
"""

from __future__ import annotations

from polyfactory.factories.pydantic_factory import ModelFactory

__all__ = ["ModelFactory"]
