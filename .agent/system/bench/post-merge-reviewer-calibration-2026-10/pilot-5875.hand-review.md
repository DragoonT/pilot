## Post-merge review — APPROVE-WITH-NOTES

Reviewed merge `57e935622` against #5867 (own diff read, independent second read, `go test -race`, four mutation pins).

### Verified
- The incident path is closed: evidence runs on its own `WithTimeout(WithoutCancel(ctx), budget)` (default 15m, `executor.acceptance_evidence_budget`, validated `>= 0`, box default sane without a config edit), with an `AfterFunc` that propagates a real `context.Canceled`, so `pilot task cancel` during evidence still stops PR creation. Right before `CreatePR`/`CreateMR` on all five sites (SDK, shared creator, gh CLI, timeout salvage, epic) the finalize window is re-derived; the recovery ref in `formatGitStepFailureWithRecovery` gets its own 5m window.
- Gate reuse is exact-argv on *passed* gates only (resolved command, so a `make test` → `go test ./...` fallback matches what ran); `make test` ≠ `make test-race` ≠ `go test ./...`, so those bullets still run, bounded by the budget. Reused lines carry `(from the quality-gate run)`.
- Mutation pins (applied and reverted locally):
  - fresh window before CreatePR → `WithCancel(ctx)` at all 5 sites → `TestExecute_PRCreateSurvivesDeadlineBlownDuringEvidence` fails.
  - recovery ref on the dead ctx → `TestExecute_PRCreateSurvivesDeadline_RecoveryRefOnExpiredCtx` fails.
  - evidence budget chained to the task ctx → `TestEvidenceBudgetCtx_DetachesDeadlineButKeepsCancel` fails.
  - gate output never indexed → `TestAppendAcceptanceEvidence_ReusesQualityGateOutput` fails.

```
go test -race -count=1 ./internal/executor/ -run '<the seven GH-5867 tests>'   ok  12.515s
go test -race -count=1 ./internal/config/                                       ok  2.551s
```

### Defects (evidence integrity, low) — worth one follow-up
1. **A budget-killed command inside a mixed item renders as evidence.** In `runPasteOutputItemReusing`, `allErrored` is false once any command of the item finished, so when the second command of a `make build` · `make test` · `make lint` bullet is SIGKILLed by the budget, `NotVerifiedReason` stays empty, `cr.Err` is never rendered, and the item lands under `## Evidence` with the killed command's partial output and no marker; the third command's "Not verified: evidence budget exhausted" lands *inside* the fenced block. A truncated `make test` showing only `ok` lines reads as a pass.
2. **Reused gate output is not pinned to the pushed HEAD.** Gates run before self-review, and self-review can commit fixes with no gate re-run (`runner.go` ~L7129: "Self-review or quality retries may push new commits after result.CommitSHA was captured"). `newEvidenceGateOutputs` checks only `Passed`/`ExitCode`/`Command`, so the PR body can show `$ make test (from the quality-gate run)` for a tree that is not the pushed SHA. Skip reuse when HEAD moved after the gates.

### Notes (no action required)
- `finalizeCtx` grants a fresh window only when the task ctx is *already* `DeadlineExceeded` at call time. If seconds remain after evidence, it returns `WithCancel(ctx)` and the three `CreatePR` attempts 300 ms apart still die on the deadline (the recovery ref then does get its window). The spec's "expires during evidence" case is met; the "expires during CreatePR" tail is narrowed, not closed. Granting the window when remaining < budget would close it.
- The re-derived ctx is block-scoped to each creator branch; the task-completed webhook, `syncMainBranch` and `recordLearning` after the branch chain still run on the outer ctx, which is dead when the deadline blew during evidence. Pre-existing, but the 15m evidence budget makes it the common case for complex runs.
- `ctx.Err()` is sticky: a cancel issued *after* the deadline already blew is ignored for the rest of evidence (≤15m) and finalize (≤15m). No Execute-level test covers "cancel during evidence → no CreatePR".
- No upper bound on `acceptance_evidence_budget` vs the complexity timeout (`2h` silently extends a 60m task by 2h + finalize).
- Spec asked for "one WARN log line"; `logEvidenceEvent` fires once per reused command (three for the standard bullet) plus one on exhaustion.
- Gate output is `stdout + "\n" + stderr`, not interleaved `CombinedOutput` — cosmetic difference in the pasted block.
- The runner test exercises only the shared-creator branch (`SourceAdapter = "linear"`); the gh-CLI branch (the incident's), the SDK branch, `pushAndCreatePRAfterTimeout` and `finalizeEpicBranchPR` are untested. Timing is wall-clock (2–3 s sleeps, `elapsed <= 3.5s`), adequate margin but `-race`-on-loaded-CI sensitive.

