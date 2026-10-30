"""Delete ``e2e-`` test data that crashed or cancelled runs never cleaned up.

Fixture teardown only runs when a test finishes normally, so dev1 slowly collects leftovers.
The nightly workflow runs this after the suite (even on failure)::

    python -m tests.support.sweep

Each creatable resource registers one sweep function in ``SWEEPERS`` (see reference §3). Only
items older than ``MAX_AGE`` are deleted, so data from runs still in progress is left alone.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from tests.support.api_client import ApiClient
from tests.support.auth import Authenticator
from tests.support.config import get_settings

MAX_AGE = timedelta(hours=6)

# (client, cutoff) -> number deleted. Deletes only E2E_PREFIX items created before cutoff.
Sweeper = Callable[[ApiClient, datetime], int]
SWEEPERS: list[Sweeper] = []


def main() -> None:
    settings = get_settings()
    cutoff = datetime.now(UTC) - MAX_AGE
    with ApiClient(settings.api_base_url, Authenticator(settings)) as client:
        for sweeper in SWEEPERS:
            print(f"{sweeper.__module__}.{sweeper.__name__}: deleted {sweeper(client, cutoff)}")
    print(f"sweep done ({len(SWEEPERS)} sweepers, cutoff {cutoff:%Y-%m-%d %H:%M} UTC)")


if __name__ == "__main__":
    main()
