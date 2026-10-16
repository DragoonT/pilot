# TASK-570: fix(executor): auto-init and bootstrap honour navigator: false; daemon lists projects with it off (PR #5721 fast-follow)

**Status**: ✅ MERGED 2026-10-16 14:42Z → [PR#5736](https://github.com/qf-studio/pilot/pull/5736) (#5732). Post-merge review 2026-10-16: **APPROVE with defects**, 3/3 pins kill; defect: the bootstrap gate is keyed on the worktree `executionPath`, not the clone path, so it is inert under worktree isolation (protected today only by the upstream auto-init gate) — follow-up to file. Archived.
**Created**: 2026-10-16
**Assignee**: Pilot (one issue, this repo)
**Source**: post-merge review 2026-10-16

---

Follow-up to PR #5721 (GH-5710, review: APPROVE with notes, posted on the PR). Anchors on main at 76b65caeb.

## Problem

A project's `navigator: false` (`internal/config/config.go:282`, resolved by `newProjectNavigatorEnabledLookup` at `cmd/pilot/adapters.go:272`) is honoured by the copy-back only (`internal/executor/navigator.go:706`). The two other Navigator entry points ignore it:

- `maybeInitNavigator` (`internal/executor/runner_git.go:200`) runs whenever the global `navigator.auto_init` is on (`internal/executor/runner.go:3939`, gated on `task.LocalMode` and the global flag only). So the worktree of a `navigator: false` project still gets `.agent/` scaffolded.
- `maybeBootstrapNavigator` (`internal/executor/navigator_bootstrap.go:361`) runs on the global `bootstrap: auto` plus the README placeholder check, with no per-project gate.
- The prompt then detects `.agent/` in the worktree (`internal/executor/prompt_builder.go:176-178`) and runs the task with Navigator context, which may commit `.agent/` into the project's PR.

Net effect for a `navigator: false` project with global `auto_init: true`: scaffold, Navigator prompt, possible `.agent/` in the PR, and only the clone copy-back suppressed. This is almost certainly how the box's `navigator: false` project came to have `.agent/` in its worktree in the first place (GH-5710 context).

Second, smaller point: `ProjectConfig.Navigator` is a plain `bool` with no default-true, and the lookup returns `proj.Navigator` for any registered project, so a project registered before its `.agent/` existed and relying on `auto_init` since then loses copy-back after PR #5721, with only a DEBUG line to say so.

## Scope

- `internal/executor/runner.go:3939`: consult `r.navigatorEnabledLookup(task.ProjectPath)` in the `auto_init` branch; when the lookup is non-nil and returns false, skip `maybeInitNavigator` and log one DEBUG line (`task_id`, `project_path`). A nil lookup keeps today's behaviour (enabled).
- `internal/executor/navigator_bootstrap.go:361`: same gate in `maybeBootstrapNavigator`.
- `internal/executor/prompt_builder.go:176`: no change; once the scaffold is skipped the `.agent/` check already selects the plain prompt. State in the PR body that this was verified (a `navigator: false` project with no `.agent/` gets the non-Navigator prompt).
- Daemon start: one INFO line listing registered projects whose `navigator` is false (so the behaviour change for pre-existing registrations is visible), at the site where `newProjectNavigatorEnabledLookup` is built (`cmd/pilot/adapters.go:272`) or where projects are logged at start.
- Tests: (a) in `internal/executor/runner_test.go` next to `TestLocalModeSkipsNavigatorAutoInit` (`:3542`): with `AutoInit: true` and a lookup returning false, `maybeInitNavigator` is not called and no `.agent/` is created in the execution path; a lookup returning true or a nil lookup still scaffolds; (b) in `internal/executor/navigator_bootstrap_test.go`: `bootstrap: auto`, placeholder README, lookup false → no bootstrap session is spawned; (c) `cmd/pilot`: the start-up INFO line names exactly the `navigator: false` projects from a two-project config.

## Acceptance

- `go build ./...` and `go vet ./internal/executor/ ./cmd/pilot/` pass; paste the output into the PR body.
- `go test -short -race ./internal/executor/ -run 'NavigatorAutoInit|NavigatorBootstrap|CopyNavigatorBack' -count=1 -v` prints `--- PASS` for every new test; paste the lines into the PR body.
- `go test -short -race ./internal/executor/ ./cmd/pilot/` green.
- Pin: remove the lookup check from the `auto_init` branch → test (a) fails on the created `.agent/`.
- Pin: remove the lookup check from `maybeBootstrapNavigator` → test (b) fails.
- Pin: drop the start-up INFO line → test (c) fails.

## Out of scope

- Changing the default of `ProjectConfig.Navigator` to true (a documented opt-in; the INFO line makes the state visible instead).
- The tripwire `-uall` timeout window and the chat/bootstrap write boundary (separate class).

## Refs

- PR #5721 review (verdict comment), GH-5710, GH-5685 (copy-back), GH-5679 (bootstrap session), GH-2108 (LocalMode skip)
- `internal/executor/runner.go`, `internal/executor/runner_git.go`, `internal/executor/navigator_bootstrap.go`, `internal/executor/navigator.go`, `internal/executor/prompt_builder.go`, `internal/config/config.go`, `cmd/pilot/adapters.go`, `internal/executor/runner_test.go`, `internal/executor/navigator_bootstrap_test.go`

- Pilot issue: https://github.com/qf-studio/pilot/issues/5732
