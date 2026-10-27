# TASK-607: executor — a killed self-review leaves uncommitted edits in the direct-mode clone; every later task fails git_clean

**Status**: ✅ BOTH MERGED 2026-10-27 — A1 pilot#5900 → PR#5902 (18:50Z, reviewer APPROVE-w-notes: killed-with-success edge may skip the PR note · test names differ from the issue pins) · A2 pilot#5901 → PR#5904 (19:47Z, reviewer APPROVE-w-notes: untracked-files note is WRONG, ResetHardToCommit runs git clean -fd · no consumer of the new preflight_self_heal event yet). #5865 closed. Was: 🚀 DISPATCHED 18:00Z — A1 → pilot#5900 (running 18:00Z) · A2 → pilot#5901 (`pilot` label REMOVED until #5900 merges: the first filing carried a literal ref, the dependency did not hold it and it queued behind #5900; re-add `pilot` after the A1 merge). Both `no-decompose`.
**Spec refs**: pilot#5865 (scrappydog, v2.289.0, macOS direct mode, Claude Code backend); SOP `.agent/sops/onboarding/new-project-issue-authoring.md` Rules 3b/3c/5b/5d.
**Origin**: external bug report 2026-10-26. Reporter: 77 of ~150 self-reviews SIGKILLed at exactly 120 s; 4 left an edit; each blocked the project queue until a hand clean.

## Why (verified at main)
- `selfReviewTimeout()` in `internal/executor/runner.go` returns a fixed 2m for Claude Code (10m OpenCode); no config key. Applied at the `reviewCtx` in `runSelfReview`.
- The self-review prompt allows edits ("FIX the issue by making the required changes"). Nothing commits or resets after the phase, on success or on failure; the failure branch logs "Self-review failure is not fatal - log and continue" and the flow goes on to lint, push and PR.
- The only direct-mode reset is the defer near runner.go:4740, which returns early when the run succeeded. A PR-created run is a success, so the dirt stays. Worktree mode discards the whole worktree, so the bug is direct-mode only.
- `finish_tripwire_root_clean` detects the dirt and alerts; it never resets.
- Pre-flight `git_clean` (`internal/executor/preflight.go`) runs `git status --porcelain` with no recovery. The stale-branch path in `internal/executor/git.go` also refuses on a dirty clone, so branch recreation is blocked too.
- Not on our box: 0 git_clean failures, ~1 self-review kill a day. The root-clean tripwires today on auth-service are `.claude/settings.json` from the hooks bootstrap, a different leak (not in scope here).

## Legs — pilot (daemon)

### LEG A1 — repo: qf-studio/pilot — title: fix(executor): self-review leaves the direct-mode clone clean on every exit, and the self-review timeout is configurable
probe: present qf-studio/pilot func \(r \*Runner\) selfReviewTimeout\(\)
probe: present qf-studio/pilot Self-review failure is not fatal
probe: absent  qf-studio/pilot self_review_timeout
probe: absent  qf-studio/pilot EffectiveSelfReviewTimeout

## Context

Reported as #5865. In direct mode the project clone is the working tree. The self-review phase (runSelfReview in `internal/executor/runner.go`) runs the backend under a hard-coded 2-minute context for Claude Code (selfReviewTimeout, 10 minutes for OpenCode). The prompt tells the session to fix what it finds, so the session edits files. Nothing commits or resets those edits afterwards: on success the caller continues to the intent judge, lint, push and PR; on error the branch logs "Self-review failure is not fatal - log and continue" and does the same. When the 2-minute cap kills the session (SIGKILL after context cancellation, exit 137) mid-edit, the edit stays in the clone. The push carries only committed HEAD, so the PR does not contain it. The only direct-mode reset is the deferred cleanup that returns early when the run succeeded, so a run that created a PR leaves the clone dirty. The next task on that project fails the git_clean pre-flight, and so does every later one. Worktree mode is unaffected because the worktree is discarded.

The reporter saw 77 of about 150 self-reviews killed at exactly 120 s on multi-file changes; four left edits; each one wedged the project queue.

## Implementation

1. Tree hygiene after self-review, on every exit. In the caller of runSelfReview (the goroutine join near the intent judge), after the phase returns — success, error, or timeout — and only in direct mode (not when UseWorktree is set): run git status --porcelain on the execution path. If the tree is dirty, commit the self-review edits on the task branch with a message like "chore(self-review): apply self-review fixes" when the phase reported REVIEW_FIXED and the session was not killed; otherwise reset the tree to HEAD with the existing ResetHardToCommit helper in `internal/executor/git.go` (it already excludes the Navigator and scaffold paths). Log one Info line stating which happened, the file count, and the reason (committed / discarded-killed / discarded-failed). Use a fresh short context for the git calls, not the expired review context.
2. When the self-review session was terminated (error type shutdown_terminated or the context deadline), record it on the result so the PR body carries one line under the self-review section: "Self-review was terminated after Ns; its edits were discarded." Add the same fact to the task-completion log line.
3. Configurable timeout. Add a self_review_timeout duration to the backend config block (file `internal/executor/backend.go`), with an EffectiveSelfReviewTimeout method modelled on EffectiveFinalizeTimeout: zero or unset keeps today's defaults (2m Claude Code, 10m OpenCode); a set value applies to every backend. selfReviewTimeout in runner.go reads it. Validate non-negative in `internal/config/config.go` where the backend block is validated. Document the key in `configs/pilot.example.yaml` next to finalize_timeout, with the 120 s history in the comment.
4. Tests: table-driven, in the executor package. Fakes that stub the backend must read their arguments (the mocks CI gate rejects fakes that ignore them): the fake self-review backend writes a file into the execution path and then returns the terminated error, or returns success with REVIEW_FIXED.

