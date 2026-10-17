# TASK-573: fix(autopilot): self-closed PR hand-off marks the original task superseded; fix issue closes it (re-pick loop 2026-10-16)

**Status**: 🚀 Dispatched to Pilot 2026-10-17 → [#5741](https://github.com/qf-studio/pilot/issues/5741) (`pilot`, `no-decompose`)
**Created**: 2026-10-17
**Assignee**: Pilot (one issue, this repo)
**Source**: incident GH-5731 re-pick loop + nav-research 2026-10-17

---

Incident 2026-10-16 on the founder box (v2.288.0), nav-research on main at 16136ede5, box rows read.

## Problem

When autopilot closes a PR to hand its work to a CI fix issue, the original task becomes re-pickable, and the dispatcher runs it again from scratch while the fix run owns the branch.

Timeline (daemon log + `executions` rows):

| Time (Z) | Event |
|---|---|
| 14:01:52 | GH-5731 completed → PR #5733; row `completed`, `pr_url` set |
| 14:02 | CI `lint` red |
| 14:13:05 | fix issue #5735 created (`autopilot-fix`, footer `branch:pilot/GH-5731 pr:5733 … source:5731`) |
| 14:13:07 | GH-5731 row rewritten to `failed`, error `pr #5733: ci_failed -> failed` |
| 14:13:58 | `PR closed internally (self-close marker), skipping external-close handling` pr=5733 |
| 14:32:28 | `dispatch re-pick: prior claim was terminal but task is not done — claiming next generation for retry` task=GH-5731 |
| 14:33:08 | fix run GH-5735: `Reusing branch from autopilot-meta footer` branch=pilot/GH-5731 |
| 14:57:55 | GH-5731 re-run ends `infra`: `push failed after 3 attempt(s): ! [rejected] pilot/GH-5731 -> pilot/GH-5731` |
| 14:58:41 | `dispatch re-pick: prior claim was infra-classified — claiming next generation without counting toward repick hard cap` → third run 15:11, same ending 15:34 |
| 15:23 | stopped by hand: `pilot` label removed from #5731, PR #5737 edited to `Closes #5731` |

Mechanism:

1. `handleCIFailed` sets the stage to failed and the error `…; fix issue #N created to continue this work` (`internal/autopilot/controller.go:4416`), after `markSelfClosed` (`:4380`, def. `:10851`) and `ClosePullRequest`.
2. `recordExecutionEvent` on a pre-merge `StageFailed` calls `ReclassifyCompletionAsFailed` (`controller.go:2720`, GH-5067), which demotes the original's `completed` row to `failed` (`internal/memory/store.go:1847`).
3. The self-close marker makes `checkExternalMergeOrClose` skip `notifyExternalClose` (`controller.go:10884`), which is the **only** caller of `ReclassifyCompletionAsSuperseded` (`:10915`, store `:1871`). So no `superseded` row is ever written for the original.
4. `HasTerminalCompletion` (`store.go:1432`) counts `completed`-with-pr, `no_op`, `canceled`, `superseded`, `needs_human` as done; `failed` is not. `nextRetryGeneration` (`internal/executor/dispatcher.go:1762`) therefore grants generation+1 and logs the line at `:2173`. The same predicate drives the poller's `terminalCompletionChecker` (`cmd/pilot/main.go:4417`).
5. Nothing on the original issue changes at hand-off: no label, no comment; `pilot-superseded` is deferred to `verifyFixPRDeliversSourceScope` (`internal/autopilot/owner_death.go:191`) after the fix PR merges. The fix PR body does not `Closes #<original>`; PR #5737 closed only #5735 until edited by hand.
6. The re-run's rejected push is classed `infra` (`internal/executor/runner.go:441-451`), which bypasses the 5-drop hard cap, the backoff window and the identical-failure streak; only `dispatcherInfraRepickCap = 8` (`dispatcher.go:1422`) bounds it, per task. Worst case: eight more 25-minute Sonnet runs per hand-off.

The review-revision rung has the same shape (`controller.go:4900`). The same class as TASK-508 (#5564), which fixed the post-merge borrow; its in-memory borrow registry protects the fix task from its origin, not the original from re-pick.

## Scope

1. `internal/autopilot/controller.go`: at both self-close sites (`:4380` and `:4900`), right after `markSelfClosed`, record the original task as `superseded` with reason `continued by fix issue #N` via `ReclassifyCompletionAsSuperseded` (`store.go:1871`) — or make the `StageFailed` demotion at `:2720` choose superseded when `prState.SelfClosedFixIssue > 0`. Pick one; say which in the PR body. The dispatcher and the poller then treat the original as done with no new store state; `tryRearmSuperseded` (`cmd/pilot/main.go`) still re-arms it on a human relabel or reopen.
2. `internal/autopilot/feedback_loop.go` `generateBody` (`:480`): the fix issue body carries `Closes #<original>` for pre-merge fix issues (the `source:` number already in the footer at `:600`), so the fix PR closes both issues on merge; keep `pilot-superseded` behaviour as is.
3. Tests: (a) `internal/autopilot/gh5247_test.go` next to `TestHandleCIFailed_Classification`: after `handleCIFailed` self-closes with a fix issue, the original task's row is `superseded` (fake store records the reclassify call and reason); mirror for the review-revision rung; (b) `internal/executor/dispatcher_test.go` next to `TestNextRetryGeneration_*` (`:5345`): a `failed` row with `pr_url` set plus a `superseded` row → no retry; (c) `internal/autopilot/feedback_loop_test.go`: pre-merge body contains `Closes #<source>`, post-merge body does not; (d) one chain test in `internal/autopilot/`: CI-fail → self-close → `HasTerminalCompletion` true for the original.

## Acceptance

- `go build ./...` and `go vet ./internal/autopilot/ ./internal/executor/ ./internal/memory/ ./cmd/pilot/` pass; paste the output into the PR body.
- `go test -short -race ./internal/autopilot/ -run 'HandleCIFailed|SelfClose|FeedbackLoop|GenerateBody' -count=1 -v` and `go test -short -race ./internal/executor/ -run 'NextRetryGeneration' -count=1 -v` print `--- PASS` for every new test; paste the lines into the PR body.
- `go test -short -race ./internal/autopilot/ ./internal/executor/ ./internal/memory/ ./cmd/pilot/` green; `golangci-lint run` on those packages 0 issues.
- Pin: remove the superseded write at the self-close site → tests (a) and (d) fail.
- Pin: drop `Closes #<source>` from the body → test (c) fails.
- Live: the next CI-red PR on the box produces a fix issue and **no** `dispatch re-pick … task is not done` line for the original task (`grep` the daemon log).

## Out of scope

- The infra re-pick cap and cross-task coordination (`dispatcherInfraRepickCap`); file separately if the loop recurs for another reason.
- The in-memory borrow registry's TTL and restart loss (TASK-508 note).
- The Slack approval click that did not reach the daemon for PR #5737 (separate).

## Refs

- Box rows: GH-5731 `56197f8d` completed→failed 14:13:07Z; `b8510515` infra 14:57:55Z; `c69ff74b` infra 15:34:02Z; GH-5735 `432d1d4c`/`e0665f10` completed → PR #5737
- GH-5067 (failed demotion), GH-5351/GH-5362 (self-close marker), GH-5361, GH-5379 (footer without label), GH-5729 (rejected push loud), TASK-508 / #5564
- `internal/autopilot/controller.go`, `internal/autopilot/feedback_loop.go`, `internal/autopilot/owner_death.go`, `internal/memory/store.go`, `internal/executor/dispatcher.go`, `internal/executor/runner.go`, `cmd/pilot/main.go`, `cmd/pilot/handlers.go`, `internal/autopilot/gh5247_test.go`, `internal/autopilot/feedback_loop_test.go`, `internal/executor/dispatcher_test.go`

- Pilot issue: https://github.com/qf-studio/pilot/issues/5741
