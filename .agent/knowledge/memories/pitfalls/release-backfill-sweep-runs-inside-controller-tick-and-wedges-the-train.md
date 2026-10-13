---
name: release-backfill-sweep-runs-inside-controller-tick-and-wedges-the-train
description: reconcileReleaseBackfill (+ the other epicParentTicker reconcilers) runs synchronously inside Controller.Run's select tick with no context deadline; earliestReleaseTagContaining does one CompareStatus per tag oldest-first (up to 100 tags, 903 tags on pilot) per failed/releasing row, so one sweep can take hours and the controller for that repo stops ticking: no PR processing, no release, no merged scan. Train 2026-10-13 16:00 never tagged PR#5656 ('releasing' 57 min). Diagnose: controller logs nothing at all for that repo; SIGQUIT dump (stderr goes to daemon-stderr.log) shows Run → reconcileReleaseBackfill → CompareStatus.
type: pitfall
---

# The release-backfill sweep runs inside the controller tick and can wedge the train

**Found 2026-10-13 (founder box, v2.282.0):** the 16:00 train enqueued a scope release with one member (PR#5656, docs-only), the carrier passed post-merge CI and moved to `releasing` at 14:00:50Z, and then the qf-studio/pilot controller logged nothing for 57 minutes: no `processing active PRs`, no merged-PR scan, no release. Other repos' controllers kept running. pilot-board showed the row stuck at `releasing`.

**Root cause (SIGQUIT goroutine dump, `kill -QUIT` writes it to the daemon's stderr file `daemon-stderr.log`, then the process exits):** goroutine of `Controller.Run` for the pilot repo was inside the `epicParentTicker` select branch (`internal/autopilot/controller.go` ~9749-9760): `reconcileReleaseBackfill` → `healReleaseBackfillRow` → `earliestReleaseTagContaining` → studio-sdk `CompareStatus` → WithRetry → http2 roundTrip. That branch runs synchronously in the same loop as `processAllPRs`, with the daemon root context (no deadline). `earliestReleaseTagContaining` lists up to 100 tags, sorts ascending and calls `CompareStatus` once per tag from the OLDEST until a match; the pilot repo has 903 tags; the sweep walks every StageFailed/StageReleasing row (`LoadAllPRStates`) subject to a per-row backoff. One pass can take hours; the tick never returns; the release handler never runs.

**Why it looked like a deadlock:** zero log lines from that controller, process at 0% CPU, no stage-deadline WARN (the deadline only wraps `processPRWithDeadline`, not the reconcilers). Delve cannot attach to the stripped release binary. The static scans for mutex holders found nothing because nothing held a mutex.

**Fix:** TASK-539 — per-pass context deadline and call cap for the epicParent reconcilers (or run them off the tick goroutine), newest-first / binary-search compare in `earliestReleaseTagContaining` with a per-row cap, WARN when a tick exceeds N s.

**Mitigation that works today:** flag the orphaned row `release_backfill_abandoned=1` in autopilot_pr_state (python3 sqlite3 over SSM; sqlite3 CLI is not on the box), then restart; the sweep skips abandoned rows (`reconcileReleaseBackfill`). Note the restarted daemon enters the epicParent branch before the first PR tick, so one full walk still happens if the row is not flagged BEFORE the restart.

**How to apply:** when a repo's autopilot "stops" with no log lines at all, suspect a synchronous reconciler inside the Run tick before suspecting locks. Get a goroutine dump: the box daemon's stderr is a file, `kill -QUIT <pid>` dumps and exits, the operator restarts in tmux (`~/start-pilot.sh`). Never add long GitHub walks to the tick branch without a deadline.
