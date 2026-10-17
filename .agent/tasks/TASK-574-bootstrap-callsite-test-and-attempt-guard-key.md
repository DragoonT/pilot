# TASK-574: fix(executor): bootstrap gate — cover the runner call site under worktree isolation; key the once-per-process attempt guard on the project path (PR #5742 fast-follow)

**Status**: 📋 Planned 2026-10-17 — not dispatched (founder call)
**Created**: 2026-10-17
**Assignee**: Pilot (one issue, this repo)
**Source**: post-merge review of PR #5742 (GH-5739), 2026-10-17

---

Follow-up to PR #5742 (GH-5739, review: APPROVE with defects, posted on the PR). Anchors on main at 23891ee04.

## Problem

Two defects from the review of PR #5742.

1. **The only production call site is untested.** `internal/executor/runner.go:3949` now passes `task.ProjectPath` to `maybeInitNavigator`. The mirror subtest `TestNavigatorAutoInit_HonoursProjectNavigatorFlag/distinct_worktree_execution_path` (`internal/executor/runner_test.go:3642-3683`) returns `false` from the lookup, so the upstream auto-init gate at `runner.go:3944` short-circuits and `maybeInitNavigator` never runs. Its assertion `lookedUp[0] == cloneDir` is satisfied by the auto-init gate alone. Mutating line 3949 to pass `executionPath` twice leaves every test green (review pin C). A regression at the call site ships silently.

2. **The once-per-process retry guard is per task under worktree isolation.** `navBootstrapAttempted` (`internal/executor/runner.go:1051-1053`) is documented as holding "project paths whose automatic Navigator bootstrap already ran (or failed) in this process", and the inline comment at `internal/executor/navigator_bootstrap.go:380` says "must not retry on every task of this daemon". The `LoadOrStore` at `:381` is keyed on `executionPath`. Worktree paths are `pilot-worktree-<task>-<unixnano>` (`internal/executor/worktree.go:144`), unique per task, so the guard never matches twice. A bootstrap that fails, or stays partial with a placeholder README on the default branch, re-runs a paid session on every task of that project. PR #5742 rewrote the doc comment at `navigator_bootstrap.go:358` to "once per execution path", which codifies the wrong key.

## Scope

- `internal/executor/navigator_bootstrap.go`: key `navBootstrapAttempted.LoadOrStore` on `projectPath`; restore the doc comment to "once per project path"; keep `executionPath` for the README placeholder check and the session's working directory (unchanged from PR #5742).
- `internal/executor/runner_test.go`: add a subtest to `TestNavigatorAutoInit_HonoursProjectNavigatorFlag` whose lookup returns `p == cloneDir` (exact match, as `FindProjectByPath` does), with `UseWorktree: true` and `Bootstrap: "auto"`; assert the backend ran in a path other than the clone, at least two lookups happened (auto-init + bootstrap), and every recorded key equals `cloneDir`.
- `internal/executor/navigator_bootstrap_test.go`: a subtest that calls `maybeBootstrapNavigator` twice with two distinct execution paths and the same project path, with a placeholder README in both, and asserts the fake backend ran exactly once.

## Acceptance

- `go build ./...` and `go vet ./internal/executor/` pass; paste the output into the PR body.
- `go test -short -race ./internal/executor/ -run 'NavigatorAutoInit|NavigatorBootstrap' -count=1 -v` prints `--- PASS` for every subtest; paste the lines into the PR body.
- `go test -short -race ./internal/executor/` green; `golangci-lint run ./internal/executor/...` 0 issues.
- Pin: at `runner.go:3949` pass `executionPath` twice → the new runner subtest fails on a recorded key that is a worktree path.
- Pin: key `LoadOrStore` on `executionPath` again → the new two-worktrees subtest fails with two backend runs.

## Out of scope

- `cmd/pilot/navigator.go:74` calling `ExecuteNavigatorBootstrap` directly (explicit operator command; bypasses the `navigator: false` gate by design, noted in the review).
- Persisting the attempt guard across daemon restarts.

## Refs

- PR #5742 review (verdict comment, defects 1 and 2), GH-5739, GH-5732, GH-5710
- `internal/executor/navigator_bootstrap.go`, `internal/executor/runner.go`, `internal/executor/runner_git.go`, `internal/executor/runner_test.go`, `internal/executor/navigator_bootstrap_test.go`, `internal/executor/worktree.go`
