---
applyTo: "tests/**,conftest.py"
name: "MontyCloud E2E Conventions"
description: "Layering, tagging, data, and ban-list rules for the E2E suite. Auto-applied when editing tests."
---

# MontyCloud E2E Conventions

Enforces the suite's standards for everything under `tests/`. Follow **all** rules.
For copy-paste templates and full examples, see
[e2e-best-practices.reference.md](e2e-best-practices.reference.md).

## Strict layering (each layer talks only to the one below)

1. **`.feature` (Gherkin)** — business intent, **declarative**. No mechanics.
   ✅ `Given I am a subscribed user`  ❌ `Given I send POST /login with body {…}`
2. **Step definitions** — **thin glue only**: orchestrate. No logic, conditionals, raw HTTP,
   raw locators, or buried assertions. More than a few lines ⇒ it's doing a lower layer's job.
3. **Domain layer** — API client objects (per resource, `tests/support/`) + page objects
   (`tests/support/pages/`). Actions and role-based locators live here.
4. **Support/infra** — typed config, fixtures, factories, base client, custom assertions.

## Two-gate rule (which layer)

A journey earns a **UI** test only if (a) it is critical **and** (b) it genuinely needs a
browser (the value is the rendered experience or a true cross-system flow). Otherwise it is
an **API** test. Default new tests to API.

**One HTTP tool per concern:** API and contract tests use **`httpx`** (via the client objects) —
**never** Playwright's `APIRequestContext` / `context.request`. Playwright is for UI rendering
and interaction only. (`context.request` is permissible inside a UI test solely for a
cookie-bound arrange step, but prefer the httpx client objects there too.)

## Tags (one scheme, three jobs)

`@smoke @critical @api @ui @regression @contract` + Allure `epic/feature/story`.
- Gate (PR): `@smoke`/`@critical`. Nightly: `@regression`/`@contract`.
- Tag the `.feature` declaratively; every scenario gets a layer tag (`@api` or `@ui`).
- **Allure `layer` (E2E) + `severity` are auto-derived from these tags** by `conftest.py`
  (`pytest_collection_modifyitems`): `@smoke`/`@critical` -> `critical`, everything else ->
  `normal`; every test -> `layer=E2E` (drives the Test Pyramid). Don't set them by hand.

## Data — arrange-via-API only

Seed and tear down state **through the API** using Polyfactory factories
(`tests/support/factories.py`). **Never** set up state through the UI. Use ephemeral /
namespaced data and clean up — dev1 is shared and DynamoDB has no easy rollback.

## Assertions

Reusable domain assertions wrapped as Allure steps (`tests/support/assertions.py`). Step defs
call these; they never inline raw asserts.

### Assertion integrity — never write a vacuously-green test

A test that passes without exercising the behaviour is worse than no test. Enforce:

- **Confirm the response shape — never guess it.** Before asserting on a body, confirm its real
  structure: run the call once, or read the API's response schema in the app codebase / the
  OpenAPI spec. Do not invent envelope keys or field names. If the shape is unknown, list it under
  **Confirm** and stop — do not guess.
- **Never assert request/query params as response fields.** Filter inputs (e.g. `Provider`,
  `Status`) are not guaranteed to appear on each returned item — assert only fields the response
  actually contains.
- **Guard every collection assertion against empty.** Any "every item …" check MUST first assert
  the collection is **non-empty** (or be backed by seeded data). A `for item in items: assert …`
  over `[]` is a silent pass and is banned.
- **No failure-hiding fallbacks.** Parse/extract helpers must fail loudly on an unexpected shape
  (assert the expected key exists) — never `return []` / swallow, which turns a real failure green.
- **Arrange-via-API when the resource is creatable.** If a create endpoint exists, seed a known
  record via the API and assert it appears (by id) — don't assert against ambient environment data.

## Definition of Done

Clearly named · declarative `.feature` · correctly tagged · thin step def · data via factory ·
locators in a page object / raw `httpx` in a client object · assertion is an Allure step ·
passes `ruff` + `mypy` · layer justified by the two-gate rule · **response shape confirmed (not
guessed); every collection assertion guarded against empty; data seeded via API when the resource
is creatable; no unused models/helpers; the test actually runs (not just `--collect-only` —
collect-green ≠ run-green)**.

## Ban list (reject if any appear)

Logic/assertions/conditionals in step defs · raw `httpx` or `page.locator` in tests/steps ·
hardcoded data/URLs · `sleep`/manual waits · god page-objects or kitchen-sink clients ·
shared mutable state between tests · copy-pasted step defs · state set up via the UI ·
Playwright `APIRequestContext` for API tests (use httpx) ·
silent locator self-heal (every heal must log a loud warning) ·
guessed response shapes / failure-hiding fallbacks (`return []` on an unknown shape) ·
collection assertions that pass on an empty list · asserting query/filter params as response
fields · unused models/factories/helpers (dead code).
