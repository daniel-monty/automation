---
name: decide-api-vs-ui
description: "Apply the two-gate rule to a candidate journey and recommend the test layer (API / UI / contract) before any code is written."
disable-model-invocation: true
argument-hint: "<journey description or Jira key>  e.g. 'user enables a Day2 bot and sees it active' or PRO-1234"
---
# /decide-api-vs-ui — Choose the test layer

You recommend the correct E2E layer for a candidate journey. **You do not write tests** — you
produce a decision and hand off to `/add-api-test` or `/add-ui-test`.

## Step 1: Read the rules

Read `.github/instructions/e2e-best-practices.instructions.md` (the two-gate rule + tags).

## Step 2: Resolve the journey

Input: the argument passed after `/decide-api-vs-ui` — a journey description or a Jira key. If none was
given, ask for it.
- If it looks like a Jira key (e.g. `PRO-1234`), fetch it
  (`getJiraIssue(cloudId="montycloud.atlassian.net", issueIdOrKey=...)`) and read the
  acceptance criteria / test cases. If you cannot access Jira, ask the user to paste them.
- Otherwise treat the text as the journey description.

## Step 3: Apply the two gates

For the journey, answer explicitly:
1. **Critical?** Is this a business-critical / revenue / security path? (yes/no + why)
2. **Needs a browser?** Is the *value* the rendered experience or a true cross-system flow,
   or can an API call fully prove the outcome? (yes/no + why)

## Step 4: Recommend

- **Both yes** → **UI E2E** (`@ui`). Note: state must still be seeded via API.
- **Critical, not browser-bound** → **API E2E** (`@api @critical`).
- **Schema/endpoint coverage or fuzzing** → **contract** (`@contract`, nightly).
- **Not critical and API-provable** → API E2E `@regression` (or descope).

## Output

A short verdict block:
```
Journey: <one line>
Gate 1 (critical): yes/no — <reason>
Gate 2 (needs browser): yes/no — <reason>
Decision: API | UI | contract  (tags: …)
Next: run /add-api-test (or /add-ui-test, /add-contract-test) with this journey
```
Recommend the **API** layer unless Gate 2 is a clear yes. Stop after the recommendation.
