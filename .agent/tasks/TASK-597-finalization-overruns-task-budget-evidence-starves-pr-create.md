# TASK-597: finalization overruns the task budget — the acceptance-evidence runner spends the task ctx and PR creation then fails on the dead ctx

**Status**: 🚀 Dispatched 2026-10-26 → pilot#5867 (`pilot`+`no-decompose`+`bug`). Written from box evidence (four lost runs today).
**Spec refs**: #5342 / PR#5345 (finalizeCtx — fresh window only when the task ctx is *already* dead), #5346 (WithoutCancel), #5399 / PR#5402 (salvage push), GH-5435/5437/5438 (acceptance-evidence gate), GH-5442 (argv runner, per-command 10 min default `defaultAcceptanceEvidenceCommandTimeout`), #5864 (re-pick over a stale head — made worse by this class).
**Origin**: founder question 2026-10-26 17:40Z "why is the outcomes chart red today". Four of today's red rows are this class; the branches were pushed each time and the work was lost to a from-scratch re-pick.

## Context

Today on the box (v2.295.0, complex timeout 60m, trivial 30m):

| run | Claude | quality gates | evidence started | task ctx expiry | result |
|---|---|---|---|---|---|
| GH-5861 run 2 | 15:17:40 → 15:31:27 (14 min) | 36m22s | 16:08:46 | 16:17:40 | PR create ×3 fails in 300 ms, recovery ref fails, `failed` |
| GH-5864 | 16:17:54 → 16:40:35 (23 min) | 21m34s | 17:03:04 | 17:17:54 | same |
| ui GH-280 (trivial, 30m) | — | — | — | 13:57:06 | same |
| GH-5861 run 1 | killed by the 15:08 self-upgrade drain | | | | PR create on the cancelled ctx |

