## Post-merge review — APPROVE-WITH-NOTES

Reviewed merge `c69964797` against #5829 (own diff read, independent second read, `go test -race`, one mutation pin).

### Verified
- The guard sits in `EnsureBranchFromOrigin`, the only direct-mode caller of `DeleteBranch`; the two other `branch -D` sites (`worktree.go` ~L792/L893) run in the repo root against a worktree's branch and are worktree-mode only. Worktree mode and `CreateOrResetBranchFromOrigin` are untouched.
- Detection is `git branch --show-current`: detached HEAD yields `""` so the guard is bypassed and `branch -D` proceeds (git allows it) — correct; a `master` default resolves through `resolveGuardBaseRef` and `checkout --detach` works for either.
- Tests use a real clone + bare origin (`setupSyncTestRepos`), no mocks; the not-checked-out path is pinned (case 3). Every #5829 acceptance item is met.
- Mutation pin: guard block removed → the checked-out cases fail (git refuses `branch -D`; the dirty case misses "checked out in the clone, refusing"). Applied and reverted locally.

```
go test -race -count=1 ./internal/executor/ -run 'TestGit|Stale|GH5867|Gh5867|5867|Finalize|AcceptanceEvidence'   ok  70.032s
mutation (guard removed): --- FAIL: TestEnsureBranchFromOrigin_StaleCheckedOutBranchIsRecreated
```

### Notes (no action required)
- **Committed-but-unmerged work on the discarded branch is deleted with no local recovery ref.** This is the exact GH-5829 shape (PR closed without merge, origin advanced). Before this change git's refusal accidentally preserved those commits; now `detachHeadAt` → `DeleteBranch` discards them. The remote `pilot/GH-N` still holds them unless the closed-PR branch was deleted on GitHub. Matches the spec's "then delete and recreate as today" — a spec limitation. `CreateRecoveryRef` exists and would close it in one line.
- `GetCurrentBranch` failure is swallowed (`curErr == nil && …`): the guard is skipped silently and the operator gets git's opaque message. A Warn on `curErr != nil` would make it visible.
- No log on the detach path: the daemon log shows only "Created branch … from origin/main"; the operator cannot tell the clone was detached and the old branch discarded.
- The dirty-tree refusal is effectively unreachable from the runner in direct mode: the `git_clean` preflight already rejects a dirty clone before branching (only `LocalMode` bypasses it). Still correct as defensive code.
- Test gaps outside the spec: the dirty case uses an untracked file, not a modified tracked file; no case starts from detached HEAD.
- The PR body pastes `make build`/`make test` output under an acceptance item the issue has since replaced with "do not re-run make … as evidence" (SOP Rule 5d).

