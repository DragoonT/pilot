# TASK-560: fix(executor): finish every begun adoption — deferred finalizer, direct-mode retry baseline (PR #5713 fast-follow)

**Status**: ✅ MERGED 2026-10-15 18:41Z → [PR#5722](https://github.com/qf-studio/pilot/pull/5722) (#5718). Post-merge review 2026-10-16: **APPROVE with notes**, 3/3 pins kill, no defects; notes: the explicit "passed" site is load-bearing for the post-gate policy, defer closes over `result` not `outResult`, PR-body evidence incomplete. Archived.
**Created**: 2026-10-15
**Assignee**: Pilot (one issue, this repo, `pilot` + `no-decompose`)
**Source**: post-merge review + nav-research on main 5892a89f6

---

Follow-up to PR #5713 (GH-5709, review: APPROVE with defects, posted on the PR). Research on main at 5892a89f6.

## Problem

`adoptPreservedWorktree` / `adoptGhostPreserved` begin an adoption (`internal/executor/runner.go:5256`, `:5425`), but `finishAdoption` runs at only two sites: gates red (`runner.go:6120`, with `adoption.failureText` at `:6119`) and gates passed (`:6166`). Four exits inside the gate section return `result` with `adoption != nil` and call neither:

| Exit | Line | Error text |
|---|---|---|
| gate checker error | `runner.go:5802` (set at `:5772`) | `quality gate error: …` |
| task ctx done, branch held | `runner.go:5865` (`holdPushedBranch` at `:5861`) | hold reason |
| pre-retry `ResetHardToCommit` failure (direct mode only) | `runner.go:5956` | reset error |
| retry backend failure | `runner.go:6079` (set at `:6012` `beErr`, `:6044` `retryErr`) | `retry execution failed: …` |

On these exits the `auto-preserved as ` marker (`autoPreservedFailureMarker`, `runner.go:73`) is absent from `result.Error`, so `IsPermanentFailure` (`runner.go:79`) is false, the dispatcher re-picks instead of blocking, and `parseAutoPreservedSHABranch` (`internal/executor/dispatcher.go:2262`, caller `:2603`) cannot name the preserved sha in the escalation comment. The "keep today's behaviour on red" promise of GH-5709 is lost exactly when the gate infrastructure fails. No INFO `adopted auto-preserved commit` line is emitted either (GH-5709 change 4).

Second defect, direct (non-worktree) mode only: `preserveDirtyWorktreeAsWIP` pushes the wip commit before the gates (`internal/executor/git_freshness.go:123`). A `ShouldRetry` gate failure hard-resets the clone to `preAttemptSHA` (`runner.go:5909`, assigned at `:4378` only when `!useWorktree`, decision at `:4329`), which rewinds the already-pushed commit; the retry's fresh commit diverges from the remote branch and the final plain push (`runner.go:6742`) is non-fast-forward. The normal flow never pushes before gates, so this is adoption-specific. The daemon runs worktrees, so it is latent there and live for direct-mode installs.

## Scope

1. `internal/executor/runner.go`: replace the two per-site `finishAdoption` calls with one deferred finalizer installed right after the adoption is set (the function has named returns; every exit writes `result` before returning). The defer, when `adoption != nil`: if `!result.Success` and `result.Error` lacks `autoPreservedFailureMarker`, set `result.Error = adoption.failureText(result.Error)`; call `finishAdoption` exactly once with `"failed"` or `"passed"` from `result.Success` (guard with a `finished` flag on `preservedAdoption` so the existing `:6120`/`:6166` sites, if kept, do not double-fire). The defer must run after `holdPushedBranch` rewrites `result.Error` at `:5861`.
2. `internal/executor/runner.go:5903-5909`: when `adoption != nil`, reset to `adoption.sha` instead of `preAttemptSHA` (the preserved commit is the retry baseline). Do not add `--force-with-lease` to the final push.
3. `internal/executor/preserve_adopt.go`: in the ghost-SHA path, do not record a second `work_preserved` event from `beginAdoption` (the first, from `applyGhostSHAGuardWithPreserve` at `runner.go:2026`, already says "needs manual review"; rewrite that text or skip the second).
4. Tests, `internal/executor/gh5709_test.go` (`TestRunner_AdoptAutoPreservedCommit`, rows at `:43-51`): add rows for (a) gate checker returns an error, (b) `taskCtxWasDone && canHoldBranch` with adoption, (c) `retryErr` and `beErr` with adoption, (d) pre-retry reset failure with adoption; each asserts `result.Error` contains `auto-preserved as <sha> on branch <b>`, `IsPermanentFailure(result.Error)` is true, and exactly one `adopted auto-preserved commit` INFO line exists (isolate that line before asserting `sha=`; the preserve WARN lines at `git_freshness.go:139` also carry a `sha` key, which is why the current `:138-143` assertion is vacuous). Add (e) a row with `Success=false` or `ErrorType` set and a dirty tree, and (f) a `DECLINED:` marker row, asserting no adoption (`preserve_adopt.go:58,64` are untested today).
5. Test, direct mode: wip pushed, `ShouldRetry`, reset, retry commit; assert the final push is a fast-forward (bare `origin` fixture).

## Acceptance

- `go build ./...` and `go vet ./internal/executor/` pass; paste the output into the PR body.
- `go test -short -race ./internal/executor/ -run 'AdoptAutoPreserved|AdoptedPreservedRun' -count=1 -v` prints `--- PASS` for every new row; paste the lines into the PR body.
- `go test -short -race ./internal/executor/ ./cmd/pilot/` green.
- `finishAdoption` has exactly one call site in `runner.go` (the defer), or the two existing sites plus the defer with a proven single-fire guard; say which in the PR body.
- Pin: remove the `failureText` wrap from the defer → rows (a)–(d) fail on the marker assertion.
- Pin: restore `preAttemptSHA` as the reset target with adoption → the direct-mode test fails on the non-fast-forward push.
- Pin: rename the INFO slog key `sha` → the isolated-line assertion fails (today it survives).

## Out of scope

- The post-gate returns after `:6166` (contract evidence, PR creation, veto, push-retry exhaustion at `:6777`): whether the marker should apply there is a separate policy decision.
- The optional continuation prompt before the grace kill (GH-5709 second lever).
- `.agent/system/FEATURE-MATRIX.md:660` has 6 cells in a 4-column table and sits under the wrong version heading; fix in the same PR if touched, otherwise leave.

## Refs

- PR #5713 review (verdict comment), GH-5709, GH-5530 (grace kill), GH-5381 (sweep)
- `internal/executor/runner.go`, `internal/executor/preserve_adopt.go`, `internal/executor/git_freshness.go`, `internal/executor/dispatcher.go`, `internal/executor/gh5709_test.go`, `internal/executor/gh5709_dispatcher_test.go`
- Pilot issue: https://github.com/qf-studio/pilot/issues/5718
