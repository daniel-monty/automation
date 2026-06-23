# AGENTS.md

Source of truth for AI agents (GitHub Copilot, Claude, etc.) working in this repo.
Keep changes here small and stable. Task-specific recipes live in `.github/prompts/`;
full code templates live in `.github/instructions/e2e-best-practices.reference.md`.

## Project Overview

Standalone **end-to-end (E2E) BDD automation suite** for the MontyCloud platform.
**API-first, UI-supported.** One language (Python), one runner (**pytest + pytest-bdd**),
one combined report (**Allure 3**). E2E / system-level only — **no unit tests**. Tests
exercise the **deployed** system (the backend is AWS serverless; there is no local server).
Default target environment: **dev1**.

## Commands

```bash
# setup
python -m venv .venv && source .venv/bin/activate
pip install -e . && pip install ruff mypy pre-commit
playwright install
npm install                       # Allure 3 CLI + Playwright CLI

# run
pytest -m api                     # API E2E only
pytest -m ui                      # UI E2E only
pytest -m "smoke or critical"     # PR gate subset (fast)
pytest -m "regression or contract"  # nightly set

# quality (must pass — same bar as production code)
ruff check . && ruff format --check . && mypy

# report
npm run report:generate && npm run report:open   # or: npm run report:watch
```

## Test architecture (the agreed shape)

| Layer | Tool | Share | Marker |
|---|---|---|---|
| API E2E (the workhorse) | `httpx` | ~70% | `@api` |
| Contract / fuzz | `schemathesis` (from OpenAPI) | nightly | `@contract` |
| UI E2E (thin, critical) | Playwright (`pytest-playwright`) | ~30% | `@ui` |

**Two-gate rule for a UI test:** (a) is the journey critical, *and* (b) does it genuinely
need a browser? If an API call can prove it, it is an **API** test. Default new tests to API.

**Strict layering** — each layer talks only to the one below:
`.feature` (declarative Gherkin) → **thin** step defs (orchestration only) → domain layer
(API client objects + page objects) → support/infra (config, fixtures, factories, assertions).

## Project structure

```
tests/
  features/ api/ ui/      # Gherkin (declarative, stakeholder-readable)
  step_defs/ api/ ui/     # thin glue
  support/                # config, auth, api_client, factories, assertions, pages/
  contract/               # schemathesis wiring
conftest.py               # root fixtures
allure/                   # Allure 3 config + self-hosted history
scripts/triage.py         # AI failure triage (off the gating path)
```

## Conventions

- **Tags:** `@smoke @critical @api @ui @regression @contract` + Allure `epic/feature/story`.
- **Data:** arrange-via-API only — seed/teardown through the API via Polyfactory factories.
  **Never** set up state through the UI. Use ephemeral/namespaced data; clean up (dev1 is shared).
- **Config:** one `Pydantic Settings` object from env (`tests/support/config.py`). No magic strings/URLs.
- **Secrets:** `.env` only (gitignored) / CI secrets. Never commit.
- Full Definition-of-Done + reuse patterns: [CONTRIBUTING.md](CONTRIBUTING.md) and
  `.github/instructions/e2e-best-practices.instructions.md`.

## Boundaries (never do these — the ban list)

- ❌ Logic, assertions, or conditionals in step defs.
- ❌ Raw `httpx` or `page.locator` in tests/steps (use client objects / page objects).
- ❌ Hardcoded data, URLs, magic strings.
- ❌ `sleep` / manual waits (use Playwright auto-wait / explicit conditions).
- ❌ God page-objects or kitchen-sink clients; shared mutable state between tests.
- ❌ Copy-pasted step defs (use the shared parametrized library).
- ❌ State set up through the UI; silent locator self-heal (every heal logs a loud warning).
- ❌ Unit tests; modifying the MontyCloud application code.

## Workflow (slash prompts)

- `/decide-api-vs-ui` — apply the two-gate rule to a candidate journey (run first).
- `/add-api-test` — author a new API E2E journey.
- `/add-ui-test` — author a thin UI E2E journey (Playwright).
- `/add-contract-test` — wire a schemathesis contract/fuzz test from the spec.

Every authored test must pass `ruff`, `mypy`, and the layering/ban-list checks before done.
