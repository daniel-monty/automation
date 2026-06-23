# Contributing to the MontyCloud E2E Suite

Treat test code as **production code**: same review bar, linting, and DRY discipline.
Good design is enforced by **layering + tooling**, not intention.

## The layering rule (each layer talks only to the one below)

1. **`.feature` (Gherkin)** — business intent, **declarative**. No mechanics.
   - ✅ `Given I am a subscribed user`
   - ❌ `Given I click login, type email…`
2. **Step definitions** — **thin glue only**: orchestrate. No logic, conditionals, raw
   HTTP, raw locators, or buried assertions. If a step def runs more than a few lines,
   it's doing a lower layer's job.
3. **Domain layer** — API client objects (per resource) + page/component objects (UI).
   Actions live here. Role-based locators live **only** in page objects.
4. **Support / infra** — typed config, fixtures, data factories, base HTTP client,
   custom assertions.

## Reuse levers (DRY)

- **Data factories** (`Polyfactory` on Pydantic models) — every test arranges state via
  these, never by hand. Shared by API and UI tests. → `tests/support/factories.py`
- **API client objects per resource** — encapsulate base URL, auth, headers, retries,
  serialization, Allure-step wrapping. Tests never touch raw `httpx`. → extend
  `tests/support/api_client.py`.
- **Small, composable page objects** over god-objects. → `tests/support/pages/`
- **Shared, parametrized step library** (`parsers.parse`) + `Background` for
  preconditions. No copy-pasted step defs.
- **One `Pydantic Settings` config** from env — single source of truth. →
  `tests/support/config.py`
- **Reusable domain assertions** wrapped as Allure steps. → `tests/support/assertions.py`

## Arrange-via-API (the core technique)

Seed and tear down state **through the API**; drive the browser only for the user-facing
journey; assert through both UI and API. **Never set up state through the UI.** Use
ephemeral / namespaced data and clean up — dev1 is shared and DynamoDB has no easy
rollback.

## Tag taxonomy (one scheme, three jobs)

`@smoke @critical @api @ui @regression @contract` + Allure `epic / feature / story`.

- **Run selection:** `pytest -m "smoke or critical"`, `-m api`, `-m ui`, …
- **PR gate:** `@smoke` / `@critical` (fast, blocks the PR).
- **Nightly:** `@regression` + `@contract` (full + fuzz).
- **Leadership grouping:** Allure `epic/feature/story`; link a Jira requirement on at
  least one scenario.

## Definition of Done (a test is done when it is…)

- [ ] Clearly named and **declarative** in the `.feature`.
- [ ] **Tagged** correctly (run selection + report grouping).
- [ ] Step def is **thin** (orchestration only).
- [ ] Data arranged via a **factory** (never hand-built).
- [ ] Locators live in a **page object** (UI); raw `httpx` lives in a **client object** (API).
- [ ] Assertions are **reusable domain assertions wrapped as Allure steps**.
- [ ] Passes **ruff** + **mypy**.
- [ ] Correct layer choice justified by the **two-gate rule** (API unless it truly needs a browser).

## Ban list (PR checklist — reject if any appear)

- [ ] Logic / assertions / conditionals in step defs
- [ ] Raw `httpx` or `page.locator` in tests/steps
- [ ] Hardcoded data, URLs, or magic strings
- [ ] `sleep` / manual waits (use Playwright auto-wait / explicit conditions)
- [ ] God page-objects or kitchen-sink clients
- [ ] Shared mutable state between tests
- [ ] Copy-pasted step defs (use the shared parametrized library)
- [ ] State set up through the UI (must be arrange-via-API)
- [ ] Silent locator self-heal (every heal must log a loud warning)

## Golden exemplars

> **Skeleton note:** no exemplars exist yet. When the first journeys are authored, the
> canonical **API** sample (e.g. `customer_account` lifecycle) and **UI** sample (login →
> dashboard renders real, API-seeded data + ARIA-snapshot) are designated the templates
> to copy. Mark them clearly and keep them green.
