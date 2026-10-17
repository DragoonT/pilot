# TASK-572: fix(executor): Navigator bootstrap gate keyed on the clone path (PR #5736 fast-follow)

**Status**: ✅ MERGED 2026-10-17 13:01Z → [PR#5742](https://github.com/qf-studio/pilot/pull/5742) (#5739). Post-merge review 2026-10-17: **APPROVE with defects**, 2/3 pins kill — pin C (`runner.go:3949` passes `executionPath` twice) survives: the mirror subtest returns `false` from the lookup, so the auto-init gate at `:3944` short-circuits before the changed call site. Defect 2: `navBootstrapAttempted` keyed on `executionPath` (unique per worktree) → the once-per-process retry guard is per task. Both → [TASK-574](../TASK-574-bootstrap-callsite-test-and-attempt-guard-key.md). Archived.
**Created**: 2026-10-17
**Assignee**: Pilot (one issue, this repo)
**Source**: post-merge review 2026-10-16

---

Follow-up to PR #5736 (GH-5732, review: APPROVE with defects, posted on the PR). Anchors on main at 99cce9ead.

## Problem

The `navigator: false` gate in `maybeBootstrapNavigator` is keyed on the wrong path. `internal/executor/navigator_bootstrap.go:366` consults `r.navigatorEnabledLookup(projectPath)`, but its sole caller `internal/executor/runner_git.go:215` passes the path `maybeInitNavigator` (`runner_git.go:200`) received, and `runner.go:3949` calls that with `executionPath` — the worktree path whenever worktree isolation is active. `FindProjectByPath` is exact-match (`internal/config/config.go:473`), so a worktree path matches no registered project and the lookup returns enabled. The gate is therefore inert under worktree isolation. No wrong behaviour is observable today only because the upstream auto-init gate at `runner.go:3944` is keyed correctly on `task.ProjectPath` and short-circuits before bootstrap is reached. Any new caller of `maybeInitNavigator` or `maybeBootstrapNavigator` with a worktree path (a bootstrap CLI, a non-auto-init path) bypasses the check. `TestNavigatorBootstrap_AutoSkippedWhenProjectNavigatorDisabled` (`internal/executor/navigator_bootstrap_test.go:341`) cannot see this because it passes the same directory as both the lookup key and the path.

## Scope

- `internal/executor/runner_git.go`: `maybeInitNavigator(ctx, executionPath, projectPath string)`; pass `task.ProjectPath` from `runner.go:3949`; forward both to `maybeBootstrapNavigator(ctx, executionPath, projectPath)`.
- `internal/executor/navigator_bootstrap.go:361-371`: key `navigatorEnabledLookup` on `projectPath` (the clone path the config knows); keep `executionPath` for the README placeholder check and the session's working directory; add `project_path` and `execution_path` to the DEBUG skip line.
- Update every other caller of `maybeInitNavigator` / `maybeBootstrapNavigator` (grep; the CLI path through `cmd/pilot/commands.go` if it calls them directly).
- Tests: extend `TestNavigatorBootstrap_AutoSkippedWhenProjectNavigatorDisabled` with distinct worktree and clone directories, a lookup fake that records its argument, and assertions that (a) the lookup was called with the clone path, (b) no bootstrap session was spawned; add the mirror case in `TestNavigatorAutoInit_HonoursProjectNavigatorFlag` (`internal/executor/runner_test.go:3584`) where `executionPath != task.ProjectPath`.

## Acceptance

- `go build ./...` and `go vet ./internal/executor/ ./cmd/pilot/` pass; paste the output into the PR body.
- `go test -short -race ./internal/executor/ -run 'NavigatorAutoInit|NavigatorBootstrap' -count=1 -v` prints `--- PASS` for every subtest; paste the lines into the PR body.
- `go test -short -race ./internal/executor/ ./cmd/pilot/` green; `golangci-lint run ./internal/executor/... ./cmd/pilot/...` 0 issues.
- Pin: key the bootstrap lookup on `executionPath` again → the distinct-paths subtest fails on the recorded lookup argument.
- Pin: drop the forwarded `projectPath` → compile error or the same subtest fails.

## Out of scope

- The default value of `ProjectConfig.Navigator` (documented opt-in; the daemon-start INFO line from PR #5736 makes the state visible).
- The prompt builder's `.agent/` detection on the worktree path (`internal/executor/prompt_builder.go:176`), which is correct as is.

## Refs

- PR #5736 review (verdict comment, defect 1), GH-5732, GH-5710, GH-5685, GH-5679
- `internal/executor/runner_git.go`, `internal/executor/navigator_bootstrap.go`, `internal/executor/runner.go`, `internal/config/config.go`, `internal/executor/navigator_bootstrap_test.go`, `internal/executor/runner_test.go`

- Pilot issue: https://github.com/qf-studio/pilot/issues/5739
