# Pitfall: Autopilot self-close hand-off leaves the original task re-pickable: the dispatcher re-runs it into the fix run's branch

## Summary
When CI fails and autopilot closes the PR to hand the work to a fix issue (self-close marker, GH-5351/5362), recordExecutionEvent demotes the original's completed row to failed (GH-5067) and notifyExternalClose — the only writer of a superseded row — is skipped. HasTerminalCompletion is then false, nextRetryGeneration grants gen+1, and the original task runs again from scratch while the fix run owns the branch; its push is rejected, classed infra, and re-picked without the hard cap. GH-5731 ran three times on 2026-10-16 (13:31, 14:32, 15:11Z).

## Context
Queue check 2026-10-16 after PR#5733 went lint-red; board rows GH-5731 failed → infra → infra; daemon log 'dispatch re-pick: prior claim was terminal but task is not done'; box executions rows read 2026-10-17.

## Details
When CI fails and autopilot closes the PR to hand the work to a fix issue (self-close marker, GH-5351/5362), recordExecutionEvent demotes the original's completed row to failed (GH-5067) and notifyExternalClose — the only writer of a superseded row — is skipped. HasTerminalCompletion is then false, nextRetryGeneration grants gen+1, and the original task runs again from scratch while the fix run owns the branch; its push is rejected, classed infra, and re-picked without the hard cap. GH-5731 ran three times on 2026-10-16 (13:31, 14:32, 15:11Z).

## Recommended Approach
Stop it by hand: remove the pilot label from the original issue and edit the fix PR to Closes #<original>. Fix (TASK-573 / #5741): write a superseded row at the self-close sites (controller.go markSelfClosed callers) and put Closes #<source> in the fix issue body. Never re-label the original while an autopilot-fix issue with source:<N> in its footer is open.

## Related
- TASK-573
- TASK-569
- TASK-508
- `internal/autopilot/controller.go`
- `internal/memory/store.go`
- `internal/executor/dispatcher.go`
- `internal/autopilot/feedback_loop.go`

---
**Captured**: 2026-10-17
**Confidence**: 90%
**Concepts**: autopilot-fix, self-close, repick, superseded, dispatcher
