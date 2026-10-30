"""Poll with exponential backoff: the replacement for ``sleep`` in tests.

The backend is serverless and eventually consistent (async Lambdas, DynamoDB indexes), so a
record created via the API may take a moment to show up in reads. Never ``sleep``; poll::

    wait_until(lambda: projects_client.get(project_id), lambda r: r.status_code == 200)

``ApiClient`` retries use the same ``backoff_delays`` schedule. The UI side doesn't need this:
Playwright's ``expect`` already retries until its timeout.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from typing import TypeVar

import allure

T = TypeVar("T")


def backoff_delays(initial: float = 0.5, max_delay: float = 5.0) -> Iterator[float]:
    """Endless delays doubling from ``initial`` and capped at ``max_delay``: 0.5, 1, 2, 4, 5, 5…"""
    delay = initial
    while True:
        yield delay
        delay = min(delay * 2, max_delay)


def wait_until(
    fetch: Callable[[], T],
    done: Callable[[T], bool],
    *,
    timeout: float = 30.0,
    description: str = "condition",
) -> T:
    """Call ``fetch`` until ``done(result)`` is true, backing off between polls; return the result.

    Raises ``AssertionError`` with the last result on timeout (fails loudly, never green).
    """
    deadline = time.monotonic() + timeout
    delays = backoff_delays()
    with allure.step(f"Wait up to {timeout:g}s for {description}"):
        while True:
            result = fetch()
            if done(result):
                return result
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AssertionError(
                    f"timed out after {timeout:g}s waiting for {description}; last: {result!r}"
                )
            time.sleep(min(next(delays), remaining))
