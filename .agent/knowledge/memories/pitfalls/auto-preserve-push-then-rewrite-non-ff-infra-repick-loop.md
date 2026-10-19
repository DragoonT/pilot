# Pitfall: Auto-preserve pushes a wip SHA, later steps rewrite it, and every infra re-pick collides with the stale pilot/<task> branch

## Summary
GH-5756 (2026-10-19): preserveDirtyWorktreeAsWIP committed and pushed 3d1fb36 to origin; the branch was rewritten before the final plain Push, so the push was non-fast-forward and the run ended status=infra. Each infra re-pick builds pilot/<task> fresh from origin/main, never fetches the remote branch, and hits the same rejection: 6 runs of ~15 min and ~0.40 USD each, until the operator deleted the remote branch. Cap is dispatcherInfraRepickCap=8.

## Context
TASK-576 leg A dispatch; diagnosed from daemon.log on the box; filed #5762. Sibling of auto-preserved-wip-recover-by-cherry-pick-continuation (that one covers recovering the wip commit; this one covers the push collision).

## Details
Sequence: result event with a still-running test sweep -> process group killed (GH-5530) -> worktree dirty -> auto-preserve commit+push -> quality gates adopt the wip SHA -> self-review + intent judge -> final Push sees remote_head=wip SHA, local_head=rewritten SHA -> rejected (GH-5730 does not retry non-FF) -> status=infra -> re-pick generation+1 from origin/main -> same rejection. No 'Stripped Co-Authored-By' line in the log, so the rewrite came from self-review/adoption, not stripCoAuthorBeforePush.

## Recommended Approach
Operator unblock: back up the remote commit locally (git fetch + git update-ref refs/backup/...), then git push --no-verify origin --delete pilot/<task> (the pre-push gate otherwise runs the full Go gate for a ref deletion). Product fix (#5762): lease-push against the SHA Pilot itself pushed (PushForceWithLease), and on re-pick base the worktree on origin/pilot/<task> or escalate on the first non-FF instead of re-running.

## Related
- [[auto-preserved-wip-recover-by-cherry-pick-continuation]] (sibling: recovery of the wip commit; its product fix #5445 / PR#5446 keys on the 'auto-preserved … needs manual review' failure string, which the #5722 adoption path never produces)
- #5762 (fix), #5445 / PR#5446 (earlier guard), #5722 (adoption finalizer)
- TASK-576
- `internal/executor/git_freshness.go`
- `internal/executor/git.go`
- `internal/executor/dispatcher.go`

---
**Captured**: 2026-10-19
**Confidence**: 95%
**Concepts**: executor, git, dispatcher
