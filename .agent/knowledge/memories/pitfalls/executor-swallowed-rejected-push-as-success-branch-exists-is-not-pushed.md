# Pitfall: Executor push loop (runner.go, GH-1389 shortcut) treated any push error as succe

## Summary
Executor push loop (runner.go, GH-1389 shortcut) treated any push error as success when a remote branch of that name existed; a non-fast-forward rejection on an autopilot-fix continuation (console GH-415 rebasing pilot/GH-403, 2026-10-16 09:34Z) was swallowed, the stale PR#408 adopted, 'Task completed successfully' logged, nothing pushed. The earlier continuation #5661 only worked because that session force-pushed itself. Rule: 'branch exists on remote' is not 'my commit is on remote'; forgive a failed push only when remote head == local HEAD, and push a rebased autopilot-fix continuation once with --force-with-lease on the footer SHA. Fixed by pilot#5729 → PR#5730 (TASK-563). Recovery when it happens on an old daemon: the session's commits survive in the box's project repo (/var/lib/pilot/repos/...), push them from the box as ec2-user with gh credentials and a lease on the old head.

## Context
Discovered during development.

## Details
Executor push loop (runner.go, GH-1389 shortcut) treated any push error as success when a remote branch of that name existed; a non-fast-forward rejection on an autopilot-fix continuation (console GH-415 rebasing pilot/GH-403, 2026-10-16 09:34Z) was swallowed, the stale PR#408 adopted, 'Task completed successfully' logged, nothing pushed. The earlier continuation #5661 only worked because that session force-pushed itself. Rule: 'branch exists on remote' is not 'my commit is on remote'; forgive a failed push only when remote head == local HEAD, and push a rebased autopilot-fix continuation once with --force-with-lease on the footer SHA. Fixed by pilot#5729 → PR#5730 (TASK-563). Recovery when it happens on an old daemon: the session's commits survive in the box's project repo (/var/lib/pilot/repos/...), push them from the box as ec2-user with gh credentials and a lease on the old head.

## Recommended Approach
Apply this knowledge when working on related topics.

## Related
- None documented

---
**Captured**: 2026-10-16
**Confidence**: 95%
**Concepts**: false-success, executor, git-push, autopilot-fix, continuation
