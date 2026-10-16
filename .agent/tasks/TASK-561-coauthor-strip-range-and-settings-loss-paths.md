# TASK-561: fix(executor): co-author strip covers the whole branch and the settings key survives hooks-off (PR #5714 fast-follow)

**Status**: 🚀 Dispatched to Pilot 2026-10-15 → [#5719](https://github.com/qf-studio/pilot/issues/5719) (`pilot`, `no-decompose`)
**Created**: 2026-10-15
**Assignee**: Pilot (one issue, this repo, `pilot` + `no-decompose`)
**Source**: post-merge review + nav-research on main 5892a89f6

---

Follow-up to PR #5714 (GH-5711, review: APPROVE with defects, posted on the PR). Research on main at 5892a89f6.

## Problem

Three gaps leave the Anthropic `Co-Authored-By` trailer reachable on main despite GH-5711:

1. **The push-time strip is unverified at its only wiring point.** `GitOperations.Push` (`internal/executor/git.go:885`) calls `StripAnthropicCoAuthor` at `:886`; removing that call keeps `go test -run 'Push|StripAnthropicCoAuthor'` green, because `TestStripAnthropicCoAuthor` (`internal/executor/git_test.go:1853`) drives the function directly on a repo with no remote. Six call sites depend on the wiring (`internal/executor/runner.go:2467`, `:3126`, `:3233`, `:6742`; `internal/executor/runner_decompose.go:549`; `internal/executor/git_freshness.go:123`).
2. **The strip rewrites HEAD only.** `git.go:861` reads `git log -1`; `:873` amends HEAD. Every push site can carry more than one new commit: the Claude session commits any number of times, and before the final push `StripUnindexedMemoryDocs` (`git.go:553`, called at `runner.go:6665`) and `RestoreDeletedIndexedMemoryDocs` (`git.go:737`, called at `runner.go:6683`) each add a commit of their own, and `preserveDirtyWorktreeAsWIP` (`git_freshness.go:113`) puts a wip commit on top of the session's commits. The GitHub squash body aggregates co-authors from every commit in the PR, which is the path that put the trailer on main in #5712 and #5713. The WARN at `git.go:887`/`:891` names only the branch, not the task.
3. **The settings layer has two loss paths.** The `includeCoAuthoredBy: false` write sits under `r.config.Hooks.Enabled` (`runner.go:4539`, generated at `:4558`, merged at `:4562`), so `hooks.enabled: false` loses it. And `GenerateClaudeSettings` returns an empty map when no hook entries are generated (`internal/executor/hooks.go:160-161`) before the key is set at `:168`, so `enabled: true` with every sub-hook off loses it too, and `MergeWithExisting` (`hooks.go:259-260`) then has nothing to force.

The default is `Enabled: true` (`hooks.go:65`, GH-5280), so the daemon is covered today; the gaps are for configs that disable hooks and for multi-commit branches.

## Scope

- `internal/executor/git.go`: make `StripAnthropicCoAuthor` range-aware. Resolve the base with `GetDefaultBranch` (`git.go:1101`), prefer the remote-tracking ref of that base, fall back to the branch's own remote ref, then HEAD. List `git rev-list <base>..HEAD`; when only HEAD matches keep the amend; when an older commit matches, rewrite the range message-only (tree hashes unchanged) and WARN with the rewritten shas. Keep "log and continue" on error. Let `Push` take a task id (or a logger) so the WARN names the task.
- `internal/executor/hooks.go`: `GenerateClaudeSettings` returns the `includeCoAuthoredBy: false` key even when the hooks map is empty (`:160-161`).
- `internal/executor/runner.go:4539`: write the key independent of `Hooks.Enabled` — an unconditional minimal-settings merge, or an `else` branch that merges only that key.
- Tests: (a) `Push` wiring test on `newRemoteAndLocalRepo` (`git_test.go:931`): three commits, two with the trailer (one not HEAD), `Push`, then assert `git log --format=%B origin/<branch>` has no `@anthropic.com` line and every tree hash is unchanged — this goes red if the `:886` call is removed; (b) a multi-commit subtest in `TestStripAnthropicCoAuthor`; (c) a settings test with `hooks.enabled: false` and one with `enabled: true` and no sub-hooks, each asserting the written `settings.json` contains `"includeCoAuthoredBy": false`.

## Acceptance

- `go build ./...` and `go vet ./internal/executor/` pass; paste the output into the PR body.
- `go test -short -race ./internal/executor/ -run 'Push|StripAnthropicCoAuthor|CoAuthoredBy' -count=1 -v` prints `--- PASS` for every new test; paste the lines into the PR body.
- `go test -short -race ./internal/executor/` green.
- Pin: delete the `StripAnthropicCoAuthor` call from `Push` → the wiring test fails (today it survives).
- Pin: restore `git log -1` / HEAD-only amend → the multi-commit subtest fails.
- Pin: restore the empty-map early return in `GenerateClaudeSettings` → the no-sub-hooks settings test fails.
- The squash commit of this PR and the next executor-made PR on main carry no `Co-Authored-By` line (`git log -1 --format=%B`).

## Out of scope

- Prompt guidance tests (`internal/executor/prompt_builder.go:331, 365, 401`); coverage only.
- `CleanStalePilotHooks` leaving `includeCoAuthoredBy: false` in a user's project settings after a crash in root mode (same class as the pre-existing hook-entry leak).
- The Qwen backend; `includeCoAuthoredBy` is a Claude Code setting.
- Whether the Navigator bootstrap session (`internal/executor/navigator_bootstrap.go:158`) can commit at all; it does not pass through the settings write, verify and file separately if it can.

## Refs

- PR #5714 review (verdict comment), GH-5711, GH-5280 (hooks default)
- `internal/executor/git.go`, `internal/executor/hooks.go`, `internal/executor/runner.go`, `internal/executor/git_test.go`, `internal/executor/hooks_test.go`
- Pilot issue: https://github.com/qf-studio/pilot/issues/5719
