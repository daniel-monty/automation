"""Request models for the Azure security bot resource.

Not built by a Polyfactory factory: a ``SecurityBotTarget`` must reference a real, already
connected Azure subscription (and its real resource groups) discovered via
``GET /bots/azure/api/v1/security/subscriptions`` — random data would never map to a target
the backend recognizes. See ``AzureSecurityBotClient.find_connected_target``.
"""

from __future__ import annotations

from pydantic import BaseModel


class SecurityBotTarget(BaseModel):
    """A subscription (+ in-scope resource groups) for activate/deactivate requests."""

    SubscriptionId: str
    SubscriptionName: str | None = None
    ResourceGroups: list[str] = []
