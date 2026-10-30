// Allure 3 configuration (npm package `allure`, CLI v3.x).
//
// The Python adapter (allure-pytest-bdd) writes Allure 2 result JSON into `allure-results/`;
// the Allure 3 CLI renders it. Apply this config with: `allure generate --config allure/allurerc.mjs`.
//
// Supported top-level keys (validated by @allurereport/core): name, output, plugins,
// environments, qualityGate, variables, defaultLabels, appendHistory, historyPath, historyLimit,
// knownIssuesPath, allowedEnvironments. (knownIssues / history are NOT valid keys — known-issues is handled by
// the e2e-failure-triage agent via Jira; history uses appendHistory + historyPath.)

export default {
  name: "MontyCloud E2E",
  output: "allure-report",

  // Self-hosted history/trends — no SaaS (EU + GOVCloud data-residency).
  appendHistory: true,
  historyPath: "allure/history/history.jsonl",

  // Bound the JSONL so it can't grow forever (one line per generate; ~5 KB per 100 tests).
  historyLimit: 60,

  // Known/blocked failures (by historyId) are labelled separately and excluded from the gate.
  knownIssuesPath: "allure/known-issues.json",

  // Contract results arrive as JUnit XML with no labels; tag them E2E like the rest of this
  // repo (conftest.py) so the Testing pyramid counts them.
  defaultLabels: { layer: "E2E" },

  // Reporting gate, run by `npm run report:gate` via allure/qualitygate.mjs (exits 1 on breach). Allure 3 rule shape: { <ruleName>: expected, filter?, id? }; rules are
  // maxFailures / minTestsCount / successRate / maxDuration. pytest's exit code stays the hard gate.
  qualityGate: {
    rules: [
      {
        id: "critical",
        maxFailures: 0,
        filter: (tr) => tr.labels.some((l) => l.name === "severity" && l.value === "critical"),
      },
    ],
  },

  // Failure buckets for triage, first match wins. Quarantined tests (tag @quarantine) are
  // listed on their own so a known-flaky failure is never mistaken for a new one.
  categories: [
    {
      name: "Quarantined (known flaky)",
      matchers: { statuses: ["failed", "broken"], labels: { tag: "quarantine" } },
    },
    {
      name: "Infrastructure / environment",
      matchers: { statuses: ["failed", "broken"], message: /ConnectError|Timeout|\b50[234]\b/ },
    },
    { name: "Product defects", matchedStatuses: ["failed"] },
    { name: "Test defects", matchedStatuses: ["broken"] },
  ],

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
