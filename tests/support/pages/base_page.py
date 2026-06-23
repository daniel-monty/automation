"""Base for Playwright page/component objects (the UI domain layer).

Role-based locators (`get_by_role`, `get_by_label`) live ONLY here — never in step
defs or tests. Keep page objects small and composable; no god-objects.

Skeleton: base only. Concrete pages are added when the first UI journey is authored.
"""

from __future__ import annotations

from playwright.sync_api import Page


class BasePage:
    """Common page-object behaviour."""

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

    def goto(self, path: str = "") -> None:
        self.page.goto(f"{self.base_url}{path}")
