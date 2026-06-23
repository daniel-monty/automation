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

## Tags (one scheme, three jobs)

`@smoke @critical @api @ui @regression @contract` + Allure `epic/feature/story`.
- Gate (PR): `@smoke`/`@critical`. Nightly: `@regression`/`@contract`.
- Tag the `.feature` declaratively; every scenario gets a layer tag (`@api` or `@ui`).

## Data — arrange-via-API only

Seed and tear down state **through the API** using Polyfactory factories
(`tests/support/factories.py`). **Never** set up state through the UI. Use ephemeral /
namespaced data and clean up — dev1 is shared and DynamoDB has no easy rollback.

## Assertions

Reusable domain assertions wrapped as Allure steps (`tests/support/assertions.py`). Step defs
call these; they never inline raw asserts.

## Definition of Done

Clearly named · declarative `.feature` · correctly tagged · thin step def · data via factory ·
locators in a page object / raw `httpx` in a client object · assertion is an Allure step ·
passes `ruff` + `mypy` · layer justified by the two-gate rule.

## Ban list (reject if any appear)

Logic/assertions/conditionals in step defs · raw `httpx` or `page.locator` in tests/steps ·
hardcoded data/URLs · `sleep`/manual waits · god page-objects or kitchen-sink clients ·
shared mutable state between tests · copy-pasted step defs · state set up via the UI ·
silent locator self-heal (every heal must log a loud warning).
