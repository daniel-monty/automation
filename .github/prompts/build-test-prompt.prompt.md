---
description: "Generate or improve an authoring prompt (/add-api-test, /add-ui-test, /add-contract-test) from a curl, a Jira key, a journey description, or a rough draft — fully aligned to the suite's conventions. Outputs a ready-to-run prompt; does not write tests."
argument-hint: "<curl | Jira key | journey description | rough draft prompt>"
---

# /build-test-prompt — Generate or improve a test-authoring prompt

You turn raw input into a polished, convention-correct `/add-*-test` prompt that the
`e2e-test-author` agent can run. **You do not author tests or write files** — you output a single
prompt block for the user to review and run. Generation is cheap; the review is the point — but
for cross-system flows a wrong guess is not cheap, so Step 1b asks first when it must.

## Step 0: Load conventions

Read `.github/instructions/e2e-best-practices.instructions.md` (two-gate rule, tags, layering, ban
list) and the target prompts in `.github/prompts/` (`add-api-test`, `add-ui-test`,
`add-contract-test`). Match their shape exactly.

## Step 1: Parse the input

Input: `${input:source:Paste a curl, a Jira key, a journey description, or a rough draft prompt}`.
Detect the type and extract intent:
- **curl / raw HTTP** → method, path, query/body params, response shape if shown.
- **Jira key** (e.g. `PRO-1234`) → fetch via the Atlassian MCP; read acceptance criteria / TCs.
- **journey description** → treat the prose as the intent.
- **existing draft prompt** → improve it: fix stale/auth lines, add missing scenarios/tags/Allure,
  correct fixture/resource naming.

**Strip incidental noise from curls:** drop browser headers (`user-agent`, `sec-*`, cookies,
analytics) and the captured `authorization` token — auth is automatic (Step 3). Never echo a real
token or secret.

## Step 1b: Clarify gate (blocking unknowns → ask before generating)

Sort every unknown into one of two buckets:
- **Blocking** — the answer changes the *shape* of the prompt (layer, arrange strategy, what gets
  polled, prerequisite infra, scenario scope). Ask **before** generating.
- **Non-blocking** — a missing *value* (a UUID, a field name, an exact payload key). Don't ask;
  list it under **Confirm:** in Step 6.

**Stop and ask first** if any of these hold:
1. **Crosses into a system the suite has no client for** (e.g. S3, ECS, CloudWatch, Step Functions,
   AWS tagging) — check `tests/support/clients/` and `pyproject.toml`. Missing support code is a
   separate prerequisite prompt; never let the author improvise raw SDK calls in step defs.
2. **Arrange can't go through the public API** (synthesizing a CUR file, triggering a state
   machine) — a ban-list exception that needs explicit sign-off.
3. **The outcome is async / out-of-band** (ECS task, step function, scheduled job) — need the
   correlation ID to poll on, the timeout, and what "done" means.
4. **Shared or real cloud resources** — reused pool vs per-run creation, and how parallel runs
   avoid colliding.
5. **Environment or credentials differ from the defaults** (not dev1, cross-account access, extra
   IAM roles).
6. **The input contradicts itself or adds steps beyond the acceptance criteria.**

**How to ask:** at most ~5 questions, each with a **recommended default** so the user can reply
"defaults". After the answers, echo a 3–5 line plan (layer · arrange · act · what's polled/asserted
· teardown) and **wait for a yes** before Step 2. If no trigger fires (e.g. a single-endpoint curl
with a known shape), skip this step and generate directly.

## Step 2: Choose the layer (two-gate rule)

Pick the target prompt:
- Provable by an API call → **`/add-api-test`** (default).
- Critical **and** genuinely needs a browser (rendered experience / true cross-system flow) →
  **`/add-ui-test`**.
- Schema-driven endpoint fuzzing from the OpenAPI spec → **`/add-contract-test`**.
If the layer is genuinely unclear, recommend running `/decide-api-vs-ui` first and stop.

## Step 3: Normalize auth (current framework)

State auth as: **handled automatically by the `api_client` fixture** (login via `/auth/signin` →
ID token in `Authorization`, raw, no `Bearer`). Add an `x-api-key` note **only** if the endpoint
needs it (else leave `E2E_API_KEY` blank). For negative cases, use the `unauthenticated_api_client`
fixture. Never include Cognito details or real tokens.

## Step 4: Derive scenarios (declarative)

- A happy path tagged `@smoke @critical` (or `@regression`).
- Edge cases implied by the input (pagination, filters, state transitions).
- At least one **negative** (unauthenticated → 401/403; or invalid input → 400 if known).
Business intent only — no mechanics. **Never invent** endpoints, payloads, or response keys; if a
path/param/response field is unknown, list it under **Confirm** rather than guessing.

## Step 5: Name the structure

- Resource + a `<Resource>Client` in `tests/support/clients/` with typed query/body params.
- A Pydantic model + Polyfactory factory if the resource has a request body.
- Allure `epic / feature / story` + the layer tag (`@api` / `@ui` / `@contract`). (`layer=E2E` +
  `severity` are auto-derived from the tags by `conftest.py` — no need to set them.)

## Step 6: Output

Emit **one fenced block**: the ready-to-run `/add-<layer>-test …` prompt, in the same shape as the
existing add-* prompts (endpoint, params, auth note, tagged scenarios, resource/client, Allure
labels, "keep step defs thin; assert via Allure-step assertions; verify ruff + mypy"). Then,
**outside** the block, a short **Confirm:** list of the remaining *non-blocking* gaps (base
URL/creds, exact payload, response keys, the OpenAPI spec for contract) — blocking unknowns were
settled in Step 1b, so never park one here. End with:
"Review, then run this prompt to author the test."

> Output a prompt only — do not create files, clients, features, or tests yourself.
