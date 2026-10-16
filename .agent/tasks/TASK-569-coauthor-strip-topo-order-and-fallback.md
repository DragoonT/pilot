# TASK-569: fix(executor): co-author range strip walks history in topo order; no silent HEAD-only fallback (PR #5723 fast-follow)

**Status**: 🚀 Dispatched to Pilot 2026-10-16 → [#5731](https://github.com/qf-studio/pilot/issues/5731) (`pilot`, `no-decompose`)
**Created**: 2026-10-16
**Assignee**: Pilot (one issue, this repo)
**Source**: post-merge review 2026-10-16

---

Follow-up to PR #5723 (GH-5719, review: APPROVE with defects, posted on the PR). Anchors on main at 76b65caeb.

## Problem

1. **The range rewrite duplicates history and leaves the trailer reachable when the unpublished range has two lines (a merge commit), even with no clock skew.** `unpublishedCommits` (`internal/executor/git.go:936`) lists the range with plain `git rev-list HEAD ^base` (`git.go:958`), reverse-chronological. `rewriteCommitMessages` (`git.go:994`) walks that list oldest-first (`:1001-1002`) on the assumption that every parent comes later in the list than its children; the re-parent only fires when the parent was already rewritten. Default `rev-list` order gives no such guarantee once two lines of history exist and timestamps tie or skew. Reproduced in the review: `epic one(trailer) → {child one(trailer), child two} + epic two → merge --no-ff`, all in the same second: `child one` was processed before `epic one`, kept the old parent, the result had 6 commits instead of 5, and `epic one` with the trailer stayed reachable via the child line. `Push` returned no error. Trees were unchanged, so nothing is lost, but the branch is wrong and the GH-5711 promise (no `@anthropic.com` line reachable on the pushed branch) is broken for that shape. Exposure in Pilot's own flows is low (epic children land on the remote epic branch via the autopilot merge; a conflict `git merge origin/main` has one in-range line), so it needs a session doing a local two-line merge.
2. **Silent HEAD-only degradation when the default branch cannot be resolved.** `git.go:949-956`: when `GetDefaultBranch` (`git.go:1311`) fails (no remote HEAD symbolic ref and the default is neither `main` nor `master`, e.g. `develop`) and the branch has never been pushed, `base == ""` and the function returns `[]string{head}` (`:955`) with no error and no log. Reproduced: `develop` default, no remote HEAD symbolic ref, branch with `one(trailer)` then `two`: zero rewrites, trailer survives, `Push` logs nothing.

## Scope

- `internal/executor/git.go`, `unpublishedCommits`: list the range with `git rev-list --topo-order HEAD --not --remotes=origin`. `--topo-order` guarantees children before parents, so the oldest-first walk re-parents correctly across merges. `--not --remotes=origin` needs no default-branch resolution at all and also excludes commits already published on any other origin ref (the epic-child case), which removes the `base == ""` fallback. Keep the `commits[0] != head` short-circuit (HEAD already published → nothing to rewrite). If a fallback to HEAD-only remains for any reason, log a WARN naming the task and the reason.
- Keep the message-only rewrite (`commit-tree` with preserved author and committer env, single compare-and-swap `update-ref`) and the log-and-continue behaviour in `Push`.
- Tests in `internal/executor/git_test.go`: (a) a merge-commit subtest in `TestStripAnthropicCoAuthor` (`:1853`): two lines with a trailer on the older line's first commit, all commits in the same second, `--no-ff` merge; assert the rewritten branch has the same commit count, no `@anthropic.com` line reachable from HEAD, every tree hash unchanged, the merge commit still has two parents; (b) a `develop`-default subtest with no remote HEAD symbolic ref and an unpushed branch: assert the trailer is rewritten; (c) an epic-child subtest: a commit with a trailer already on a second remote-tracking branch and reachable from HEAD is not rewritten and the push stays fast-forward.

## Acceptance

- `go build ./...` and `go vet ./internal/executor/` pass; paste the output into the PR body.
- `go test -short -race ./internal/executor/ -run 'StripAnthropicCoAuthor|Push_Strips' -count=1 -v` prints `--- PASS` for every new subtest; paste the lines into the PR body.
- `go test -short -race ./internal/executor/` green.
- `grep -n 'rev-list' internal/executor/git.go` shows `--topo-order` on the strip's `rev-list` call.
- Pin: drop `--topo-order` → the merge-commit subtest fails on the commit count or on the reachable trailer.
- Pin: restore the `base == ""` → `[]string{head}` fallback → the `develop`-default subtest fails.
- Pin: drop `--not --remotes=origin` (exclude only the branch's own remote ref) → the epic-child subtest fails.

## Out of scope

- The single-HEAD amend path still resetting the committer date (route it through `rewriteCommitMessages` later if wanted).
- Trailers already on the remote before this code runs.

## Refs

- PR #5723 review (verdict comment), GH-5719, GH-5711, GH-5729 (push rejection must fail loudly)
- `internal/executor/git.go`, `internal/executor/git_test.go`

- Pilot issue: https://github.com/qf-studio/pilot/issues/5731