The chain in `internal/executor/runner.go`: `finalizeCtx` (line ~347) hands back a fresh bounded window **only when `ctx.Err() == DeadlineExceeded` at call time**; otherwise it returns `WithCancel(ctx)`, the task ctx itself. The last re-derivation before the PR step is the push refresh (~6809). After it, `appendAcceptanceEvidence(ctx, …)` (~7197) runs every paste-output bullet as a subprocess (per-command timeout 10 min, but each command is also bounded by the parent task ctx), with no budget of its own and no reuse of the quality-gate output it just duplicated (`make build`, `make test`, `make lint` = 21–36 min on the box). The task ctx blows during evidence; `git.CreatePR(ctx, …)` (~7202) and the recovery ref in `formatGitStepFailureWithRecovery(ctx, …)` (~7218) then fail instantly. The branch is already pushed (the error names the SHA), but no PR exists, so the next re-pick starts from scratch (and until #5864 ships cannot even push over that head).

## Legs — pilot (daemon)

### LEG F1 — repo: qf-studio/pilot — title: fix(executor): PR creation and the recovery ref must run on a fresh finalize window; the acceptance-evidence step gets its own budget and reuses quality-gate output instead of re-running it

## Context
Three runs today (GH-5861 twice, GH-5864; also console-ui GH-280 on the trivial 30-minute budget) ended "pr-create failed after 3 attempt(s): failed to create PR: context deadline exceeded" with the branch pushed and the recovery ref failing on the same error. Timeline of GH-5864 from daemon.log on the box: Claude Code 16:17:54 to 16:40:35; quality gates 21m34s to 17:02:10; intent judge and self-review to 17:03:03; acceptance classification 17:03:04 (four items, two paste-output: a package go test and make build, make test, make lint); silence until 17:17:54, which is exactly the 60-minute task deadline; then three PR-create attempts 300 ms apart, all context deadline exceeded. GH-5861 run 2 is the same shape with 36m22s of gates and evidence from 16:08:46 to the 16:17:40 deadline.

Cause in `internal/executor/runner.go`: finalizeCtx grants a fresh bounded window only when the task ctx is already past its deadline at the moment it is called; when the ctx is still alive it returns WithCancel of the task ctx. The last refresh before the PR step is the push refresh. After it, appendAcceptanceEvidence runs every paste-output command as a subprocess on that ctx (per-command cap defaultAcceptanceEvidenceCommandTimeout, 10 minutes, in `internal/executor/backend.go`, but every command is also cut by the parent ctx). On this repo the standard bullet make build, make test, make lint repeats the quality gates the run just finished (21 to 36 minutes on the box), so evidence consumes the rest of the task budget. Then git.CreatePR and the recovery ref inside formatGitStepFailureWithRecovery both run on the dead ctx and fail instantly. The pushed branch is orphaned and the re-pick starts from scratch.

probe: present qf-studio/pilot func finalizeCtx\(ctx context\.Context, budget time\.Duration\)
probe: present qf-studio/pilot appendAcceptanceEvidence\(ctx, task, git\.ProjectPath\(\), prBody\)
probe: present qf-studio/pilot defaultAcceptanceEvidenceCommandTimeout
probe: absent  qf-studio/pilot evidenceBudgetCtx
probe: absent  qf-studio/pilot evidence budget exhausted

## Scope
- Re-derive the finalize window immediately before the PR/MR create block (after appendAcceptanceEvidence) and again inside formatGitStepFailureWithRecovery before the recovery ref is created, so a deadline that blows during evidence never reaches CreatePR or the recovery ref. Keep the GH-5342 rule that a real cancellation (context.Canceled) is not extended.
- Give the evidence step its own budget: appendAcceptanceEvidence runs on a new helper evidenceBudgetCtx that is WithoutCancel of the task ctx bounded by a knob executor.acceptance_evidence_budget (default 15m, validated in `internal/config/config.go`, documented in `configs/pilot.example.yaml`). When the budget is exhausted, every remaining paste-output and mutation item renders "Not verified: evidence budget exhausted" and the PR body still gets the evidence block; the task proceeds to PR creation.
- Reuse instead of re-run: when a paste-output command's argv equals a quality-gate command that ran and passed in this run, reuse the gate's captured output (head and tail per the existing trim) and mark the line "(from the quality-gate run)" instead of executing it again. Match on the exact argv string after allowlist parsing; anything else runs as today.
- One WARN log line when evidence reuse or budget exhaustion happens, with task id, item index and the elapsed evidence time.

## Acceptance
- [ ] Runner test: a task ctx that expires during appendAcceptanceEvidence still creates the PR; the fake PR creator sees a ctx with a live deadline, and the recovery-ref helper sees one too when PR creation fails for another reason. Remove the finalize re-derivation before the PR-create block -> TestExecute_PRCreateSurvivesDeadlineBlownDuringEvidence fails.
- [ ] Evidence test: three paste-output items with a 1-second budget and a runner that sleeps 2 seconds yield one executed item and two "Not verified: evidence budget exhausted" lines, and the function returns within the budget plus one command. Remove the budget ctx -> TestAppendAcceptanceEvidence_BudgetExhausted fails.
- [ ] Reuse test: a paste-output item whose argv equals a passed quality-gate command renders the gate's captured output and the runner is not invoked for it; a different argv still runs. Remove the argv match -> TestAppendAcceptanceEvidence_ReusesQualityGateOutput fails.
- [ ] Config test: executor.acceptance_evidence_budget defaults to 15m, rejects negative values, and is read by the runner.
- [ ] `go test -race ./internal/executor/ -run TestAppendAcceptanceEvidence` passes; paste the output into the PR body.
- [ ] `go test -race ./internal/executor/ -run TestExecute_PRCreateSurvives` passes; paste the output into the PR body.
- [ ] `go test -race ./internal/config/ -run TestAcceptanceEvidenceBudget` passes; paste the output into the PR body.
- [ ] Do not add a make build, make test, make lint evidence bullet to this issue: the quality gates already run them and the re-run is the defect under repair.

## Out of scope
- Raising the complexity timeouts on the box (operator config, separate decision).
- The re-pick lease over a stale head (#5864) and the self-upgrade drain that cancels running tasks.
- Changing which commands the evidence allowlist accepts.

## Refs
- Box evidence: daemon.log 2026-10-26 lines for GH-5861 (15:17:40 → 16:17:41) and GH-5864 (16:17:54 → 17:17:54); executions rows with error "pr-create failed after 3 attempt(s)".
- F1 → - F1 → https://github.com/qf-studio/pilot/issues/5867
- Prior: #5342 → PR#5345 (finalizeCtx), #5346, #5399 → PR#5402, GH-5435/5437/5438/5442 (evidence gate), SOP `sops/onboarding/new-project-issue-authoring.md` Rule 5d.

**Last Updated**: 2026-10-26
