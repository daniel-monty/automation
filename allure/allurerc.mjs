// Allure 3 configuration (npm package `allure`, CLI v3.x).
//
// The Python adapter (allure-pytest-bdd) writes Allure 2 result JSON into `allure-results/`;
// the Allure 3 CLI renders it. Apply this config with: `allure generate --config allure/allurerc.mjs`.
//
// Supported top-level keys (validated by @allurereport/core): name, output, plugins,
// environments, qualityGate, variables, defaultLabels, appendHistory, historyPath,
// allowedEnvironments. (knownIssues / history are NOT valid keys — known-issues is handled by
// the e2e-failure-triage agent via Jira; history uses appendHistory + historyPath.)

export default {
  name: "MontyCloud E2E",
  output: "allure-report",

  // Self-hosted history/trends — no SaaS (EU + GOVCloud data-residency).
  appendHistory: true,
  historyPath: "allure/history/history.jsonl",

  // PR gate: fail when critical-severity failures occur (the hard PR gate is pytest's exit code).
  qualityGate: {
    rules: [
      {
        type: "failRate",
        limit: 0,
        filter: { labels: [{ name: "severity", value: "critical" }] },
      },
    ],
  },

  // Group the report tree by epic/feature/story (stakeholder-readable) instead of the
  // file path (which otherwise renders as "tests > features > api > ...").
  plugins: {
    awesome: {
      options: {
        reportName: "MontyCloud E2E",
        groupBy: ["epic", "feature", "story"],
        appendTitlePath: false,
        singleFile: true,
      },
    },
  },
};
