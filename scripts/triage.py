"""AI failure triage — additive tooling, OFF the PR-gating path.

Allure 3's known-issues list handles known/blocked classification natively. This
script targets only NEW, UNKNOWN failures: it reads Allure results, drops anything
already in the known-issues list, and (when an LLM is configured) classifies each
remaining failure as `regression | flaky | env | test-bug`, dedupes clusters, and
drafts a root-cause summary to post to the PR / Confluence.

Skeleton: result parsing + known-issue filtering are stubbed; the LLM call is a TODO.
The LLM provider is configurable via env and entirely optional — determinism gates,
AI only accelerates triage.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tests.support.config import get_settings


def load_results(allure_results: Path) -> list[dict[str, object]]:
    """Load failed/broken results from an Allure results directory."""
    failures: list[dict[str, object]] = []
    for result_file in allure_results.glob("*-result.json"):
        data = json.loads(result_file.read_text())
        if data.get("status") in {"failed", "broken"}:
            failures.append(data)
    return failures


def load_known_issues(path: Path) -> set[str]:
    """Load known-issue identifiers so they are excluded from triage."""
    if not path.exists():
        return set()
    issues = json.loads(path.read_text())
    return {str(issue.get("id")) for issue in issues if "id" in issue}


def triage(failures: list[dict[str, object]], known: set[str]) -> None:
    """Classify only new, unknown failures. LLM call is a TODO (provider via env)."""
    settings = get_settings()
    new_failures = [f for f in failures if str(f.get("historyId")) not in known]
    provider = settings.llm_provider or "none"
    print(f"{len(new_failures)} new/unknown failure(s) to triage (provider: {provider}).")
    # TODO: when settings.llm_provider is set, send each new failure's Allure result +
    # Playwright trace + console logs to the LLM, classify, dedupe, draft a summary.


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allure-results", type=Path, default=Path("allure-results"))
    parser.add_argument("--known-issues", type=Path, default=Path("allure/known-issues.json"))
    args = parser.parse_args()

    failures = load_results(args.allure_results)
    known = load_known_issues(args.known_issues)
    triage(failures, known)


if __name__ == "__main__":
    main()
