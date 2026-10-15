# Pitfall: Executor session ends its turn while a background test run is still active — nothing committed, run fails as a dirty no-op

## Summary
GH-5701 (2026-10-15): the session staged all work, launched go test -short -race with run_in_background, polled with an until-grep loop that hit the Bash timeout, then ended its turn with 'once it reports I will commit'. In headless -p mode there is no next turn: the result event fired, the background go test kept the process alive, the executor killed the group after the 30s grace (GH-5530), the harvested SHA equalled main (no-op), the dirty worktree was auto-preserved as a wip commit on pilot/GH-5701, and the task went stalled + pilot-blocked as a deterministic failure. The preserved commit was complete and green; recovery = verify on a detached worktree and open the PR from it (PR#5702).

## Context
Queue check after dispatching TASK-557; daemon log + recording TG-1792061946748 on the box.

## Details
Chain: run_in_background go test (11:09:10) -> until-grep wait loop times out -> turn ends 11:10:01 with staged, uncommitted work -> process alive after result -> killed 11:10:31 -> 'harvested SHA already on base' -> 'worktree had uncommitted work at no-op classification' -> auto-preserved 8fe4dd2, pushed -> repick cap, stalled, pilot-blocked. The uncommitted work came from the session itself (deferred git commit), not from another process. Product gap: an auto-preserved commit that builds and passes tests is treated as a deterministic failure instead of continuing the pipeline (quality gates -> PR).

## Recommended Approach
Diagnose from the recording: the RESULT text names the deferred commit; grep run_in_background in stream.jsonl for the backgrounded command. Recovery: fetch pilot/GH-N, git worktree add --detach, gofmt/build/vet/test, then open the PR from the preserved commit (Pilot's own comment recommends it). Prevention candidates: executor prompt rule 'commit before any long test run; never background a test run and end the turn'; executor: when the result arrives with the process alive AND the worktree is dirty, send one continuation turn ('commit now') before the kill; or treat a green auto-preserved commit as the deliverable and continue to gates + PR.

## Related
- TASK-557
- `internal/executor/claudecode.go`
- `cmd/pilot/handlers.go`

---
**Captured**: 2026-10-15
**Confidence**: 95%
**Concepts**: executor, worktree, recovery, stalled, silent-failure, claude-code-integration
