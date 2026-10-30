# TODO

## Fill the Testing pyramid with unit and integration results

**Goal:** the Allure report's Testing pyramid shows real `unit` / `integration` / `e2e` layers.
This repo fills `e2e` only (`layer=E2E` on every test). Unit and integration tests live in the
platform repo (pytest) and the UI repo (Jest). Both repos stay in sync on their `dev` branch,
which is what dev1 runs, so their results can describe the same code as our E2E run.

### Answer these first

1. **Does the platform repo have integration tests yet?** If not, the `integration` layer stays
   empty until it does. That's fine, but say so in the README.
2. **How does dev1 record which `dev` commit is deployed?** Options: a deployment record in
   GitHub, a git tag, a `/version` endpoint. The nightly needs it to pull results for the
   *deployed* commit, not just the latest run.
3. **One report or two?** Either merge everything into this report, so the pyramid fills
   here, or build a separate overview report next to it, which keeps the E2E report for QA
   triage only. Recommended: merge, but scope the E2E-only features (gate, triage, categories)
   to `layer=E2E` (see "This repo" below).
4. **Access:** a fine-grained token or GitHub App with `actions:read` on both repos, stored here
   as a secret (e.g. `RESULTS_READ_TOKEN`).

### Platform repo (pytest), done by its owners

- [ ] Add `allure-pytest` to dev dependencies.
- [ ] Keep unit and integration results apart: either two runs (`--alluredir=allure-unit`,
      `--alluredir=allure-integration`), or one run that labels each test in `conftest.py`:

      ```python
      def pytest_collection_modifyitems(items):
          for item in items:
              layer = "integration" if item.get_closest_marker("integration") else "unit"
              item.add_marker(allure.label("layer", layer))
      ```

- [ ] On push to `dev`, upload the results as an artifact named `allure-unit` /
      `allure-integration` (or one `allure-results`), kept for at least 7 days.

### UI repo (Jest), done by its owners

- [ ] Add `allure-jest` (JSON results, not `jest-junit`; see the pitfall below).
- [ ] On push to `dev`, upload `allure-results` as an artifact named `allure-unit`, kept for at
      least 7 days.

### This repo

- [ ] **Nightly: find the deployed commits.** Get each repo's deployed `dev` SHA (question 2).
- [ ] **Download that commit's results:**

      ```bash
      run=$(gh run list --repo <org>/<platform> --branch dev --commit "$PLATFORM_SHA" \
        --workflow <ci.yml> --status success --json databaseId --jq '.[0].databaseId')
      gh run download "$run" --repo <org>/<platform> -n allure-unit -D external/platform-unit
      ```

      Same for `allure-integration` and the UI repo.
- [ ] **Stamp the layer by source**, if the other repos don't label their results: a few lines
      of Python that add `layer=unit` or `layer=integration` to every `*-result.json` in each
      downloaded folder that has no layer label yet.
- [ ] **Generate from all folders:** `allure generate allure-results external/* --config ...`.
- [ ] **Show the commits in the report header:** add `PLATFORM_COMMIT` and `UI_COMMIT` to the
      `environment.properties` written by `conftest.py` (or a small step in the nightly).
- [ ] **Keep E2E-only features E2E-only:**
  - quality gate: add `layer === "E2E"` to the `critical` rule's filter in `allurerc.mjs`;
  - categories: add a first rule "Unit / integration failures" matching
    `labels: { layer: /^(unit|integration)$/ }`, so they don't land in "Product defects";
  - `e2e-failure-triage` agent: triage only `layer=E2E` results, and list unit/integration
    failures separately for their owners;
  - quarantine stays E2E-only (README §8.1).
- [ ] **Fail soft:** if an artifact is missing, expired or for a different SHA, still generate the
      report, and add a warning to the run summary (`$GITHUB_STEP_SUMMARY`). Never fail the
      nightly over another repo's results.
- [ ] **Docs:** README §6 (report) and §11 (CI), plus `.env.example` / required secrets.

**Pitfall:** `allurerc.mjs` sets `defaultLabels: { layer: "E2E" }` so our label-less contract
JUnit results count as E2E. Any other label-less results (e.g. `jest-junit` XML) would be
counted as E2E too. Use Allure JSON from the other repos, or stamp their layer before
generating.

**Done when:** the nightly report's pyramid shows non-zero `unit` (and `integration`, once it
exists) for the deployed `dev` commits, the header shows those commits, and unit failures
don't affect the quality gate, the triage agent or the "Product defects" category.

---

## Still to do from the staff-QA review

- [ ] **Trigger smoke tests on app deploy** (P1 #6): the app's deploy pipeline sends a
      `repository_dispatch`, and this repo runs the PR-gate subset against dev1.
- [ ] **Publish reports to a URL + notify** (P1 #10): S3 static site in the right region
      (also makes history durable beyond the 7-day Actions cache), plus a Slack/Teams message
      on nightly failure.
- [ ] **Jira links from tags** (P1 #11): an Allure link pattern so `@PRO-1234` becomes a link.
- [ ] **More environments** (P1 #12): staging / production-smoke / region selection.
- [ ] **P2:** axe accessibility checks on critical pages, Firefox/WebKit in nightly, a
      `Scenario Outline` example in the reference templates.

## Setup still needed for what's already built

- [ ] Create the `E2E_TEST_USERS` users on dev1 (no MFA, permanent password) and add the GitHub
      secret.
- [ ] Set `E2E_OPENAPI_SPEC` to the real spec, or the nightly contract step skips.
- [ ] Register a `sweep_stale` in `tests/support/sweep.py` for the first creatable resource.
