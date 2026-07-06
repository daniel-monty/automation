---
description: "Generate or improve an authoring prompt (/add-api-test, /add-ui-test, /add-contract-test) from a curl, a Jira key, a journey description, or a rough draft — fully aligned to the suite's conventions. Outputs a ready-to-run prompt; does not write tests."
argument-hint: "<curl | Jira key | journey description | rough draft prompt>"
---

# /build-test-prompt — Generate or improve a test-authoring prompt

You turn raw input into a polished, convention-correct `/add-*-test` prompt that the
`e2e-test-author` agent can run. **You do not author tests or write files** — you output a single
prompt block for the user to review and run. Generation is cheap; the review is the point.

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
**outside** the block, a short **Confirm:** list of anything missing (base URL/creds, exact
payload, response keys, the OpenAPI spec for contract). End with:
"Review, then run this prompt to author the test."

> Output a prompt only — do not create files, clients, features, or tests yourself.
