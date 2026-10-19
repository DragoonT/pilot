# TASK-575: fix(autopilot): self-close hand-off — supersede a still-running original row, and strip `pilot` labels from an original the fix PR closed (PR #5743 fast-follow)

**Status**: 🚀 Dispatched to Pilot 2026-10-19 → [#5747](https://github.com/qf-studio/pilot/issues/5747) (labels `pilot` + `no-decompose`)
**Last Updated**: 2026-10-19
**Created**: 2026-10-19
**Assignee**: Pilot (one issue, this repo)
**Source**: post-merge review of PR #5743 (GH-5741), 2026-10-19, notes 1 and 2

---

Two gaps left by PR #5743 (GH-5741), found in its post-merge review on main at 488c8a9c8. Both are small; both sit on the same hand-off path.

## Problem

**1. The supersede at self-close is a silent no-op when the original's row is not `completed`.**

`markOriginalSuperseded` (`internal/autopilot/controller.go:10877`) calls only `ReclassifyCompletionAsSuperseded` (`internal/memory/store.go:1871`), whose `UPDATE` matches `status = 'completed'` with an empty `error` and a deliverable. If the original's latest row is still `queued`/`pending`/`running` at self-close time (the GH-4499 shape: the poller never finalized the row, or the PR was opened by a run that was then killed), nothing is updated, nothing is logged, and the later `StageFailed` demotion in `recordExecutionEvent` (`controller.go:2720`) flips the `running` row to `failed` via `UpdateExecutionStatusIfNotTerminal`. `HasTerminalCompletion` (`store.go:1432`) is then false and `nextRetryGeneration` (`internal/executor/dispatcher.go:1762`) re-picks the original — the GH-5731 loop PR #5743 fixed, still open on this path.

`notifyExternalClose` already handles this shape: it calls `ReclassifyCompletionAsSuperseded` (`controller.go:10965`) **and then** `TerminateNonTerminalExecutionAsSuperseded` (`controller.go:10988`, store `store.go:1924`, which updates only the latest row and only when it is `queued`/`pending`/`running`). `markOriginalSuperseded` mirrors the first call and omits the second.

**2. An original the fix PR closed keeps `pilot` / `pilot-in-progress` and never gets `pilot-superseded`.**

PR #5743 added `Closes #<original>` to the pre-merge fix issue body (`internal/autopilot/feedback_loop.go:616-621`), and the executor lifts it into the fix PR body, so GitHub closes the original when the fix PR merges. `verifyFixPRDeliversSourceScope` (`internal/autopilot/owner_death.go:191`) then runs and returns early at `owner_death.go:243` (`source.State == github.StateClosed || HasLabel(Superseded)`) **before** the `mutateIssueLabels` call at `owner_death.go:263-266` that adds `pilot-superseded` and strips `pilot`, `pilot-in-progress`, `pilot-needs-manual-rebase`. Net: the original ends **closed with its trigger labels standing** and no `pilot-superseded`. Dispatch is unaffected (closed issues are not polled; the ledger row is `superseded`), but the GH-5298 invariant ("`pilot-superseded` and `pilot` never coexist") and the GH-5375 label mirror are broken on every hand-off from now on, and the stale-label sweep and any operator reading labels see a live task on a closed issue. The doc comment at `owner_death.go:67` ("the original issue stays open (pilot-superseded, never closed) after hand-off") is now false.

## Scope

1. `internal/autopilot/controller.go` `markOriginalSuperseded` (`:10877`): after `ReclassifyCompletionAsSuperseded`, also call `TerminateNonTerminalExecutionAsSuperseded` with the same `taskID`, `projectPath`, `reason` — the same pair `notifyExternalClose` runs at `:10965`/`:10988`. Resolve the store the same way the function already does (`evalStore`, else `memoryStore` via interface assertion); widen the local interface to both methods. Warn on error from either call, as today.
2. `internal/autopilot/owner_death.go` `verifyFixPRDeliversSourceScope`: split the early return at `:243`. If the source already carries `pilot-superseded` → return (idempotent, as today). If the source is **closed and does not** carry `pilot-superseded` → do not return; fall through to the overlap check so a confirmed-overlap source gets the `:263` label mutation (add `pilot-superseded`, strip `pilot`, `pilot-in-progress`, `pilot-needs-manual-rebase`) and the Info log. A closed source with **no** overlap → keep the current mismatch handling (needs-human label + comment) unchanged; the comment text "Leaving this issue open" may stay as is. Update the doc comment at `owner_death.go:62-70` to say the original is closed by the fix PR's `Closes #<source>` since GH-5741.
3. Tests:
   (a) `internal/autopilot/gh5741_test.go`, next to `TestHandleCIFailed_SelfClose_OriginalHasTerminalCompletion` (`:69`): a real `memory.Store` whose latest row for the original is `running` (no `completed` row); run `handleCIFailed` through the self-close, then `recordExecutionEvent(StageCIFailed → StageFailed)`; assert the row is `superseded` and `HasTerminalCompletion` is true. Mirror with a `pending` row.
   (b) `internal/autopilot/gh5247_test.go`, next to `TestHandleCIFailed_HandOff_MarksOriginalSuperseded` (`:313`): the mock store records both the `ReclassifyCompletionAsSuperseded` and the `TerminateNonTerminalExecutionAsSuperseded` call with the same reason.
   (c) `internal/autopilot/gh4841_test.go` or a new test file gh5741b_test.go next to the existing `verifyFixPRDeliversSourceScope` tests: source issue **closed**, no `pilot-superseded`, files overlap → `mutateIssueLabels` adds `pilot-superseded` and removes `pilot` + `pilot-in-progress`; source closed **with** `pilot-superseded` → no label call (idempotent); source open → unchanged behaviour.

## Acceptance

- `go build ./...` and `go vet ./internal/autopilot/ ./internal/memory/` pass; paste the output into the PR body.
- `go test -short -race ./internal/autopilot/ -run 'SelfClose|HandOff|FixPRDeliversSourceScope|GH5741' -count=1 -v` prints `--- PASS` for every new test; paste the lines into the PR body.
- `go test -short -race ./internal/autopilot/ ./internal/memory/ ./internal/executor/` green; `golangci-lint run ./internal/autopilot/ ./internal/memory/` 0 issues.
- Pin: remove the `TerminateNonTerminalExecutionAsSuperseded` call from `markOriginalSuperseded` → tests (a) and (b) fail.
- Pin: restore the unconditional `StateClosed` early return at `owner_death.go:243` → test (c)'s closed-no-label case fails.
- The existing GH-5741 tests (`TestHandleCIFailed_HandOff_MarksOriginalSuperseded`, `TestHandleReviewRequested_SelfClose_MarksOriginalSuperseded`, `TestHandleCIFailed_SelfClose_OriginalHasTerminalCompletion`) still pass.

## Out of scope

- The one-hop `Closes` chain (a 2-deep cascade closes fix1 but not the original on GitHub; the ledger is unaffected).
- Logging rows-affected from the store methods (optional; the second call makes the gap moot).
- `tryRearmSuperseded` semantics (`cmd/pilot/rearm_superseded.go`) — unchanged; re-arm still needs reopen + relabel.

## Refs

- PR #5743 post-merge review (verdict comment, notes 1 and 2); GH-5741; GH-4499 (`TerminateNonTerminalExecution`); GH-4701 (superseded sibling); GH-5298 / GH-5375 (label invariants); GH-5351 / GH-5362 (`verifyFixPRDeliversSourceScope`)
- `internal/autopilot/controller.go`, `internal/autopilot/owner_death.go`, `internal/autopilot/feedback_loop.go`, `internal/memory/store.go`, `internal/executor/dispatcher.go`, `internal/autopilot/gh5741_test.go`, `internal/autopilot/gh5247_test.go`, `internal/autopilot/gh4841_test.go`, `cmd/pilot/rearm_superseded.go`
- Pilot issue: https://github.com/qf-studio/pilot/issues/5747
