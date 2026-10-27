# Pitfall: the agent may run `gh pr create` itself — the reconciler adopts that PR and autopilot merges it on CI alone, then the stale-running reaper prunes the live worktree under the still-running gates

## Summary
The gh guard allows `gh pr create` on the agent's own branch (policy.go, "pr create on current branch") and the prompt only forbids mutations on *other* issues/PRs. On 2026-10-26 the GH-5862 session opened PR#5874 ten seconds before "Task completed"; the autopilot reconciler adopted the untracked PR within a minute and merged it on green CI at 19:59 while the executor's gates were still running. The merge marked the claim row completed; six minutes later `recoverStaleRunningTasks` (any running row older than 30 min is a crash candidate) hit the `HasCompletedExecution` shortcut — checked before `hasLiveWorker` and never against the runner's `IsRunning` — deleted the live execution row and pruned the worktree. Gates finished in a deleted directory; judge, self-review ("fork/exec /usr/bin/claude: no such file" = cwd gone), contract evidence and the commit-count guard all failed; the run ended `failed` on a shipped ticket. Three untracked PRs were adopted that day (auth-service 544, 571; pilot 5874).

## Context
Founder: "check again, 5862 failed" after the outcomes chart showed a red row for a merged ticket. Diagnosed from PR#5874's author/body/createdAt (10 s before Task completed, agent-written body), the recording's `gh pr create` line, and daemon.log 19:33–20:07.

## Details
- Signature: PR createdAt before the run's "Task completed"; "reconciler: adopting untracked open PR" for a pilot/GH-N branch with a running execution; later "Deleting orphan running row (task already completed)" + "Pruned orphaned task worktree" while gates are mid-run; then a burst of chdir/no-such-file failures at the same second.
- What an agent-opened PR bypasses: quality gates, intent judge, self-review, contract evidence, acceptance evidence, the PR-body evidence block. CI is the only check before merge.
- The 30-minute stale rule alone marks every complex run a crash candidate (gates take 20–36 min on the box); the check order is the only protection.

## Recommended Approach
- Durable fix: TASK-599 — G1 deny `gh pr create|merge|close` in ghguard + a prompt line; G2 consult `Runner.IsRunning` before the completed shortcut, and never prune a worktree or reap a claim of a live execution.
- Until it ships: when an "adopting untracked open PR" line names a branch whose task is still running, expect the gates to be bypassed; review that PR by hand. A `failed` row with "failed to verify commit count … chdir /tmp/pilot-worktree-…: no such file" after a merge is this class, not a product failure.

## Related
- evidence-rerun-of-quality-gates-blows-task-budget-pr-create-on-dead-ctx
- completed-row-without-live-execution-polled-forever-as-stalled
- bug_child_push_pr_silent_stranding
