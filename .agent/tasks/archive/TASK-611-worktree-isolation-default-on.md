# TASK-611: worktree isolation is the default — `executor.use_worktree` becomes a tri-state, nil means true, explicit false warns at startup

**Status**: ✅ MERGED 2026-10-28 10:56Z — #5908 → PR#5909 (reviewer APPROVE-w-notes). In v2.297.0: use_worktree nil = true, explicit false warns. Was: dispatched 10-28.
**Spec refs**: `internal/executor/backend.go` UseWorktree (bool, default false); the pointer-plus-Effective idiom already used by AutoCreatePR in the same struct; docs `docs/content/concepts/worktree-isolation.mdx`.
**Origin**: session 2026-10-27/28 — of ~30 fixes in two weeks, every direct-mode-only defect came from one user running the default.

## Why
- `executor.use_worktree` is a plain bool. Unset and false are the same value, so the default can only be false.
- Ten read sites: runner.go (worktree creation, SkipGitClean, cleanup), backend_execute_guard.go, cmd/pilot/main.go ×2, cmd/pilot/commands.go ×2, plus two log fields.
- Direct mode is where the dirty-clone, branch-delete-on-checked-out-branch and root-clean classes live. Worktree mode discards the tree per run.

## Legs — pilot (daemon)

### LEG W1 — repo: qf-studio/pilot — title: feat(executor): worktree isolation on by default — use_worktree is a tri-state (nil = true), explicit false logs a startup warning, docs and example updated
probe: present qf-studio/pilot UseWorktree bool
probe: present qf-studio/pilot autoCreatePR := true
probe: absent  qf-studio/pilot EffectiveUseWorktree

## Context

Pilot can run each task in an isolated git worktree (`executor.use_worktree`) or edit the project clone in place (direct mode). The flag in `internal/executor/backend.go` is a plain bool, so unset equals false and direct mode is the default for every new install. The founder box has run worktree mode for months without incident. Every direct-mode-only defect class of the last two weeks — a killed self-review leaving uncommitted edits that wedged the git_clean pre-flight (#5865), stale-branch delete on the checked-out branch (#5829), root-clean tripwires — came from an external user on the default. The decision is to make worktree isolation the default and keep direct mode as an explicit opt-out.

## Implementation

1. In `internal/executor/backend.go` change UseWorktree to a pointer to bool (keep the yaml key use_worktree, omitempty) and add EffectiveUseWorktree() on BackendConfig: nil returns true, otherwise the value. Set the default in DefaultBackendConfig the same way AutoCreatePR is set (a local true and its address). Update the field comment: default true since this change; false keeps direct mode.
2. Replace every read of the raw field with EffectiveUseWorktree(): `internal/executor/runner.go` (worktree creation decision, SkipGitClean, the cleanup decision and both log fields), `internal/executor/backend_execute_guard.go` (worktreeExpected), `cmd/pilot/main.go` (two sites) and `cmd/pilot/commands.go` (two sites). Keep the existing extra conditions (task branch non-empty, not DirectCommit, allowWorktree) unchanged.
3. Startup warning: where the executor config is validated or logged at startup in `cmd/pilot/main.go`, when the field is explicitly false log one Warn line: "executor.use_worktree is false: tasks edit the project clone in place; a killed phase can leave the clone dirty and block later tasks (set use_worktree: true or remove the key)". Nil and true log nothing new.
4. Config validation in `internal/config/config.go`: no new rule; confirm Load over DefaultConfig keeps nil as "unset" when the key is absent and false when the user writes false (yaml decodes a bool into the pointer).
5. Docs: `docs/content/concepts/worktree-isolation.mdx` and `docs/content/getting-started/configuration.mdx` say worktree isolation is on by default and show use_worktree: false as the opt-out with the warning text; `configs/pilot.example.yaml` shows the key with true and the same note.
6. Tests, table-driven, in the executor package and in cmd/pilot: EffectiveUseWorktree nil/true/false; a loaded config without the key resolves true, with false resolves false; the runner takes the worktree path for a task with a branch when the config is nil-valued; the startup warning fires only for explicit false. Fakes that stub the backend must read their arguments (mocks gate).

## Acceptance

- A config without use_worktree runs a branch task in an isolated worktree, and the start log shows use_worktree=true.
- A config with use_worktree: false runs in direct mode and the daemon logs the startup warning once.
- A config with use_worktree: true behaves as today.
- `go test -race ./internal/executor/ -run TestEffectiveUseWorktree` passes; paste the output into the PR body.
- `go test -race ./cmd/pilot/ -run TestUseWorktreeStartupWarning` passes; paste the output into the PR body.
- make EffectiveUseWorktree return false for nil -> TestEffectiveUseWorktree_NilIsTrue fails
- read the raw field at the runner's worktree decision instead of EffectiveUseWorktree -> TestRunnerUsesWorktreeByDefault fails
- fire the warning for nil as well -> TestUseWorktreeStartupWarning_NilIsSilent fails

## Out of scope

- Removing direct mode.
- Changing worktree cleanup, the stale-branch sweeper or the git_clean pre-flight.
- The box config (already true).

## Refs

- https://github.com/qf-studio/pilot/issues/5865
- https://github.com/qf-studio/pilot/issues/5829

## Refs

- W1 → https://github.com/qf-studio/pilot/issues/5908
