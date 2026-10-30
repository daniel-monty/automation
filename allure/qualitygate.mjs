// Config for `allure quality-gate` only. Allure 3.13 exits 0 silently (gate never evaluated) when
// the config sets historyPath, so the gate reads just the rules from allurerc.mjs.
// TODO: drop this file and pass allurerc.mjs once upstream fixes quality-gate + history.
import config from "./allurerc.mjs";

export default { qualityGate: config.qualityGate, knownIssuesPath: config.knownIssuesPath };
