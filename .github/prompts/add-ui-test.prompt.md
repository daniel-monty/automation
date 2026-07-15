---
description: "Author a thin, critical UI E2E journey with Playwright: page object + declarative .feature + thin step defs, state seeded via API, an ARIA-snapshot assertion, traces/screenshots to Allure on failure."
argument-hint: "<journey description or Jira key>  e.g. 'login then the cost dashboard renders my data' or PRO-1234"
---

# /add-ui-test — Author a UI E2E journey

Operate as the **`e2e-test-author`** agent. UI tests are **thin and rare** — only critical,
genuinely browser-bound journeys.

## Step 0: Load domain knowledge (read in full)

- `.github/agents/e2e-test-author.agent.md`
- `.github/instructions/e2e-best-practices.instructions.md`
- `.github/instructions/e2e-best-practices.reference.md` — templates §7–9, §"Allure grouping".

## Step 1: Confirm it earns a browser

Input: `${input:journey:Describe the journey, or paste a Jira key}` (fetch Jira if a key).
**Apply the two-gate rule.** If an API call could prove it, **halt** and route to
`/add-api-test`. Proceed only if the value is the rendered experience or a true cross-system flow.

## Step 2: Explore the live app (Playwright agent stack)

Use the Python **`playwright` CLI** (`playwright codegen`) or Playwright MCP to explore the deployed dev1
app (`E2E_UI_BASE_URL`) and identify **role-based** locators (`getByRole`/`getByLabel`) for the
journey. Prefer the accessibility tree over CSS.

> ⚠️ Playwright codegen / Test Agents emit **TypeScript**. You **must materialize output as
> Python `pytest-bdd`** step defs + page objects — translate TS→Python. Never commit TS.

## Step 3: Plan and confirm

State: the page object(s), the `.feature` (and its cloud provider — Azure or AWS — which fixes
its subdir under `tests/features/ui/<azure|aws>/` and `tests/step_defs/ui/<azure|aws>/`), how
state is **seeded via API** (which factory / client), and the ARIA-snapshot target. Get
agreement before writing.

## Step 4: Implement (reference templates §7–9)

1. **Page object** (§7) — role-based locators only; small and composable; extends `BasePage`.
2. **Feature** (§8) — declarative; `Given` seeds state **via API**, `When` drives the browser;
   tag with `@ui` + `@azure`/`@aws`.
3. **Step defs** (§9) — thin glue; the `Given` calls the API client/factory (arrange-via-API);
   the `Then` uses `expect(...).to_match_aria_snapshot(...)` for structure (not brittle CSS).
   Reserve `to_have_screenshot()` for genuine visual drift on pages that matter.
4. **Failure artifacts** — ensure screenshot + trace attach to Allure on failure (suite fixture).
5. **Tags + Allure** — `@ui` + `@azure`/`@aws` + `@critical`/`@smoke`; `cloud/epic/feature/story`;
   Jira `@allure.link`.

## Step 5: Verify

```bash
ruff check . && ruff format --check . && mypy
pytest tests/step_defs/ui/<azure|aws>/<new_test>.py --collect-only
```
Run with dev1 creds if available; otherwise note the gap. Locator self-heal must log a loud
warning — never silent. 100% green required to close.

## Step 6: Success-criteria checklist

Confirm the Definition of Done. Summarize files added + how to run. Confirm no state was
seeded through the UI and no TypeScript was committed.

> Do not modify the MontyCloud application code. Halt and ask if creds/base URL are missing.
