# TASK-602: stale-reap liveness — pin the runner→dispatcher wiring, log the skip at Info, add CompletedExecutionID to the completion invariant

**Status**: 🚀 Dispatched 2026-10-27 → pilot#5883 (`pilot`+`no-decompose`+`bug`), from the post-merge review of PR#5881 (GH-5878), notes 1, 5 and 6.
**Spec refs**: TASK-599 / #5878, PR#5881 review comment (APPROVE-WITH-NOTES), TASK-574 (same class: call site untested).
**Origin**: post-merge review 2026-10-27 — own read + independent second read + `go test -race` + four mutation pins (M2 fails as required; M1/M3/M4 survive).

## Why
- M3 survived: `NewDispatcher` installs the runner as `liveness` only when non-nil; both new tests overwrite `d.liveness` with a fake, so the wiring line is unpinned.
- The skip line is Debug; the daemon default is Info, so the next incident's log cannot show why an old row survived.
- `CompletedExecutionID` copies the `HasCompletedExecution` predicate but sits outside `TestTaskCompletionInvariant` (`internal/executor/task_completion_invariant_test.go`); the `store.go` doc comment names a non-existent `internal/integration/` path.

## Legs — pilot (daemon)

### LEG L1 — repo: qf-studio/pilot — issue #5883
Body as filed (Context / Scope / Acceptance / Out of scope). Path pre-flight re-run after one wrong path (internal/integration/…) was caught and edited out before pickup.

## Review notes carried from PR#5881 (no action)
- Liveness keyed by task id only is **correct**: `PruneOrphanedWorktreeForTask` has no project scoping; a per-project key would prune another project's live worktree. Cross-project same-number ids only delay a reap.
- CLI runs (`pilot task run`) are unprotected against a daemon on the same DB — the heartbeat column, out of scope.
- M1 survived because `deleteOrphanRunningRow`'s second guard and the pre-existing `hasLiveWorker` cover the tested cases.
- `AND id != ?` is logically redundant (reaped rows are `running`).

## Refs
- https://github.com/qf-studio/pilot/issues/5883
- https://github.com/qf-studio/pilot/pull/5881#issuecomment-6438461457
