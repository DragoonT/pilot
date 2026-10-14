# fix(executor): stop assuming main after PR #5620 — chat-filed tasks, lint baseline and the autopilot branch resolver must use the project's default branch

**Status**: 🚀 Dispatched to Pilot 2026-10-14 → [#5695](https://github.com/qf-studio/pilot/issues/5695) (labels `pilot` + `no-decompose`; follow-up from the review of external PR #5620 / issue #5619)
**Created**: 2026-10-14
**Repo**: qf-studio/pilot

Blocked by: PR #5620 merged (it introduces `WorktreeManager.SetBaseBranch` / `resolveBaseBranch`)

## Context

PR #5620 bases worktrees on the project's default branch. Three places still assume `main` and break a repository whose default branch is, for example, `mainline`, right after worktree creation succeeds:
- `internal/comms/handler.go` line 852 sets `baseBranch = "main"` for every chat-filed task when `createPR` is true. That value reaches `SetBaseBranch("main")` as an explicit setting and fails with "couldn't find remote ref main". The GitHub polling path resolves the base through `ProjectConfig.ResolveBaseBranch` (`internal/config/config.go` around line 340); the chat path must do the same.
- `internal/executor/lint.go` line 81 runs golangci-lint with `--new-from-rev=origin/main`, and the prompt text in `internal/executor/prompt_builder.go` near line 662 tells the model to do the same. On a `mainline` repo the lint step errors on a missing ref.
- `internal/autopilot/controller.go` around line 6741 (`resolveMainBranchName`) and `internal/autopilot/auto_merger.go` around line 212 fall back to the literal `main` with a WARN and, per their own comment, never consult the project's `default_branch` / `branch_from`. A `mainline` project only works when `environments.<env>.branch` is set by hand.

Also found, lower priority, not in scope: about twelve "main" fallbacks in runner.go reached only when `task.BaseBranch` is empty and `GetDefaultBranch` fails; acceptance_evidence_run.go line 608 goes straight to `main`; the unused worktree pool would race on `SetBaseBranch` if it were ever wired.

## Scope

- `internal/comms/handler.go`: resolve the base branch for a chat-filed task the same way the polling path does (project config `branch_from`, else `default_branch`, else empty so the worktree manager detects `origin/HEAD`). Remove the literal.
- `internal/executor/lint.go` and `internal/executor/prompt_builder.go`: take the base ref from the task (`task.BaseBranch`, else the worktree manager's resolved branch) and use `origin/<base>`; keep the fallback to `origin/main` only when nothing resolves.
- `internal/autopilot/controller.go` `resolveMainBranchName` and `internal/autopilot/auto_merger.go`: consult the project's `branch_from` / `default_branch` before the `main` fallback; log once at Info which source won.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go vet ./internal/comms/ ./internal/executor/ ./internal/autopilot/` passes; paste the output into the PR body.
- `go test ./internal/comms/ -run ChatFiledTask -count=1` passes; paste the output into the PR body. Adds TestChatFiledTask_BaseBranchFromProjectConfig: with `branch_from: mainline` the filed task carries BaseBranch "mainline"; with no config it carries "".
- `go test ./internal/executor/ -run Lint -count=1` passes; paste the output into the PR body. Adds TestLintBaseRefFollowsTaskBaseBranch: a task with BaseBranch "mainline" produces `--new-from-rev=origin/mainline`.
- `go test ./internal/autopilot/ -run ResolveMainBranchName -count=1` passes; paste the output into the PR body. Adds TestResolveMainBranchName_UsesProjectDefaultBranch.
- `grep -n 'baseBranch = "main"' internal/comms/handler.go` prints nothing; paste the output into the PR body.
- restore the literal "main" in the chat handler -> TestChatFiledTask_BaseBranchFromProjectConfig fails
- hardcode origin/main again in lint.go -> TestLintBaseRefFollowsTaskBaseBranch fails

## Out of scope

- The twelve runner.go fallbacks and acceptance_evidence_run.go (separate cleanup once a shared helper exists).
- Wiring or deleting the worktree pool.

## Refs

- `internal/comms/handler.go`, `internal/executor/lint.go`, `internal/executor/prompt_builder.go`, `internal/autopilot/controller.go`, `internal/autopilot/auto_merger.go`, `internal/config/config.go`
- PR #5620 (external, approved) and issue #5619 — the worktree half of this problem

- Pilot issue: https://github.com/qf-studio/pilot/issues/5695
