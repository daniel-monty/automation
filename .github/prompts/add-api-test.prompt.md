---
description: "Author a new API E2E journey (the workhorse layer): declarative .feature + thin step defs + per-resource httpx client object + Polyfactory + Allure-step assertions, fully tagged."
argument-hint: "<journey description or Jira key>  e.g. 'create a customer account then retrieve it' or PRO-1234"
---

# /add-api-test — Author an API E2E journey

Operate as the **`e2e-test-author`** agent. Produce a complete, layered, green API test.

## Step 0: Load domain knowledge (read in full)

- `.github/agents/e2e-test-author.agent.md` — operating rules + Definition of Done.
- `.github/instructions/e2e-best-practices.instructions.md` — layering, tags, ban list.
- `.github/instructions/e2e-best-practices.reference.md` — templates §1–6, §"Allure grouping".

## Step 1: Resolve the journey

Input: `${input:journey:Describe the journey, or paste a Jira key}`.
- Jira key → fetch it (`getJiraIssue(cloudId="montycloud.atlassian.net", issueIdOrKey=...)`),
  extract scenarios + acceptance criteria. No Jira access → ask the user to paste them.
- Confirm this is an **API** journey (run `/decide-api-vs-ui` if unsure). Halt if it should be UI.

## Step 2: Identify the resource(s) and endpoints

From the journey, name the resource(s) and the endpoint(s) involved. If the path/payload is
unknown, check the OpenAPI spec (`E2E_OPENAPI_SPEC`) or ask — **never invent endpoints**.

## Step 2b: Confirm the response shape (don't guess)

Before writing any body assertions, confirm the **actual** response structure — the envelope key
and the real per-item field names. Run the call once, or read the API's response schema (the app
codebase / OpenAPI spec). **Do not** invent keys, and **do not** assert query/filter params (e.g.
`Provider`, `Status`) as if they were response fields — they usually aren't returned per item. If
you can't confirm the shape, list it under **Confirm** and stop. Check whether a **create**
endpoint exists so the happy path can seed a known record and assert it appears (arrange-via-API)
rather than asserting against ambient data.

## Step 3: Plan and confirm

State: target resource, files to add/extend, scenarios (happy + at least one negative), tags, and
**the confirmed response shape + how the happy path avoids a vacuous pass** (seed + assert
presence, or assert the collection is non-empty). Get agreement before writing.

## Step 4: Implement (reuse before adding)

In dependency order, following the reference templates:
1. **Model** (§1) + **factory** (§2) — only if the resource has none yet.
2. **Client object** (§3) — reuse/extend an existing one in `tests/support/clients/` if present.
3. **Feature** (§5) — declarative Gherkin; happy path + ≥1 negative; `Background` for auth.
4. **Step defs** (§6) — thin glue; orchestrate the client; `parsers.parse`; call domain assertions.
5. **Assertions** (§4) — reuse `assert_status`; add domain assertions as Allure steps if needed.
6. **Tags + Allure** — `@api` + `@smoke`/`@critical`/`@regression`; `epic/feature/story`;
   add a Jira `@allure.link` on at least one scenario. (`layer=E2E` + `severity` are auto-derived
   from the tags by `conftest.py` — don't set them by hand.)

## Step 5: Verify

```bash
ruff check . && ruff format --check . && mypy
pytest tests/step_defs/api/<new_test>.py --collect-only
```
Run the test if creds for dev1 are configured; otherwise note the gap. 100% green required to close.

## Step 6: Success-criteria checklist

Confirm every Definition-of-Done item in `e2e-test-author.agent.md`. Then summarize the files
added and how to run the new scenario. Flag any deferred item with a reason.

> Do not modify the MontyCloud application code. Halt and ask if creds, base URL, or endpoint
> details are missing — never fabricate them.
