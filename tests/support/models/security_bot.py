"""Pydantic model for an Azure Security Bot activation target.

Field names are PascalCase to match the API's request/response contract exactly (no aliasing
needed) — see ``BotCatalogClient.activate_security_bot`` /
``BotCatalogClient.first_available_security_target``.
"""

from __future__ import annotations

from pydantic import BaseModel


class SecurityBotTarget(BaseModel):
    """A single Azure subscription + resource-group target for security bot activation."""

    SubscriptionId: str
    SubscriptionName: str
    ResourceGroups: list[str]
