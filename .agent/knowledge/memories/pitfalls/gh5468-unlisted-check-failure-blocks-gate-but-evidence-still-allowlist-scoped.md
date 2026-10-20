---
name: gh5468-unlisted-check-failure-blocks-gate-but-evidence-still-allowlist-scoped
description: Since GH-5468 a failed check outside required_checks fails the CI gate, but the evidence collectors still drop unlisted checks via isScopedCheck — the PR is parked pilot-needs-human with "zero evidence gathered" although the log is one call away; hits every repo inheriting the global [test, lint] allowlist with its own checks (console PR#417, 2026-10-20); daemon fix #5776, box mitigation per-project required_checks: []
type: pitfall
---

# GH-5468 widened gate failure, not evidence scope → zero-evidence park

**What happened (2026-10-20 07:53Z, pilot-console PR#417 / GH-390):** "Check
Wire-Contract Tests" failed with a clear script message. daemon.log in one
second: `CI gate held: check-run(s) outside the required-checks allowlist
failed … (GH-5468) required_checks="[test lint]" failed_unlisted_checks="[Check
Wire-Contract Tests]"` → `CI failed` → `ci_failed`. One minute later:
`CI failure classification: zero evidence gathered class=unknown` →
`escalateAndHold … reason="CI failure with zero gathered evidence"
labels=[pilot-needs-human]`. The PR comment reads "no evidence could be
gathered from any check run".

**Why:** `GetFailedChecks`, `GetFailedCheckLogsByCheck`, `GetFailedCheckExcerpts`
(internal/autopilot/ci_monitor.go) all `continue` on `!isScopedCheck(name)`;
with a non-empty `requiredChecks` that returns false for every unlisted name.
GH-5468 made exactly those failures fail the gate. The console project on the
box has no per-project `ci_checks` block, so it inherits the global
`required_checks: [test, lint]` (tuned for the pilot repo); the other projects
set `required_checks: []`.

## Rules
- A `pilot-needs-human` with "zero evidence" on a repo that is not qf-studio/pilot:
  check `required_checks` inheritance first — the evidence is in the Actions log.
- Daemon fix: #5776 (one predicate for gate scope and evidence scope).
- Box mitigation now: add `ci_checks: {required_checks: []}` to pilot-console,
  pilot-console-ui, pilotcloud-site (operator config edit + reload).
- Related: `issue-body-backticked-paths-not-on-main-trip-base-presence-hold`
  (the other park class this week).
