# Copilot Baseline Standards — MontyCloud E2E Suite

These standards apply whenever Copilot is used in this repository.

For the suite's purpose, structure, tech stack, commands, and the **ban list**, read
[`AGENTS.md`](../AGENTS.md) at the repo root — it is the source of truth. Do not duplicate
or contradict it.

---

## Workflow (slash prompts)

This repo provides reusable prompts in `.github/prompts/` for authoring test cases:

- `/decide-api-vs-ui` — apply the two-gate rule to a candidate journey **before** writing code.
- `/add-api-test` — author a new API E2E journey (the workhorse layer).
- `/add-ui-test` — author a thin, critical UI E2E journey (Playwright).
- `/add-contract-test` — wire a schemathesis contract/fuzz test from the OpenAPI spec.

**Typical flow:** `/decide-api-vs-ui` → `/add-api-test` *or* `/add-ui-test`.

These prompts operate as the **`e2e-test-author`** agent (`.github/agents/`). The
**`e2e-test-reviewer`** agent reviews a diff against the ban list (read + lint only).

---

## Path-scoped instructions

`.github/instructions/e2e-best-practices.instructions.md` is auto-applied to `tests/**`.
Full copy-paste templates (client object, page object, factory, step def, `.feature`,
assertion) live in its companion `e2e-best-practices.reference.md` — load it when authoring.

---

## Guardrails (on top of AGENTS.md)

- **Explain your approach before writing code** — prevents wasted effort on the wrong layer.
- **Apply the two-gate rule first:** default a new test to the **API** layer; reach for the
  browser only when the value is the rendered experience or a true cross-system flow.
- **Respect strict layering:** step defs stay thin (orchestration only) — no logic,
  assertions, raw `httpx`, or raw locators above the domain layer.
- **Arrange-via-API for all data;** never seed state through the UI.
- **Fix the root cause** of every `ruff` / `mypy` / type error — never suppress.
- **Do not modify the MontyCloud application code** — only add/maintain test infrastructure.
- **Keep secrets out of the repo** (`.env` + env vars).
- **Verify, don't assume** for the Allure 3 adapter→v3 seam: smoke-test `allure generate`
  before relying on v3 quality-gate / known-issues / environments features.

---

## Communication

- Flag any unplanned change before making it; only touch files that were discussed.
- If something must be deferred, say so explicitly with a reason.
- When scope is unclear, ask before assuming the most feature-rich solution.
