# TASK-594: direct mode (no worktree) — stale-branch cleanup deletes the branch the clone is checked out on, so every retry after a closed PR fails until the repick cap parks the task

**Status**: ✅ Merged 2026-10-26 — #5829 → PR#5870. Post-merge review posted 2026-10-27 **APPROVE-WITH-NOTES** (real-git table test, pin holds; notes: no recovery ref for committed work on the discarded branch, swallowed GetCurrentBranch error, silent detach). No follow-up.
**Spec refs**: #912 (stale local branch handling — the delete-then-recreate step this task fixes), #4594 (the EnsureBranchFromOrigin rewrite that kept the delete step), #5769 (lease-push over the run's own auto-preserve SHA — nearby, different path), TASK-421 (repick hard cap).
**Origin**: external report by @scrappydog (2026-10-22, v2.289.0). Verified against main at v2.295.0.

## Context

With worktrees off (`useWorktree=false`), the runner executes in the project clone and calls `EnsureBranchFromOrigin` (`internal/executor/git.go`) for the task branch. Nothing in direct mode ever switches the clone off `pilot/GH-N` after the task ends, so after a PR is closed unmerged the clone is still on that branch when the issue is re-picked. `EnsureBranchFromOrigin` decides the branch is stale (behind the base ref), calls `DeleteBranch` (`git branch -D`) with no check of the current HEAD, git refuses because the branch is checked out, and the runner aborts with "branch creation failed, aborting execution". The error is byte-identical on every re-pick, so `consecutiveIdenticalFailureThreshold` (2) fires, the task is marked stalled, `pilot-blocked` is added, and the re-arm sweep later adds `pilot-needs-human`. `CreateOrResetBranchFromOrigin` (`git checkout -B`) already exists in the same file and resets a branch in place, checked out or not. `GetCurrentBranch` and `HasUncommittedChanges` exist and are unused on this path.

## Legs — pilot (daemon)

### LEG B2 — repo: qf-studio/pilot — title: fix(executor): direct mode stale-branch cleanup must not run git branch -D on the branch the clone is checked out on — retry after a closed PR fails deterministically until the repick cap parks the task

## Context
Reported by @scrappydog on v2.289.0 (original report in this issue's edit history). Worktrees off, GitHub poller, max_concurrent 1. A task runs in the project clone on branch pilot/GH-N and opens a PR. The PR is closed without merge; Pilot adds pilot-retry-ready and re-picks. Branch creation then fails on every re-pick:

```
level=INFO  msg="Worktree condition check" component=executor allowWorktree=true configNotNil=true useWorktree=false branch=pilot/GH-N directCommit=false
level=ERROR msg="Task execution failed" component=dispatcher task_id=GH-N error="branch creation failed, aborting execution: failed to delete stale branch pilot/GH-N: failed to delete branch: exit status 1: error: cannot delete branch 'pilot/GH-N' used by worktree at '~/.pilot/repos/<repo>'"
level=WARN  msg="repick cap reached — task marked stalled, no further automatic retries" component=dispatcher task_id=GH-N generation=3 reason="consecutive identical failures (will not retry): branch creation failed, ..."
```

The issue then gets the "Pilot stopped retrying (repick hard cap)" comment and pilot-blocked, later pilot-needs-human. The clone was clean and on pilot/GH-N. Checking out the default branch by hand and re-adding pilot-retry-ready made the next re-pick succeed.

Verified cause (main at v2.295.0): in direct mode the runner (`internal/executor/runner.go`, the useWorktree false branch) calls EnsureBranchFromOrigin in `internal/executor/git.go`. When the branch exists and is behind the base ref, EnsureBranchFromOrigin calls DeleteBranch, which runs git branch -D with no check of the current HEAD; git refuses to delete the checked-out branch. Nothing in direct mode switches the clone back to the default branch after a task, so the retry always starts on the branch it must delete. The error text is identical on each attempt, so the dispatcher's identical-failure rule (threshold 2) parks the task. The same file already has CreateOrResetBranchFromOrigin (git checkout -B branch baseRef), which resets a branch in place whether or not it is checked out, plus GetCurrentBranch and HasUncommittedChanges.

probe: present qf-studio/pilot failed to delete stale branch
probe: present qf-studio/pilot func \(g \*GitOperations\) GetCurrentBranch
probe: present qf-studio/pilot func \(g \*GitOperations\) HasUncommittedChanges
probe: absent  qf-studio/pilot checked out in the clone, refusing

## Scope
- In EnsureBranchFromOrigin's stale path, before DeleteBranch: call GetCurrentBranch. If it equals branchName, call HasUncommittedChanges; if dirty, return an error whose text contains "checked out in the clone, refusing" and names the branch, so the operator sees the real cause instead of git's message. If clean, detach HEAD at baseRef (git checkout --detach baseRef), then delete and recreate as today. Branches that are not checked out keep the current behaviour.
- Keep the existing stale decision (behind the base ref) unchanged; this task only fixes what happens once the branch is declared stale.
- Do not touch worktree mode, CreateOrResetBranchFromOrigin, or the repick cap.

## Acceptance
- [ ] Table test in `internal/executor/git_test.go` on a temp repo with a real origin: check out pilot/GH-N, advance origin main, call EnsureBranchFromOrigin — it returns created true, HEAD is on the recreated branch at the new base, no error.
- [ ] Same table: a dirty tree on the checked-out stale branch returns an error containing "checked out in the clone, refusing" and leaves the branch and the dirty file untouched.
- [ ] Same table: a stale branch that is not checked out behaves as before (delete + recreate).
- [ ] remove the GetCurrentBranch check before DeleteBranch -> TestEnsureBranchFromOrigin_StaleCheckedOutBranchIsRecreated fails
- [ ] `go test -race ./internal/executor/ -run TestEnsureBranchFromOrigin` passes; paste the output into the PR body.
- [ ] Do not re-run make build, make test or make lint as evidence: the daemon's quality gates already run them on this repo (21–36 min on the box), and a second run overruns the 1-hour task budget before the PR is created.

## Out of scope
- Switching the clone back to the default branch at the end of every direct-mode task (a separate hygiene change; this fix makes the retry correct regardless).
- Worktree mode and the re-pick lease over a stale remote head (#5864).
- The identical-failure threshold or the pilot-needs-human sweep.

## Refs
- B2 → https://github.com/qf-studio/pilot/issues/5829
- Pilot issue: https://github.com/qf-studio/pilot/issues/5829 (reporter @scrappydog; original text in the edit history)
- Prior work on this path: #912 (stale branch delete), #4594 (EnsureBranchFromOrigin), #5769 (lease-push)

**Last Updated**: 2026-10-26
