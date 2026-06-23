# MontyCloud E2E Automation Suite

API-first, UI-supported **end-to-end** BDD automation for the MontyCloud platform.
One language (Python), one runner (**pytest + pytest-bdd**), one combined report (**Allure 3**).

> **Status:** infrastructure + GitHub Copilot authoring layer are complete and verified
> (`ruff`/`mypy` clean, deps resolve, `pytest` collects). There are **no `.feature` tests yet** —
> the first golden exemplars (one API journey, one UI journey) are authored next, using the
> `/add-*` prompts below.

E2E / system-level only — **no unit tests**. Tests exercise the running, **deployed** system
(the MontyCloud backend is AWS serverless; there is no local server to boot). Default target
environment: **dev1**.

---

## Table of contents

1. [Architecture & the two-gate rule](#1-architecture--the-two-gate-rule)
2. [Prerequisites](#2-prerequisites)
3. [Installation](#3-installation)
4. [Configuration (`.env`)](#4-configuration-env)
5. [Running tests](#5-running-tests)
6. [The Allure 3 report](#6-the-allure-3-report)
7. [Writing a new test](#7-writing-a-new-test)
8. [Tag taxonomy](#8-tag-taxonomy)
9. [Project layout](#9-project-layout)
10. [Code quality](#10-code-quality)
11. [CI/CD](#11-cicd)
12. [AI failure triage](#12-ai-failure-triage)
13. [Troubleshooting & FAQ](#13-troubleshooting--faq)
14. [Versions & compatibility](#14-versions--compatibility)
15. [Where to go next](#15-where-to-go-next)

---

## TL;DR

```bash
git clone <repo-url> && cd Automation
python3.12 -m venv .venv && source .venv/bin/activate     # Python 3.11+
pip install -e . && pip install ruff mypy pre-commit
playwright install                                         # browsers
npm install                                                # Allure 3 CLI + Playwright CLI
cp .env.example .env                                       # fill in dev1 creds (never commit)

pytest -m "smoke or critical"                              # run the gate subset
npm run report:generate && npm run report:open            # view the Allure report
```

To add a test, open the repo in VS Code / Copilot and run `/decide-api-vs-ui`, then
`/add-api-test` or `/add-ui-test` (see [§7](#7-writing-a-new-test)).

---

## 1. Architecture & the two-gate rule

| Layer | Tool | Share | Marker |
|---|---|---|---|
| **API E2E** (the workhorse) | `httpx` | ~70% | `@api` |
| **Contract / fuzz E2E** | `schemathesis` (from OpenAPI) | nightly | `@contract` |
| **UI E2E** (thin, critical) | Playwright (`pytest-playwright`) | ~30% | `@ui` |
| **Reporting** | Allure 3 | — | — |

**Two-gate rule — what earns a UI test:** (a) is the journey *critical*, **and** (b) does it
*genuinely need a browser* (the value is the rendered experience or a true cross-system flow)?
If an API call can prove it, it's an **API** test, not a UI one. **Default new tests to API.**

**Strict layering** — each layer talks only to the one below:

```
.feature (declarative Gherkin)      ← business intent, no mechanics
   └─ step definitions (thin glue)  ← orchestration only; no logic/HTTP/locators/asserts
        └─ domain layer             ← API client objects + page objects (actions live here)
             └─ support / infra     ← config, fixtures, factories, base client, assertions
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full Definition of Done and the ban list.

---

## 2. Prerequisites

| Requirement | Why | Check |
|---|---|---|
| **Python 3.11+** | the suite's own venv (decoupled from the app's 3.7 runtime) | `python3 --version` |
| **Node 18+** (20+ recommended) | Allure 3 CLI + Playwright tooling | `node --version` |
| **dev1 access** | tests hit the deployed dev1 API/UI | see [§4](#4-configuration-env) |
| **Cognito test user** (no-MFA) + `x_api_key` | auth for API/UI calls | from the platform team |

If you don't have Python 3.11+: `brew install python@3.12` (macOS) or use `pyenv`/`uv`.
If your Node is old: `brew install node` or `nvm install 20`.

---

## 3. Installation

```bash
cd Automation

# 1. Python venv (3.11+) + the suite (editable) + dev tools
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .                      # runtime deps from pyproject.toml
pip install ruff mypy pre-commit      # quality tooling

# 2. Playwright browsers (for UI tests)
playwright install                    # or: playwright install --with-deps chromium

# 3. Git hooks (ruff + mypy on commit)
pre-commit install

# 4. Node tooling — Allure 3 CLI + Playwright CLI
npm install

# 5. Environment
cp .env.example .env                  # then fill it in (see §4)
```

> The Allure **3** CLI ships as the npm package `allure` (in `devDependencies`). `npm install`
> makes `npm run report:*` work. To use `allure` directly anywhere, `npm i -g allure`.

---

## 4. Configuration (`.env`)

All config is a single typed object (`tests/support/config.py`, `pydantic-settings`). Every var
is prefixed `E2E_` and loaded from `.env` (gitignored) or real env vars in CI. Copy
`.env.example` and fill in:

| Variable | Purpose | Where to get it |
|---|---|---|
| `E2E_ENV` | target env label (default `dev1`) | — |
| `E2E_API_BASE_URL` | dev1 API base URL | platform team / OpenAPI `servers` |
| `E2E_UI_BASE_URL` | dev1 app URL (for Playwright) | platform team |
| `E2E_API_KEY` | `x-api-key` header value | platform team (secret) |
| `E2E_COGNITO_REGION` | Cognito region (e.g. `us-east-1`) | platform team |
| `E2E_COGNITO_USER_POOL_ID` | Cognito user pool | platform team |
| `E2E_COGNITO_CLIENT_ID` | Cognito **app client** (USER_PASSWORD_AUTH enabled) | platform team |
| `E2E_TEST_USERNAME` / `E2E_TEST_PASSWORD` | dedicated **no-MFA** test user | platform team (secret) |
| `E2E_OPENAPI_SPEC` | path/URL to the richer OpenAPI spec | drives `@contract` layer |
| `E2E_LLM_*` | optional LLM for failure triage | off the gating path |
| `E2E_JIRA_*` | optional Jira project for requirement links | — |

**How auth works:** `tests/support/auth.py` mints a Cognito **ID token** via `USER_PASSWORD_AUTH`
and sends it as `Authorization` alongside `x-api-key`. Tests never handle tokens directly — the
`api_client` fixture attaches both headers automatically.

> ⚠️ **Never commit `.env`.** It is gitignored. In CI, the same values come from GitHub secrets.

---

## 5. Running tests

```bash
# By layer / selection (tags)
pytest -m api                       # API E2E only
pytest -m ui                        # UI E2E only
pytest -m "smoke or critical"       # the PR gate subset (fast)
pytest -m "regression or contract"  # the full nightly set
pytest -m "api and not slow"        # combine markers
pytest                              # everything

# Targeting
pytest tests/step_defs/api/test_customer_account.py     # one file
pytest -k "create and account"                          # by name substring
pytest tests/step_defs/api/test_customer_account.py::test_create   # one test

# Useful flags
pytest -v                           # verbose (one line per scenario)
pytest -x                           # stop at first failure
pytest -ra                          # summary of skips/fails (already in addopts)
pytest --alluredir=allure-results   # already set in pyproject; results for the report
```

> Until the first `.feature` is authored, `pytest` reports **"no tests collected"** — that's
> expected, not an error.

**Parallelism:** add `pytest-xdist` (`pip install pytest-xdist`) and run `pytest -n auto`. Because
state is arranged via API with namespaced/ephemeral data, scenarios are independent and safe to
parallelize — but mind shared-dev1 rate limits.

---

## 6. The Allure 3 report

```bash
npm run report:generate   # allure generate allure-results --output allure-report --clean
npm run report:open       # open the generated report in a browser
npm run report:watch      # live-updating report while you run tests locally
```

What the report gives you:

- **Stakeholder grouping** — `epic / feature / story` (set via tags/decorators on tests).
- **Environments** — API vs UI results separated and linked in one report (`allure/allurerc.mjs`).
- **History / trends** — **self-hosted** in `allure/history/` (no SaaS, per EU + GOVCloud
  data-residency). CI restores it before each run so trends persist.
- **Categories** — failures bucketed (known issues / infra / test defect / product defect) via
  `allure/categories.json`.
- **Quality gate** — `allure/allurerc.mjs` fails on critical-severity failures (reporting-side
  gate; the hard PR gate is pytest's own exit code).
- **Known issues** — `allure/known-issues.json` labels known/blocked items separately from new
  failures (sync from Jira where possible).

> ⚠️ **Verify on first run.** The Python adapter (`allure-pytest-bdd`) emits Allure **2** result
> JSON; the Allure **3** CLI renders it. Smoke-test a real `allure generate` and confirm the v3
> config keys (quality gate / known-issues / environments) before relying on them.

---

## 7. Writing a new test

### 7.1 Decide the layer (always first)

Apply the [two-gate rule](#1-architecture--the-two-gate-rule). In Copilot:

```
/decide-api-vs-ui  "user enables a Day2 bot and sees it become active"
```

It returns a verdict (API / UI / contract) + tags and tells you which `/add-*` prompt to run.

### 7.2 Add an API test (the common case)

**With Copilot (recommended):**

```
/add-api-test  "create a customer account, then retrieve it"      # or a Jira key, e.g. PRO-1234
```

The `e2e-test-author` agent loads the rules + templates, plans the files, and writes a declarative
`.feature`, thin step defs, a per-resource `httpx` client object, a Polyfactory factory, and
Allure-step assertions — fully tagged — then runs `ruff`/`mypy`/`pytest`.

**Manually:** follow the templates in
`.github/instructions/e2e-best-practices.reference.md` (§1–6). In dependency order:

1. **Model + factory** (`tests/support/models/`, `tests/support/factories.py`).
2. **Client object** (`tests/support/clients/<resource>_client.py`) — extends the Allure-wrapped
   `ApiClient`; encapsulates paths/serialization.
3. **Feature** (`tests/features/api/<journey>.feature`) — declarative; happy path + ≥1 negative;
   `Background` for auth; tags `@api @smoke`/`@critical`/`@regression`.
4. **Step defs** (`tests/step_defs/api/test_<journey>.py`) — thin glue; `parsers.parse`; call
   domain assertions.
5. Run `ruff check . && ruff format --check . && mypy && pytest tests/step_defs/api/test_<journey>.py`.

### 7.3 Add a UI test (thin, critical only)

```
/add-ui-test  "login, then the cost dashboard renders my data"    # or a Jira key
```

Uses the Playwright CLI/agent to find **role-based** locators on the live dev1 app, seeds state
**via the API** (never the UI), asserts structure with an **ARIA snapshot**
(`to_match_aria_snapshot`), and attaches screenshots/traces to Allure on failure. Templates: §7–9.

> ⚠️ Playwright `codegen` / Test Agents emit **TypeScript**. Output **must be materialized as
> Python `pytest-bdd`** step defs + page objects. Every locator self-heal must log a loud warning.

### 7.4 Add a contract / fuzz test (nightly)

```
/add-contract-test  customer_account        # or an endpoint group / tag, or "all"
```

Wires `schemathesis` against `E2E_OPENAPI_SPEC`, authenticated, scoped to an endpoint group,
excluding destructive ops on shared dev1. Marked `@contract` (nightly-only). Template: §10.

### 7.5 Review before you push

```
# In Copilot, switch to the e2e-test-reviewer agent (read + lint only)
```

It checks your diff against the layering rules + ban list and returns APPROVE / CHANGES
REQUESTED. Or run the gates yourself: `ruff check . && ruff format --check . && mypy`.

---

## 8. Tag taxonomy

One scheme drives three jobs: **what runs**, **what gates a PR**, **how the report groups**.

| Tag | Meaning | Used by |
|---|---|---|
| `@smoke` | fast must-pass checks | PR gate |
| `@critical` | business-critical journeys | PR gate |
| `@api` | API-level E2E | layer selection |
| `@ui` | UI E2E (browser) | layer selection |
| `@regression` | full regression set | nightly |
| `@contract` | schemathesis contract/fuzz | nightly |

Plus Allure `epic` / `feature` / `story` for leadership-readable grouping, and an `@allure.link`
to a Jira requirement on at least one scenario per feature.

- **PR gate:** `pytest -m "smoke or critical"`
- **Nightly:** `pytest -m "regression or contract"`

---

## 9. Project layout

```
Automation/
├── pyproject.toml            # deps + pytest/ruff/mypy config (single source of truth)
├── package.json              # Allure 3 CLI + Playwright CLI (Node tooling)
├── conftest.py               # root fixtures: settings, authenticator, api_client
├── .env.example              # env template (copy to .env; secrets out of repo)
├── AGENTS.md                 # agent source-of-truth (conventions, ban list, commands)
├── CONTRIBUTING.md           # Definition of Done + PR checklist
├── allure/                   # Allure 3 config, categories, known-issues, self-hosted history
├── scripts/triage.py         # AI failure triage (off the gating path)
├── .github/
│   ├── copilot-instructions.md
│   ├── instructions/         # e2e-best-practices.instructions.md (+ .reference.md templates)
│   ├── prompts/              # /add-api-test, /add-ui-test, /decide-api-vs-ui, /add-contract-test
│   ├── agents/               # e2e-test-author, e2e-test-reviewer
│   └── workflows/            # e2e-gate (PR) + e2e-nightly
└── tests/
    ├── features/  api/ ui/   # Gherkin (.feature) — declarative, stakeholder-readable
    ├── step_defs/ api/ ui/   # thin step definitions
    ├── support/              # config, auth, api_client, factories, assertions, pages/, clients/, models/
    └── contract/             # schemathesis wiring
```

---

## 10. Code quality

Test code is held to the **same bar as production code**.

```bash
ruff check .            # lint
ruff format --check .   # format (drop --check to auto-format)
mypy                    # strict type-checking
```

`pre-commit install` wires `ruff` + `mypy` to run on every commit. CI runs all three and fails
the build on any violation. Config lives in `pyproject.toml` (`[tool.ruff]`, `[tool.mypy]`).

---

## 11. CI/CD

GitHub Actions (`.github/workflows/`):

- **`e2e-gate.yml`** (on PRs) — `ruff` + `ruff format` + `mypy`, then `pytest -m "smoke or
  critical"`, then `allure generate`, uploads the report artifact. The hard gate is pytest's exit
  code.
- **`e2e-nightly.yml`** (cron 02:00 UTC + manual) — `pytest -m "regression or contract"`, restores
  Allure history, runs the triage script, uploads the report.

**Required GitHub secrets** (Settings → Secrets → Actions): `E2E_API_BASE_URL`, `E2E_UI_BASE_URL`,
`E2E_API_KEY`, `E2E_COGNITO_REGION`, `E2E_COGNITO_USER_POOL_ID`, `E2E_COGNITO_CLIENT_ID`,
`E2E_TEST_USERNAME`, `E2E_TEST_PASSWORD`, and (nightly) `E2E_OPENAPI_SPEC`, `E2E_LLM_*`.

---

## 12. AI failure triage

```bash
python scripts/triage.py --allure-results allure-results
```

Determinism gates; AI only accelerates triage. Allure 3 known-issues handles known/blocked items;
this script classifies only **new, unknown** failures (`regression | flaky | env | test-bug`). The
LLM provider is configurable via `E2E_LLM_*` and entirely optional — it never blocks the PR gate.

---

## 13. Troubleshooting & FAQ

| Symptom | Cause / fix |
|---|---|
| `no tests collected` | Expected in the skeleton — author a `.feature` (see §7). |
| `ModuleNotFoundError: tests.support` | Activate the venv and run `pip install -e .`. `pythonpath=["."]` is set in `pyproject.toml`. |
| `allure: command not found` | Run `npm install` (local) or `npm i -g allure`. Needs Node 18+. |
| `Executable doesn't exist … playwright` | Run `playwright install`. |
| Cognito `NotAuthorizedException` / `InvalidParameterException` | Check `E2E_TEST_USERNAME/PASSWORD`, ensure the user has **no MFA** and the app client has **USER_PASSWORD_AUTH** enabled. |
| schemathesis "spec not found" | Set `E2E_OPENAPI_SPEC` to a reachable OpenAPI 3.x spec. |
| `ruff`/`mypy` fail on commit | Run them locally and fix the root cause — they are not suppressed. |
| pytest can't find Python 3.11+ | Create the venv with `python3.12`/`python3.13`; the app's 3.7 is unrelated. |

**Why pytest + pytest-bdd (not duplicate)?** pytest-bdd is a *plugin on top of pytest* — one
runner. The `.feature` + step defs *become* pytest tests; there's no second copy.

**Why arrange-via-API?** dev1 is shared and DynamoDB has no easy rollback. Seeding via API with
namespaced/ephemeral data keeps tests independent and cleanable. Never seed through the UI.

---

## 14. Versions & compatibility

Pinned to **latest compatible**, verified resolvable (`uv pip install -e .`). See `pyproject.toml`.

| Package | Pin | Note |
|---|---|---|
| pytest | `>=8.3` → resolves to **9.1.1** | schemathesis 4.21 *requires* pytest ≥9; pytest-bdd 8.1 supports it |
| pytest-bdd | `>=8.1.0` | BDD layer (plugin on pytest) |
| pytest-playwright / playwright | `>=0.8.0` / `>=1.60.0` | UI E2E |
| httpx | `>=0.28.1` | API E2E |
| schemathesis | `>=4.21.0` | v4 — major rewrite from v3 |
| allure-pytest-bdd | `>=2.16.0` | emits Allure **2** results |
| **Allure 3 CLI** (npm `allure`) | `^3.12.0` | the v3 report generator |
| polyfactory / pydantic / pydantic-settings | `>=3.3.0` / `>=2.13.0` / `>=2.14.0` | data + config |
| ruff / mypy | `>=0.15.0` / `>=2.1.0` | quality bar |

**Open items to validate as tests land:** (1) Allure 3 rendering of `allure-pytest-bdd` results +
v3 config keys; (2) schemathesis→Allure reporting path; (3) the richer `E2E_OPENAPI_SPEC`.

---

## 15. Where to go next

- [`AGENTS.md`](AGENTS.md) — the conventions source-of-truth (read first when authoring).
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — Definition of Done + the ban-list PR checklist.
- `.github/instructions/e2e-best-practices.instructions.md` (+ `.reference.md`) — rules + templates.
- `.github/prompts/` — the `/add-*` and `/decide-api-vs-ui` authoring prompts.
