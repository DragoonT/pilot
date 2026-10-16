# TASK-568: fix(linear): one-line push reason, branch_pushed visible with the terminal status, superseded read-error keeps the prior (PR #5717 fast-follow)

**Status**: ✅ MERGED 2026-10-15 21:00Z → [PR#5728](https://github.com/qf-studio/pilot/pull/5728) (#5720; chain PR#5724 → #5725 → PR#5726 → #5727, CI skew with PR#5723's `Push` signature). Post-merge review 2026-10-16: **APPROVE with notes**, 4/4 pins kill, no defects; `Persist` writes `branch_pushed` first with a non-terminal guard. Renumbered from TASK-562 (collided with the archived console-403 doc). Archived.
**Created**: 2026-10-15
**Assignee**: Pilot (one issue, this repo, `pilot` + `no-decompose`)
**Source**: post-merge review + nav-research on main 5892a89f6

---

Follow-up to PR #5717 (GH-5715, review: APPROVE with defects, posted on the PR). Research on main at 5892a89f6.

## Problem

1. **The push-failed hold reason still shows git's `To https://…` header on Linear.** `pushAndCreatePRAfterTimeout` builds the reason as `fmt.Sprintf("timeout salvage: branch push failed: %v", err)` (`internal/executor/runner.go:3236`) with the raw `Push` error, which is `failed to push: %w: %s` over git's full stderr (`internal/executor/git.go:898`). `holdPushedBranch` appends its own one-line `(branch push also failed: …)` at the end (`runner.go:3136`), but the Linear text path keeps only the first line: row error → `classifyWaitedExecution` (`cmd/pilot/handler_common.go:612`) → `linearOutcomeDetail` (`cmd/pilot/handlers.go:402`) → `linearDetailText` → `linearDetailLine` (`cmd/pilot/linear_state.go:729`). So the `**Reason**` reads `timeout salvage: branch push failed: failed to push: exit status 1: To https://github.com/o/r.git`. The same first-line symptom exists on the failed-row path at `runner.go:2478` (`epic branch push failed: %v`) and through `formatGitStepFailureWithRecovery` (`runner.go:393`, callers `runner.go:6775` and `internal/executor/runner_decompose.go:576`), where the `recovery:` tail is also cut off. `PushFailureReason` (`runner.go:3198`) exists for exactly this, and its keyword list misses `fatal:` lines (a bad remote URL yields the hint trailer `and the repository exists.`).
2. **`branch_pushed` becomes visible after the terminal status.** `Persist` (`internal/executor/lifecycle.go:311`) runs the status CAS at `:330` (`UpdateExecutionStatusIfNotTerminal`, `internal/memory/store.go:3047`) and then `SetExecutionBranchPushed` at `:335` (`store.go:3504`, plain `UPDATE … SET branch_pushed = ? WHERE id = ?`, no guard). The comment at `:333` says the value "rides on the same terminal write"; it does not. `Dispatcher.WaitForExecution` (`internal/executor/dispatcher.go:3007`, 1s tick from `handler_common.go:421`) returns on the first terminal `GetExecution` read; `classifyWaitedExecution` copies `exec.BranchPushed` at `handler_common.go:615`; a NULL column scans to `nil`, and `linearHeldComment` then posts `No branch was pushed: the work was held without a push.` (`linear_state.go:510`) for a branch that was pushed. The `Persist` doc comment (`lifecycle.go:303-310`, GH-4259) already states the rule for events: write the companion row before the status write.
3. **A Linear read error during the superseded restore strands the issue.** `MoveSuperseded` (`linear_state.go:228`) on a `GetIssue` error calls `forgetPrior` (`:231`), warns, and returns the error; the only caller discards it (`linear_state.go:648`), nothing retries, and the prior state is gone, so the issue stays in the started state forever. `TestLinearSupersededForgetsPrior` (`cmd/pilot/linear_outcome_legs_test.go:320`) has no read-error row.

## Scope

- `internal/executor/runner.go:3236`: build the hold reason once with `PushFailureReason(err)`; decide whether `holdPushedBranch` then still appends its own fragment (two push-failure fragments in one reason is noise) — simplest: pass the short `timeout salvage: branch push failed` and let `holdPushedBranch` re-push and append the single one-line reason. Apply `PushFailureReason` at `runner.go:2478` and inside `formatGitStepFailureWithRecovery` when the step is the push. Add `fatal:` to the keyword list at `runner.go:3198`.
- `internal/executor/lifecycle.go`: make the push result visible no later than the terminal status. Either move the `SetExecutionBranchPushed` block above the status CAS (minimal diff; add a `… AND status NOT IN (<terminal>)` guard variant so a rejected CAS does not stamp another writer's row), or fold `branch_pushed = COALESCE(?, branch_pushed)` into `UpdateExecutionStatusIfNotTerminal` (`store.go:3054-3070`) as one statement (zero window). Fix the comment at `:333` either way.
- `cmd/pilot/linear_state.go:229-236`: on a `GetIssue` error keep the `priorState` entry (drop the `forgetPrior` call) and return the error; whether anything retries is a separate design choice, state it in the PR.
- Tests: (a) `internal/executor/runner_gh5715_test.go`: a row that drives `pushAndCreatePRAfterTimeout` with a multi-line `Push` error and asserts the row error has no newline and no `To ` before the first newline; a `TestPushFailureReason` row for a `fatal:` stderr; (b) a store-or-lifecycle test asserting `GetExecution` never returns a terminal row with `BranchPushed == nil` after `Persist` for a result with `BranchPushed != nil` (pause or hook between the two writes, or assert the single statement); (c) a `GetIssue`-error row in `TestLinearSupersededForgetsPrior` asserting the prior is kept and zero `issueUpdate` calls.

## Acceptance

- `go build ./...`, `go vet ./internal/executor/ ./internal/memory/ ./cmd/pilot/` pass; paste the output into the PR body.
- `go test -short -race ./cmd/pilot/ -run 'Linear' -count=1 -v` and `go test -short -race ./internal/executor/ -run 'GH5715|PushFailureReason|HoldPushedBranch|Persist' -count=1 -v` print `--- PASS` for every new row; paste the lines into the PR body.
- `go test -short -race ./internal/executor/ ./internal/memory/ ./cmd/pilot/` green.
- `grep -n '"timeout salvage: branch push failed: %v"' internal/executor/runner.go` returns nothing.
- Pin: restore `%v` at the `:3236` site → test (a) fails on `To `.
- Pin: restore the status-then-push order (or drop the COALESCE column) → test (b) fails.
- Pin: restore `forgetPrior` in the read-error branch → test (c) fails.
- Live: the next `needs_human` row with a failed push shows a one-line `**Reason**` on the Linear issue (box log `Linear state transition` + the comment body).

## Out of scope

- The other `holdPushedBranch` callers with `%v` reasons that are not push errors (`runner.go:3033`, `:3058`, `:3267`, `:3298`): check whether `createErr` can be multi-line and file separately if so.
- Whether the Linear poller re-picks a superseded issue.
- GitLab/Azure/Asana state write-back (same class as GH-5701, unfiled).

## Refs

- PR #5717 review (verdict comment), GH-5715, GH-5708, GH-5705, GH-5701, GH-4259 (event-before-status rule)
- `internal/executor/runner.go`, `internal/executor/lifecycle.go`, `internal/memory/store.go`, `internal/executor/dispatcher.go`, `cmd/pilot/handler_common.go`, `cmd/pilot/handlers.go`, `cmd/pilot/linear_state.go`, `internal/executor/runner_gh5715_test.go`, `cmd/pilot/linear_outcome_legs_test.go`
- Pilot issue: https://github.com/qf-studio/pilot/issues/5720
