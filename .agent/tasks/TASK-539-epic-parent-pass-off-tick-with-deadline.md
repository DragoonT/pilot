# fix(autopilot): run the epicParent reconcilers off the controller tick with a deadline and a row cap

**Status**: 📋 Planned 2026-10-13
**Created**: 2026-10-13
**Repo**: qf-studio/pilot

Blocked by: none

## Context

Founder box, v2.282.0, 2026-10-13: the 16:00 train moved its carrier PR#5656 to releasing at 14:00:50Z and the qf-studio/pilot controller then logged nothing for 57 minutes. A SIGQUIT goroutine dump showed the Run goroutine of that controller inside the epicParentTicker select branch of `internal/autopilot/controller.go`, in reconcileReleaseBackfill, waiting on a GitHub compare. All seven reconcilers in that branch (reconcileEpicParents, reconcileClosedEpicScopes, reconcileLabelScopes, startPendingScopeReleases, reconcileReleaseBackfill, reconcileLaneStarvation, reconcileUnsourcedBoardIssues) run synchronously in the single Run goroutine with the bare run context, so a slow pass starves processAllPRs: no PR processing, no release, no merged-PR scan for that repo. The GH-5541 stage deadline (processPRWithDeadline) covers only the ticker.C branch. reconcileReleaseBackfill has no per-pass row cap and walks every StageFailed and StageReleasing row of the repo.

## Scope

- `internal/autopilot/controller.go`, the epicParentTicker case in Run: move the seven reconciler calls into a new method runEpicParentPass and run it in its own goroutine behind an inflight guard (skip the pass and log at debug when the previous pass still runs). Give each pass a context with timeout from EffectiveStageTimeout. When the deadline fires, log one WARN that names the reconciler that was running, increment a new counter autopilot_epic_parent_pass_timeouts_total on Metrics, and let the loop continue. Copy the guard ordering from processPRWithDeadline (clear the inflight guard, then signal done, then cancel) per GH-5554.
- Inside the pass, call each reconciler through a small helper that records the reconciler name as the current step, so the WARN can name it.
- `internal/autopilot/release_backfill.go`, reconcileReleaseBackfill: add a per-pass row cap (new constant maxReleaseBackfillRowsPerPass, value 5) and a ctx.Err() check at the top of each row iteration; also gate the sweep with backgroundScanAllowed("release_backfill") next to the existing platform breaker check.
- `internal/autopilot/metrics_alerter.go`: do not reuse RecordTick for the pass; add a separate liveness stamp so a stuck processAllPRs still trips tickStaleness.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go vet ./internal/autopilot/` passes; paste the output into the PR body.
- `go test ./internal/autopilot/ -run TestEpicParentPass -count=1` passes; paste the output into the PR body. Adds TestEpicParentPass_BlockedReconcilerDoesNotStallTick (a fake reconciler blocks on a channel; the Run loop still calls processAllPRs within two tick intervals; a second pass is skipped while the first is inflight) and TestEpicParentPass_DeadlineLogsAndCounts (the pass exceeds the stage timeout; one WARN names the reconciler; the counter increments once).
- `go test ./internal/autopilot/ -run TestReconcileReleaseBackfill -count=1` passes; paste the output into the PR body. Adds TestReconcileReleaseBackfill_RowCapPerPass (20 eligible rows, one pass touches at most 5) and TestReconcileReleaseBackfill_StopsOnCancelledContext.
- `go test ./internal/autopilot/ -run TestProcessAllPRs_StageDeadline -count=1` passes; paste the output into the PR body.
- run the epicParent pass inline instead of in its own goroutine -> TestEpicParentPass_BlockedReconcilerDoesNotStallTick fails
- remove the inflight guard from runEpicParentPass -> TestEpicParentPass_BlockedReconcilerDoesNotStallTick fails
- remove the per-pass row cap from reconcileReleaseBackfill -> TestReconcileReleaseBackfill_RowCapPerPass fails
- remove the ctx.Err() check from the row loop -> TestReconcileReleaseBackfill_StopsOnCancelledContext fails

## Out of scope

- The compare fan-out in earliestReleaseTagContaining (separate issue).
- Changing what the reconcilers do or their intervals.
- The ScanRecentlyMergedPRs branch (same class, lower risk; follow-up if it ever starves).

## Refs

- `internal/autopilot/controller.go` (Run select loop, processPRWithDeadline, EffectiveStageTimeout usage, backgroundScanAllowed)
- `internal/autopilot/release_backfill.go` (reconcileReleaseBackfill, releaseBackfillDue)
- `internal/autopilot/metrics_alerter.go` (tickStaleness)
- Tests: `internal/autopilot/gh5541_stage_deadline_test.go` (blocked-handler template), `internal/autopilot/release_backfill_test.go` (releaseBackfillServer, releaseBackfillClock)
- Precedents: GH-5541 stage deadline, GH-5554 guard ordering, GH-4919 backfill backoff
