# Learning: The acceptance-evidence runner pastes a failing command under a 'passes' bullet by design; it is evidence, not a gate — the reviewer must read exit codes

## Summary
runPasteOutputItem treats a non-zero exit as 'a legitimate result worth pasting' (only binary-missing/timeout mark Not-verified). PR#5670's body carried 'make lint … Error 1' under a 'passes; paste the output' bullet and autopilot merged on green CI (CI pins golangci-lint 2.8.0; local 2.14.0 flags QF1012). Also: golangci-lint's shared cache leaks a dead sibling worktree's paths into a Pilot run's lint output; and the runner refuses '|' inside -run quotes and any command not in the allowlist (grep) — write acceptance commands without pipes and with allowlisted binaries.

## Context
Post-merge reviews of PR#5670/#5691/#5697 (2026-10-14).

## Details
runPasteOutputItem treats a non-zero exit as 'a legitimate result worth pasting' (only binary-missing/timeout mark Not-verified). PR#5670's body carried 'make lint … Error 1' under a 'passes; paste the output' bullet and autopilot merged on green CI (CI pins golangci-lint 2.8.0; local 2.14.0 flags QF1012). Also: golangci-lint's shared cache leaks a dead sibling worktree's paths into a Pilot run's lint output; and the runner refuses '|' inside -run quotes and any command not in the allowlist (grep) — write acceptance commands without pipes and with allowlisted binaries.

## Recommended Approach
Reviewer: scan pasted evidence for 'Error', 'FAIL', 'exit status' before trusting a green bullet. Author: no '|' in -run patterns, no grep in acceptance; prefer separate go test -run bullets. Product gap (not filed): flag exit≠0 under a 'passes' bullet in the PR body.

## Related
- TASK-545
- TASK-548
- TASK-552
- TASK-556
- `internal/executor/acceptance_evidence_run.go`

---
**Captured**: 2026-10-15
**Confidence**: 90%
**Concepts**: evidence-gate, review, lint, issue-authoring
