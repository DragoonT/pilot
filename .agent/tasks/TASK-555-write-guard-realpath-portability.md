# fix(executor): make the write-boundary guard script portable — realpath -m is GNU-only, so on macOS the guard denies every write and its test fails

**Status**: 🚀 Dispatched to Pilot 2026-10-14 → [#5694](https://github.com/qf-studio/pilot/issues/5694) (labels `pilot` + `no-decompose`; found in the post-merge review of PR #5692 / TASK-551)
**Created**: 2026-10-14
**Repo**: qf-studio/pilot

Blocked by: none

## Context

The PreToolUse guard that `setupWriteBoundary` writes (`internal/executor/write_boundary.go`, constant `writeBoundaryGuardScript`) resolves the target and the boundary with `realpath -m`. That flag exists in GNU coreutils (the founder box, CI on Ubuntu, Amazon Linux tenants) but not in BSD `realpath` on macOS. On a Mac the script prints `realpath: illegal option -- m` and takes the deny branch, so every Write, Edit, MultiEdit and NotebookEdit is refused in chat and bootstrap sessions (fail-closed, but the bootstrap can then write nothing), and `TestWriteBoundaryGuardScript` fails four times with `exit = 2, want 0` on every developer machine. Reviewer evidence: the test passes on the box and fails on macOS at the same commit (fe28fc661). The issue text for TASK-551 asked for `realpath -m`; that was the spec miss.

## Scope

- `internal/executor/write_boundary.go`: replace both `realpath -m -- X` calls with a resolver that works on GNU and BSD: walk up from X to the nearest existing ancestor, resolve that with plain `realpath --` (available on both), and append the remaining path components; keep the symlink-escape protection (the ancestor resolution follows symlinks). Alternatively, when `python3` is present, resolve with `python3 -I -c 'import os,sys;print(os.path.realpath(sys.argv[1]))'`, falling back to the shell walk. No change to the deny semantics or the matcher.
- `internal/executor/write_boundary_test.go`: run the script with `/bin/sh` as today; add a case where the target's parent directory does not exist yet (the create-new-file case) and keep the symlink-escape case.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go test ./internal/executor/ -run TestWriteBoundaryGuardScript -count=1` passes; paste the output into the PR body. The same command must pass on macOS; the reviewer runs it there.
- `go test ./internal/executor/ -run TestSetupWriteBoundary_CleanupRemovesFiles -count=1` passes; paste the output into the PR body.
- `grep -n 'realpath -m' internal/executor/write_boundary.go` prints nothing; paste the output into the PR body.
- resolve the target without following symlinks -> TestWriteBoundaryGuardScript fails on the symlink-escape case
- skip the ancestor walk and resolve only existing paths -> TestWriteBoundaryGuardScript fails on the new-file case

## Out of scope

- The deny list on the chat session and the bootstrap sweep (PR #5692, unchanged).

## Refs

- `internal/executor/write_boundary.go` (writeBoundaryGuardScript, setupWriteBoundary), `internal/executor/write_boundary_test.go`
- PR #5692 post-merge review (defect section)

- Pilot issue: https://github.com/qf-studio/pilot/issues/5694
