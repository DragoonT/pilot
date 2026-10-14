# fix(executor): enforce the write boundary of chat and bootstrap sessions with a PreToolUse guard, because --allowedTools does nothing under --dangerously-skip-permissions

**Status**: 🚀 Dispatched to Pilot 2026-10-14 → [#5688](https://github.com/qf-studio/pilot/issues/5688) (labels `pilot` + `no-decompose`; found in the post-merge review of PR #5683 / TASK-549)
**Created**: 2026-10-14
**Repo**: qf-studio/pilot

Blocked by: none

## Context

Every Claude Code spawn in `internal/executor/backend_claudecode.go` passes `--dangerously-skip-permissions`. Under that flag `--allowedTools` is inert: it is an auto-approve list, and skip-permissions already approves every tool. The chat session (`ChatReadOnlyTools`, TASK-518) and the Navigator bootstrap session (`NavigatorBootstrapTools()`, PR #5683: `Write(.agent/**)`, `Edit(.agent/**)`) rely on that flag as their safety boundary, so in production both sessions can write any file in the project clone. The unit tests pass because the fake backend re-implements the allowlist rule (`toolAllows` in `navigator_bootstrap_test.go`); the real CLI was never exercised.

Reviewer probes with the local CLI (2026-10-14), prompt "use the Write tool to create ./outside.txt and ./.agent/inside.txt":
- `--dangerously-skip-permissions --allowedTools "Read,Write(.agent/**)"` → both files written.
- `--dangerously-skip-permissions --disallowedTools "Write,Edit"` → neither written (deny lists hold).
- `--dangerously-skip-permissions --settings <file with a PreToolUse hook on Write|Edit|MultiEdit that exits 2>` → the hook fires and blocks; hooks run under skip-permissions.

Claude Code has no "deny Write except under this directory" rule, so the enforceable shape is a PreToolUse hook that allows a write only when the resolved path is under `<project>/.agent/`.

## Scope

- `internal/executor/backend.go` / `backend_claudecode.go`: add `ExecuteOptions.WriteBoundary string` (a directory relative to the project path; empty means no guard). When set, the backend writes a per-run settings JSON into the run's temp dir with a `PreToolUse` hook on `Write|Edit|MultiEdit|NotebookEdit` whose command is a small Go-free shell script (also written to the temp dir) that reads the hook JSON from stdin, resolves `tool_input.file_path` with `realpath -m` against the realpath of the project dir, exits 0 when the path is inside `<project>/<WriteBoundary>/` and exits 2 with a one-line reason otherwise. Pass it with `--settings <path>`. Remove both files when the run ends.
- Chat session (`internal/executor/chat_turn.go`): set `WriteBoundary` to a directory that cannot exist, so every write is blocked, and add `--disallowedTools "Write,Edit,MultiEdit,NotebookEdit"` (belt and braces: the deny list holds under skip-permissions).
- Bootstrap session (`internal/executor/navigator_bootstrap.go`): set `WriteBoundary: navigatorDirName`. After the session, run `git status --porcelain` in the project path and revert or delete every change outside the Navigator directory (log each path at Warn); report them in `NavigatorBootstrapResult.StrayWrites`.
- Keep `--allowedTools` as is (it still trims the toolbox and the token cost).

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go test ./internal/executor/ -count=1` passes; paste the output into the PR body. Adds TestClaudeCodeBackend_WriteBoundaryRendersSettingsAndHook (args contain `--settings <path>`; the settings file has a PreToolUse entry matching `Write|Edit|MultiEdit|NotebookEdit`; the script exists and is executable), TestWriteBoundaryGuardScript (runs the generated script with a hook JSON for a path inside the boundary → exit 0, outside → exit 2, a symlinked path that escapes → exit 2), TestChatTurn_DeniesWriteTools (args contain `--disallowedTools` with Write, Edit, MultiEdit, NotebookEdit) and TestNavigatorBootstrap_StrayWriteReverted (a fake backend that writes `src/stray.txt` and edits `go.mod` outside the boundary → after the run `src/stray.txt` is gone, `go.mod` is restored, `StrayWrites` lists both).
- `go test ./internal/executor/ -run 'NavigatorBootstrap' -count=1` still passes; paste the output into the PR body.
- drop the realpath resolution in the guard script -> TestWriteBoundaryGuardScript fails on the symlink case
- remove the post-session git sweep in the bootstrap -> TestNavigatorBootstrap_StrayWriteReverted fails

## Out of scope

- Removing `--dangerously-skip-permissions` from execution sessions (they need Bash and edits).
- Changing what the chat or bootstrap prompts say.

## Refs

- `internal/executor/backend_claudecode.go` (argument assembly near the `--allowedTools` append), `internal/executor/backend.go` (ExecuteOptions), `internal/executor/chat_turn.go`, `internal/executor/navigator_bootstrap.go`, `internal/executor/navigator_bootstrap_test.go` (bootstrapFakeBackend, toolAllows)
- PR #5683 post-merge review (probe table)
- Claude Code CLI: `--settings`, `--disallowedTools`, hooks `PreToolUse` exit code 2 blocks the tool call

- Pilot issue: https://github.com/qf-studio/pilot/issues/5688
