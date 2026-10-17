# TASK-571: fix(executor): co-author strip warns and stays HEAD-only with no origin refs (PR #5737 fast-follow)

**Status**: ✅ MERGED 2026-10-17 12:35Z → [PR#5740](https://github.com/qf-studio/pilot/pull/5740) (#5738). Post-merge review 2026-10-17: **APPROVE with notes**, 2/2 pins kill (origin-refs check removed → `HEAD's parent changed`; WARN removed → `log missing "reason=..."`). Notes: the "older commit was rewritten" assertion reads the pre-strip SHA and can never fail (git objects are immutable); `task_id`/`branch` substrings are satisfied by either WARN, only `reason=` pins the degradation line; `for-each-ref` is the right detector (an `origin` added but never fetched is HEAD-only + WARN, push then succeeds once). No follow-up. Archived.
**Created**: 2026-10-17
**Assignee**: Pilot (one issue, this repo)
**Source**: post-merge review 2026-10-16

---

Follow-up to PR #5733 / PR #5737 (GH-5731, review: CHANGES REQUESTED defect 2, posted on PR #5733). Anchors on main at 99cce9ead.

## Problem

`unpublishedCommits` (`internal/executor/git.go:934`) lists the range with `git rev-list --topo-order HEAD --not --remotes=origin` (`:941`). When no remote-tracking ref under the `origin` namespace exists — a clone with no remote, or a clone whose only remote has another name — `--remotes=origin` matches nothing, `rev-list` returns the whole history with exit 0, and nothing warns. `rewriteCommitMessages` (`:973`) then rewrites every commit back to the root (the diff of PR #5733 had to add root-commit tolerance for exactly this). Verified in the review with a throwaway test on a no-remote repo: three commits, trailer on the oldest → one rewrite, HEAD moved, where main before PR #5733 rewrote HEAD only. `Push` hardcodes `origin`, so in that configuration the push then fails after the local history was already rewritten: trees intact, but every other local branch that shared those commits now diverges. GH-5731 asked for a WARN on any remaining degraded path; this one is silent.

## Scope

- `internal/executor/git.go`, `unpublishedCommits`: before the `rev-list`, check whether any ref exists under the `origin` remote namespace (`git for-each-ref --count=1 refs/remotes/origin/`, or `git remote get-url origin`). When none exists: return `[]string{head}` (HEAD-only, today's pre-#5733 behaviour) and let the caller WARN. Keep the `commits[0] != head` short-circuit (`:946`).
- `stripCoAuthorBeforePush` (`:1043`): on the HEAD-only degradation, `slog.Warn` with `task_id`, `branch` and `reason="no origin refs; co-author strip limited to HEAD"`. Keep log-and-continue on error.
- Tests in `internal/executor/git_test.go`: (a) a subtest in `TestStripAnthropicCoAuthor` (`:1853`) on `initTestRepo` (`:970`, no remote): three commits, trailers on the oldest and on HEAD; assert exactly one rewrite (HEAD), the older trailer untouched, and the WARN line present with `task_id`; (b) a subtest with a remote named `upstream` only: same expectation; (c) the existing bare-`origin` subtests unchanged and green.

## Acceptance

- `go build ./...` and `go vet ./internal/executor/` pass; paste the output into the PR body.
- `go test -short -race ./internal/executor/ -run 'StripAnthropicCoAuthor|Push_Strips' -count=1 -v` prints `--- PASS` for every subtest; paste the lines into the PR body.
- `go test -short -race ./internal/executor/` green; `golangci-lint run ./internal/executor/...` 0 issues.
- Pin: remove the origin-refs check → subtest (a) fails (two rewrites, or HEAD's parent changed).
- Pin: remove the WARN → subtest (a) fails on the missing log line.

## Out of scope

- Supporting a remote not named `origin` in `Push` (the executor hardcodes it everywhere).
- The single-HEAD amend path's committer-date reset.

## Refs

- PR #5733 review (verdict comment, defect 2), PR #5737, GH-5731, GH-5719, GH-5711
- `internal/executor/git.go`, `internal/executor/git_test.go`

- Pilot issue: https://github.com/qf-studio/pilot/issues/5738
