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
pip install -e . --group dev
playwright install
npm install                       # Allure 3 CLI + Playwright CLI

# run
pytest -m api                     # API E2E only
pytest -m ui                      # UI E2E only
pytest -m "smoke or critical"     # PR gate subset (fast)
pytest                            # nightly: every scenario + contract

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

**One HTTP tool per concern:** the API and contract layers use **`httpx`** (browserless, fast,
typed, pairs with schemathesis + Polyfactory); **Playwright is UI-only**. Do **not** use
Playwright's `APIRequestContext` / `context.request` for API tests. (Inside a UI test,
`context.request` is allowed only for a cookie-bound arrange step — prefer the httpx client objects.)

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
```

## Conventions

- **Tags:** `@smoke @critical @api @ui @regression @contract` + Allure `epic/feature/story`.
- **Data:** arrange-via-API only — seed/teardown through the API via Polyfactory factories.
  **Never** set up state through the UI. Use ephemeral/namespaced data; clean up (dev1 is shared).
- **Config:** one `Pydantic Settings` object from env (`tests/support/config.py`). No magic strings/URLs.
- **Secrets:** `.env` only (gitignored) / CI secrets. Never commit.
- Full Definition-of-Done + reuse patterns: [CONTRIBUTING.md](CONTRIBUTING.md) and
  `.github/instructions/e2e-best-practices.instructions.md`.

## Boundaries

- ❌ **Do not modify the MontyCloud application code** — only add/maintain test infrastructure.
- ❌ **No unit tests** — E2E / system-level only.
- The full test-authoring **ban list** (thin step defs; no raw `httpx`/locators; no Playwright
  `APIRequestContext` for API; arrange-via-API; no `sleep` (use `wait_until`)/hand-rolled retries/god-objects/copy-paste; no silent
  self-heal) is canonical in `.github/instructions/e2e-best-practices.instructions.md`.

## Workflow (slash prompts)

- `/build-test-prompt` — turn a curl / Jira key / journey / draft into a ready-to-run `/add-*-test` prompt.
- `/decide-api-vs-ui` — apply the two-gate rule to a candidate journey (run first).
- `/add-api-test` — author a new API E2E journey.
- `/add-ui-test` — author a thin UI E2E journey (Playwright).
- `/add-contract-test` — wire a schemathesis contract/fuzz test from the spec.

Every authored test must pass `ruff`, `mypy`, and the layering/ban-list checks before done.

## Agents & MCP

Agents (`.github/agents/`): **`e2e-test-author`** (prompts delegate to it), **`e2e-test-reviewer`**
(read + lint, ban-list enforcement), **`e2e-failure-triage`** (classify/dedupe/post new failures).
The **Atlassian MCP** (`.vscode/mcp.json`) gives agents Jira/Confluence access — fetch ticket
acceptance criteria, read the known-issues list, post triage summaries. Don't put Jira tokens in
the repo.
