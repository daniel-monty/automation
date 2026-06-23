---
description: "Wire a schemathesis contract/fuzz test from the OpenAPI spec for an endpoint group. Schema-driven coverage for the nightly suite."
argument-hint: "<endpoint group or tag>  e.g. 'customer_account' or 'all'"
---

# /add-contract-test — Wire a schemathesis contract test

Operate as the **`e2e-test-author`** agent. Generate schema-driven contract/fuzz coverage that
runs in the **nightly** suite (`@contract`), authenticated against dev1.

## Step 0: Load domain knowledge

- `.github/instructions/e2e-best-practices.instructions.md`
- `.github/instructions/e2e-best-practices.reference.md` — template §10.
- `tests/contract/conftest.py` — existing wiring notes.

## Step 1: Confirm the spec

The spec comes from `E2E_OPENAPI_SPEC` (the richer spec). If it is unset or unreachable,
**halt and ask** — do not point schemathesis at a fabricated or stale spec. Confirm the spec is
OpenAPI 3.x and lists the target endpoint group `${input:scope:Endpoint group/tag, or 'all'}`.

## Step 2: Plan

State: the spec source, the scope filter (operation tag / path prefix), the auth strategy
(`Authenticator.headers()`), and any operations to exclude (destructive ops on shared dev1).
Confirm before writing.

## Step 3: Implement (reference template §10)

1. Build the schema with `schemathesis.openapi.from_url(settings.openapi_spec)`.
2. Filter to the target scope (by tag/path) so the test is focused and nightly-sized.
3. Authenticate every case via `Authenticator(settings).headers()`.
4. Use `case.call_and_validate(...)` so responses are checked against the schema.
5. Mark `@pytest.mark.contract`. **Exclude destructive operations** on shared dev1 unless the
   data is ephemeral and torn down.

## Step 4: Verify

```bash
ruff check . && ruff format --check . && mypy
pytest -m contract --collect-only
```
With the spec + dev1 creds set, run a short sample (`--hypothesis-max-examples` low) to confirm
it executes. Note the gap if creds/spec are absent. Keep heavy fuzzing in the nightly job only.

## Step 5: Success-criteria checklist

Confirm: spec is real and reachable · scope filtered · auth applied · destructive ops excluded ·
marked `@contract` · `ruff`/`mypy` pass. Summarize what was wired and the nightly run command.

> Never fabricate a spec or endpoints. The contract layer is nightly-only — keep it off the PR gate.
