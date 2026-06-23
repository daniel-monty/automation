// Allure 3 configuration (npm package `allure`, CLI v3.x).
//
// The Python adapter (allure-pytest-bdd 2.16.x) writes Allure 2 result JSON into
// `allure-results/`; the Allure 3 CLI renders that into one combined report.
//
// ⚠️ VERIFY-DON'T-ASSUME: the exact config keys below (environments / qualityGate /
// knownIssues / history) must be validated against your installed Allure 3 version on
// the first real run: `npx allure generate allure-results`. Treat this as a template;
// adjust keys to match the CLI's reported schema before relying on the v3 features.

export default {
  name: "MontyCloud E2E",
  output: "allure-report",

  // One combined report; API and UI results separated + linked as environments.
  environments: {
    api: { matcher: { labels: [{ name: "layer", value: "api" }] } },
    ui: { matcher: { labels: [{ name: "layer", value: "ui" }] } },
  },

  plugins: {
    // Allure Awesome — the v3 report UI. Stakeholder-readable grouping.
    awesome: {
      options: {
        reportName: "MontyCloud E2E",
        groupBy: ["epic", "feature", "story"],
      },
    },
  },

  // PR gate: fail when critical-severity failures cross the threshold (0 = none allowed).
  // The hard PR gate is pytest's own exit code (CI); this is the reporting-side gate.
  qualityGate: {
    rules: [
      {
        type: "failRate",
        limit: 0,
        filter: { labels: [{ name: "severity", value: "critical" }] },
      },
    ],
  },

  // Known/blocked items labeled separately from new failures (sync from Jira where possible).
  knownIssues: "allure/known-issues.json",

  // Self-hosted history/trends — no SaaS (EU + GOVCloud data-residency posture).
  history: { path: "allure/history" },
};