## Acceptance

- After a self-review that returns the shutdown_terminated error in direct mode, the execution path has no staged or unstaged diff, and the log carries the discarded-killed line.
- After a self-review that returns REVIEW_FIXED with edits in direct mode, the edits are committed on the task branch before push, and HEAD moved by one commit.
- In worktree mode the new hygiene step does not run.
- A config with self_review_timeout set to 7m makes selfReviewTimeout return 7m for Claude Code; unset keeps 2m; a negative value fails config validation with a message naming the key.
- `go test -race ./internal/executor/ -run TestSelfReviewTreeHygiene` passes; paste the output into the PR body.
- `go test -race ./internal/executor/ -run TestEffectiveSelfReviewTimeout` passes; paste the output into the PR body.
- remove the reset call on the killed branch -> TestSelfReviewTreeHygiene_KilledReviewDiscardsEdits fails
- make selfReviewTimeout ignore the configured value -> TestEffectiveSelfReviewTimeout_ConfiguredOverridesDefault fails
- remove the UseWorktree guard so the hygiene step also runs in worktree mode -> TestSelfReviewTreeHygiene_WorktreeModeSkipped fails

## Out of scope

- Pre-flight self-heal of an already-dirty clone (separate issue, depends on this one).
- The hooks bootstrap writing .claude/settings.json into the clone root (different leak).
- Changing what the self-review prompt may do.

## Refs

- #5865

### LEG A2 — repo: qf-studio/pilot — title: fix(executor): git_clean pre-flight self-heals a direct-mode clone left dirty by a finished Pilot run instead of failing every later task
probe: present qf-studio/pilot func checkGitClean
probe: present qf-studio/pilot pre-flight check failed
probe: absent  qf-studio/pilot preflight self-heal

## Context

Second half of #5865. Depends on #5900. Even after #5900 ships, clones left dirty by earlier daemon versions, or by any future leak, wedge the project: the git_clean pre-flight (checkGitClean in `internal/executor/preflight.go`, called from the runner's pre-flight step) fails with "working directory has N uncommitted change(s): run 'git stash' or 'git commit' first" and nothing recovers. The reporter's two projects stayed blocked until a person cleaned the clone by hand. The stale-branch recreation path in `internal/executor/git.go` also refuses on a dirty clone ("working tree has uncommitted changes").

## Implementation

1. In the runner's pre-flight call site, before failing on git_clean in direct mode only, decide whether the dirt belongs to a finished Pilot run. Ownership test, all three must hold: the clone's current branch name starts with pilot/ (a Pilot task branch, never the default branch); that branch's HEAD commit exists on the remote (git ls-remote or the local remote-tracking ref matches); and the executions ledger has no running or queued row for this project path. If all hold, reset the tree to HEAD with ResetHardToCommit, log one Warn line "pre-flight self-heal: discarded N uncommitted change(s) left by finished run on branch X", emit a lifecycle notification on the project's channel with the same text, and re-run the check once.
2. If any ownership condition fails (default branch checked out, unpushed commits, another run active), do not touch the tree; fail as today, and add the three condition results to the error text so an operator sees why the heal did not run.
3. Record the heal in the execution's metadata or log so the finish tripwire and the dashboard can attribute it.
4. Tests, table-driven, with a real temporary git repo: dirty clone on a pushed pilot/ branch heals; dirty clone on main does not; dirty clone with an unpushed commit does not; a running row for the same project blocks the heal.

## Acceptance

- A direct-mode clone that is on a pushed pilot/ branch with one unstaged change passes pre-flight after the heal, and the Warn line names the branch and the file count.
- A dirty clone on the default branch fails pre-flight as before, and the error text names the failed condition.
- A dirty clone with a running execution row for the same project fails pre-flight without a reset.
- `go test -race ./internal/executor/ -run TestPreflightSelfHeal` passes; paste the output into the PR body.
- remove the branch-prefix condition so a dirty default-branch clone heals -> TestPreflightSelfHeal_DefaultBranchNotHealed fails
- remove the ledger check -> TestPreflightSelfHeal_RunningRowBlocksHeal fails

## Out of scope

- Worktree mode (the worktree is discarded per run).
- Healing untracked files outside the excluded set when the branch is the default branch.

## Refs

- #5865
- #5900

## Refs

- A1 → https://github.com/qf-studio/pilot/issues/5900
- A2 → https://github.com/qf-studio/pilot/issues/5901
