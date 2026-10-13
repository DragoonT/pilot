# feat(autopilot): alert when the epic-parent reconciler pass goes stale, like tickStaleness does for the PR loop

**Status**: 🚀 Dispatched to Pilot 2026-10-13 → [#5664](https://github.com/qf-studio/pilot/issues/5664) (labels `pilot` + `no-decompose`)
**Created**: 2026-10-13
**Repo**: qf-studio/pilot

Blocked by: none

## Context

PR #5659 (issue #5657) moved the seven epic-parent reconcilers into their own goroutine with a per-pass deadline and an inflight guard, and added the gauge LastEpicParentPassAt in `internal/autopilot/metrics.go`. The guard clears only when the pass goroutine returns, so a reconciler that ignores its context keeps the guard forever: one WARN fires at the deadline and every later tick only logs at debug that the pass is skipped. Nothing alerts. The PR loop has tickStaleness in `internal/autopilot/metrics_alerter.go` for exactly this failure shape; the pass needs the same.

## Scope

- `internal/autopilot/metrics_alerter.go`: add epicPassStaleness(lastPass, interval, stageTimeout, now) next to tickStaleness with the same shape (age, limit, stale) and a limit of three times the epic-parent interval (CIPollInterval) plus the stage timeout. In the alerter's periodic evaluation read LastEpicParentPassAt from the metrics snapshot, add the three values to the autopilot metrics alert event fields (epic_pass_age_sec, epic_pass_limit_sec, epic_pass_stale) and raise the same severity path tickStaleness uses when stale. A controller that has never run a pass (zero time) is not stale during the first limit window after start.
- `internal/autopilot/metrics.go`: expose LastEpicParentPassAt in the Snapshot the alerter reads, if it is not already there.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go vet ./internal/autopilot/` passes; paste the output into the PR body.
- `go test ./internal/autopilot/ -run TestEpicPassStaleness -count=1` passes; paste the output into the PR body. Table cases: fresh pass not stale, pass older than the limit stale, zero time inside the start window not stale, zero time past the start window stale.
- `go test ./internal/autopilot/ -run TestMetricsAlerter -count=1` passes; paste the output into the PR body. Adds TestMetricsAlerter_EpicPassStaleRaisesAlert.
- raise the staleness limit to one hour -> TestEpicPassStaleness fails
- drop the epic_pass_stale field from the alert event -> TestMetricsAlerter_EpicPassStaleRaisesAlert fails

## Out of scope

- Changing runEpicParentPass or the inflight guard semantics.
- Dashboard panels.

## Refs

- `internal/autopilot/metrics_alerter.go` (tickStaleness, the alert event fields), `internal/autopilot/metrics.go` (LastEpicParentPassAt, Snapshot), `internal/autopilot/metrics_alerter_test.go`
- PR #5659 review note on the silent-after-one-WARN consequence
- Pilot issue: https://github.com/qf-studio/pilot/issues/5664
