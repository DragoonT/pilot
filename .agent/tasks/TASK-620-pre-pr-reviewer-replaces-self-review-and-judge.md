# TASK-620: the reviewer moves before the PR — one in-run review after the gates with a resumed fix round; self-review and the in-run intent judge retire; post-merge becomes a sampled audit

**Status**: 🟢 L1 MERGED + SHADOW LIVE 2026-10-29 — pilot#5949 → PR#5951 merged 14:42Z (Opus APPROVE-w-notes: runner call to runPrePRReview untested end-to-end; judge-off gate untested; mode≠off + missing claude binary = no in-run review at all; memory recall gated on MemoryInjection — fold into L2/L3 scope). v2.299.0 by the train 15:00Z; box config `executor.pre_pr_review: {mode: shadow, model: claude-opus-5-5, timeout: 6m}` loaded by the hot-upgrade reload 15:08:46Z (`Pre-PR review initialized mode=shadow`; backup `config.yaml.bak-prepr-shadow-20261029`). Next: first shadow verdict on a live run, then dispatch L2 with `--only L2`; plan approved by the founder (plan file `~/.claude/plans/let-s-use-nav-research-pure-twilight.md`). Dispatch order L1 → L2 (shadow live) → L5 ∥ L3 → enforce → L4 → L6.
**Spec refs**: nav-research 2026-10-29 (in-run phases) + stage-machine map; `.agent/system/bench/post_merge_reviewer_calibration_2026-10.md` (runs 1–3); TASK-591 (reviewer), TASK-612/613/614/618/619 (reviewer chain); `internal/executor/runner.go` 6614–6838 (today's self-review ∥ judge block), `internal/executor/post_merge_reviewer.go`, `internal/executor/post_merge_checkout.go`, `internal/autopilot/controller.go` handleCIPassed 3760–3890, `internal/autopilot/post_merge_review.go`.
**Origin**: founder 2026-10-29 "why review after CI at all?" — gates, CI, evidence and self-review check the PR against itself; only the reviewer checks it against the system; a post-merge REQUEST-CHANGES costs a new issue cycle (25–45 min; four in a row on 10-28).

## Founder decisions (2026-10-29)
1. Shadow mode already replaces self-review and the in-run intent judge (net +3 min per run).
2. A clean fix round (REVIEW_FIXED + re-gate green) merges on green; the post-merge audit force-samples it. No approval hold.
3. The 12-minute remaining-budget floor for the fix round is accepted; `executor.timeout.complex` stays 60 m.

## Why (verified at main 5d3ecc6e8)
- Placement "daemon review holds the merge" is dead: isTrustedReviewer (controller.go ~5000) drops bot and own-login reviews (GH-5326); no change-request review call in the client; the review-fix path closes the PR and opens a new one.
- Placement "in-run, before push" has the plumbing: confined read-only checkout (post_merge_checkout.go), session resume (`use_session_resume: true` on the box; backend_claudecode.go ~558), gate re-check idiom (GH-4876), reset idiom (runner.go ~6327), escalate-only approval chain in handleCIPassed, ledger `pr_reviews` reachable from the executor (`Runner.logStore`), `ghAddLabels` for PR labels.
- Today's self-review: fresh `claude -p`, full tools, advisory, 2 m. Intent judge: Haiku, box cap 8,000 chars, no tools, verdict never reaches the PR.
- Budget: complex 60 m; the review (6 m) runs on the finalize ctx; the fix (≤10 m) only with ≥12 m left; the re-gate (5 m) on a fresh ctx; everything after already runs on detached windows (GH-5346/5867/5891). Worst case +21 m, APPROVE case +3 m net.

## Legs — pilot (daemon)

### LEG L1 — repo: qf-studio/pilot — title: feat(executor): pre-PR review in shadow mode — executor.pre_pr_review config, pre-merge prompt variant, runPrePRReview after the quality gates records a verdict and skips self-review and the in-run judge
probe: present qf-studio/pilot type IntentJudgeConfig struct
probe: present qf-studio/pilot func createPostMergeCheckout\(
probe: present qf-studio/pilot has ALREADY merged
probe: absent  qf-studio/pilot type PrePRReviewConfig struct
probe: absent  qf-studio/pilot func \(r \*Runner\) runPrePRReview\(

## Context

Pilot runs a self-review phase and an intent judge after the quality gates (`internal/executor/runner.go`, the parallel block around lines 6614–6838) and, since v2.296.0, a post-merge reviewer after autopilot merges (`internal/executor/post_merge_reviewer.go`, run by `internal/autopilot/post_merge_review.go`). Three calibration runs show the post-merge reviewer is the only stage that checks a change against the system (callers, wire producers, conventions), and that a REQUEST-CHANGES after merge costs a new issue cycle. The founder decided the review moves before the push, inside the run. This leg adds the review in shadow mode: it runs after the gates, records a verdict, writes nothing to GitHub, and already replaces the self-review phase and the in-run intent judge when its mode is not off. Default off: no behaviour change. The reviewer is the existing PostMergeReviewer with a pre-merge prompt variant and the existing detached read-only checkout from `internal/executor/post_merge_checkout.go`.

## Implementation

1. Config: new PrePRReviewConfig on BackendConfig in `internal/executor/backend.go` beside IntentJudgeConfig: mode (off, shadow, enforce; default off), model (empty = executor default), timeout (default 6m), fix_timeout (default 10m, used by a later leg), max_fix_rounds (default 1), max_diff_chars (0 = the reviewer default 200000), skip_complexity (default [trivial]). Validate in `internal/config/config.go` in the executor block: mode in the set, durations non-negative. Add EffectiveSkipSelfReview() returning true when mode is not off or skip_self_review is set.
2. Prompt variant: add PreMerge to PostMergeReviewInput in `internal/executor/post_merge_reviewer.go`. When set, Review() replaces the sentence that says the pull request has already merged with one that says the change is about to be pushed and has passed the quality gates, drops the paragraph about the PR body and its Evidence block, and renders CIResult under a heading named Gate Results. Everything else in the prompt stays byte-identical so calibration still applies.
3. Reviewer wiring: a PrePRReviewer interface (Review(ctx, PostMergeReviewInput) (*PostMergeReview, error)) satisfied by *PostMergeReviewer; build it in NewRunnerWithConfig beside the intent-judge wiring with the configured model, timeout and max_diff_chars, with the same claude LookPath warning. New file in prose: internal/executor/pre_pr_review.go with PrePRReviewOutcome (Mode, Verdict, Review, Skipped reason, Err, Duration, FilesRead) and runPrePRReview(ctx, task, executionPath, git, state, gates).
4. runPrePRReview: inputs are the task title, the issue body (task description), the full diff against origin and the base branch from the git helper, the current commit SHA from GetCurrentCommitSHA (never the literal HEAD; createPostMergeCheckout wants a resolved SHA), memories via graphrecall.RecallRelevant and the executor's renderMemoryBlock keyed on title plus description plus touched file paths, and CIResult as one line per QualityGateResult (name, passed, duration). Call Review() on a context with the configured timeout derived from the re-derived finalize context. Record one execution event with stage pre_pr_review carrying mode, verdict, blocking and minor counts, files read, duration; store the outcome on ExecutionResult.PrePRReview; log one Info line "Pre-PR review" with those fields, or "Pre-PR review skipped" with the reason.
5. Guard G1 (the review runs only when all hold): mode not off; task.CreatePR; not task.DirectCommit; task.Branch non-empty; quality gates passed or no checker factory; complexity not in skip_complexity; diff non-empty; at least 2 m left in the finalize window. A verdict of unknown or exhausted is recorded as no verdict.
6. Replace: when mode is not off, the self-review phase and the in-run intent judge do not run (gate both on EffectiveSkipSelfReview / the pre-PR mode); the self-review hygiene step still runs so the tree stays clean. Shadow mode never starts a fix round.
7. Stages: add pre_pr_review and pre_pr_fix stage constants in `internal/memory/store.go` beside the existing execution-event stages.
8. Docs: the key in `configs/pilot.example.yaml` next to intent_judge with the three modes explained, and a paragraph in `docs/content/getting-started/configuration.mdx`.
9. Tests, table-driven; fakes read their arguments (the mocks gate): the fake reviewer asserts PreMerge is true, MergeCommitSHA equals the worktree HEAD SHA, ProjectPath equals the execution path, CIResult names each gate; the recording backend (guardRecordingBackend idiom in backend_execute_guard_test.go) shows self-review still runs at mode off and does not run at mode shadow.

## Acceptance

- With mode off, a run behaves as today: the self-review backend call happens and no reviewer call happens.
- With mode shadow, after the gates pass, the reviewer is called once with PreMerge set, the worktree HEAD SHA and the execution path; the run continues to push and PR as today; no label or comment is written.
- A trivial task skips the review with reason recorded.
- `go test -race ./internal/executor/ -run TestRunPrePRReview` passes; paste the output into the PR body.
- `go test -race ./internal/executor/ -run TestPostMergeReviewerPrompt_PreMergeVariant` passes; paste the output into the PR body.
- `go test -race ./internal/config/ -run TestPrePRReviewConfig` passes; paste the output into the PR body.
- drop the PreMerge sentence swap -> TestPostMergeReviewerPrompt_PreMergeVariant fails
- pass task.ProjectPath to the reviewer instead of the execution path -> TestRunPrePRReview_Shadow_RecordsOutcomeNoFix fails
- let self-review run when mode is shadow -> TestRunPrePRReview_Shadow_SkipsSelfReview fails
- run the review when mode is off -> TestRunPrePRReview_OffIsNoop fails

## Out of scope

- Anything written to GitHub (PR body section, label) — L2.
- The fix round — L3. Retiring self-review code — L4. Autopilot hold — L5. Sampling — L6.

## Refs

- .agent/tasks/TASK-620-pre-pr-reviewer-replaces-self-review-and-judge.md
- .agent/system/bench/post_merge_reviewer_calibration_2026-10.md

### LEG L2 — repo: qf-studio/pilot — title: feat(executor): pre-PR verdict in the PR body, pilot-review-rc label on a REQUEST-CHANGES, pr_reviews row as pre-pr-reviewer, and counters
probe: present qf-studio/pilot func ghAddLabels\(
probe: present qf-studio/pilot func \(s \*Store\) UpsertPRReview\(
probe: absent  qf-studio/pilot func RenderPrePRReviewSection\(

## Context

Depends on #5949. The pre-PR review (shadow mode) records a verdict on the execution result but writes nothing anyone can see. This leg makes the verdict visible and comparable: a section in the PR body, a label when the verdict is REQUEST-CHANGES, a row in the pr_reviews ledger under a distinct reviewer id so shadow runs can be compared with the post-merge reviewer's rows on the same PR, and two counters. The PR body section must be machine-parseable, because autopilot (L5) and the post-merge sampler (L6) read it; the parser follows the LiveSmokeNotVerifiedBullets idiom in `internal/executor/acceptance_evidence.go`.

## Implementation

1. New file in prose: internal/executor/pre_pr_review_render.go with RenderPrePRReviewSection(outcome) producing an H2 "Pre-PR review" with Mode, Verdict, each defect on one line in the post-merge format with its severity tag, a Not-verified list, a Fix line (reserved; "none" until L3), and ParsePrePRReviewSection(prBody) returning mode, verdict, fix outcome and ok.
2. In `internal/executor/runner.go`, append the section at the three PR-body build sites after appendAcceptanceEvidence (direct GitHub, MR creator, gh CLI). After CreatePR returns a URL: when the verdict is REQUEST-CHANGES call ghAddLabels on the PR number with pilot-review-rc (extractPRNumberFromURL from `internal/executor/git.go`); upsert a pr_reviews row through r.logStore.UpsertPRReview with reviewer id pre-pr-reviewer (new const beside the post-merge id in `internal/executor/post_merge_reviewer.go`), state COMMENTED, review_id = the negated 62-bit FNV-64 of execution id plus ":pre-pr" (post-merge rows negate the comment id; pre-PR has none), verdict through a shared LedgerVerdict helper moved from autopilot (autopilot delegates to it). The learning string gains "Pre-PR review: verdict".
3. New file in prose: internal/executor/pre_pr_review_metrics.go with mutex-map counters exported from `internal/gateway/prometheus.go` as pilot_pre_pr_reviews_total by verdict and pilot_pre_pr_fixes_total by outcome (outcome labels reserved for L3).
4. Tests, table-driven: render and parse round trip; label added only on REQUEST-CHANGES (gh shim on PATH as the title-rejection tests do); ledger row with a real temp store asserting reviewer id, negative review_id and pr_number; the prometheus families appear.

## Acceptance

- A shadow run that ends REQUEST-CHANGES produces a PR whose body has the Pre-PR review section and the pilot-review-rc label, and a pr_reviews row with reviewer pre-pr-reviewer.
- A shadow run that ends APPROVE-WITH-NOTES produces the section and no label.
- `go test -race ./internal/executor/ -run TestRenderPrePRReviewSection` passes; paste the output into the PR body.
- `go test -race ./internal/executor/ -run TestPrePRReviewLedgerRow` passes; paste the output into the PR body.
- `go test -race ./internal/executor/ -run TestPrePRReviewLabel` passes; paste the output into the PR body.
- add the label on APPROVE-WITH-NOTES too -> TestPrePRReviewLabel_OnlyOnRC fails
- use a positive review_id -> TestPrePRReviewLedgerRow_ShadowWritesPrePRReviewerID fails
- change the section heading -> TestParsePrePRReviewSection_RoundTrip fails

## Out of scope

- The fix round, the autopilot hold, sampling.

## Refs

- #5949

### LEG L3 — repo: qf-studio/pilot — title: feat(executor): pre-PR review fix round in enforce mode — one session-resumed fix on blocking defects, one gate re-check, reset to the pre-fix SHA on failure
probe: present qf-studio/pilot ResumeSessionID
probe: present qf-studio/pilot func buildRetryPrompt\(
probe: absent  qf-studio/pilot func \(r \*Runner\) runReviewFix\(

## Context

Depends on #L2NUM. In enforce mode a REQUEST-CHANGES with at least one blocking defect gets one fix attempt in the same conversation before the push. The executor already holds the session id from the stream init event (BackendResult.SessionID) and the claude-code backend supports --resume (`internal/executor/backend_claudecode.go`, with the GH-2377 fallback that retries without resume when the session is gone); the box runs with use_session_resume on. The gate-retry prompt builder in `internal/executor/prompt_builder.go` (buildRetryPrompt) tells the model to delete its approach and start over, so it must not be reused: the fix prompt is narrow. The fix call must go through r.backendExecute, which enforces ProjectPath equals the execution path (the GH-4702 phantom-reimplementation guard); never the reviewer's confined environment. Budget: the fix runs only when at least 12 minutes of task time remain, on a context that is the minimum of fix_timeout and the remaining time; the re-gate runs on a fresh 5-minute context like the GH-4876 retry pass; everything after already runs on detached windows, so push, evidence and PR creation cannot starve (the GH-5861/5867 class).

## Implementation

1. New file in prose: internal/executor/pre_pr_fix.go with runReviewFix(taskCtx, taskCtxWasDone, task, executionPath, git, state, outcome) returning ReviewFixOutcome (Status one of fixed, no_change, skipped_ctx, skipped_budget, failed, reverted, regate_error; PreFixSHA; PostFixSHA; Fixed list; Elapsed).
2. Guard G2: mode enforce, verdict REQUEST-CHANGES, at least one blocking defect, rounds below max_fix_rounds, not taskCtxWasDone, taskCtx not done, and (no deadline or at least 12 m remain). fixCtx = WithTimeout(WithoutCancel(taskCtx), min(fix_timeout, remaining)) with the cancel propagation idiom from finalizeCtx.
3. The fix call: r.backendExecute with a new buildReviewFixPrompt in `internal/executor/prompt_builder.go` listing the blocking defects as file:line, claim, evidence, then "fix only these; no refactor; no new files unless a defect needs one; do not delete tests; commit; end with REVIEW_FIXED: list or REVIEW_UNFIXABLE: reason"; ExecuteOptions with ResumeSessionID = state.sessionID when the backend config has use_session_resume, the executor's tool options, the liveness policy, the heartbeat and an event handler that extracts commit SHAs. Dead-man attempt, success and failure events around it; rename the self-review tracker in `internal/executor/alerts.go` to a review_fix tracker and update its registration in `cmd/pilot/poller_github.go`.
4. Tree hygiene: generalise the self-review hygiene in `internal/executor/self_review_hygiene.go` into a phase-named helper; the fix round's commit message is "chore(review-fix): apply pre-PR review fixes"; it runs in worktree mode too, because the worktree is what gets pushed. No commit after the fix means no_change: the tree is reset and the verdict stays REQUEST-CHANGES.
5. Guard G3 re-gate: only when HEAD moved; the quality checker's Check on a fresh 5-minute context. G4: on not passed or error, git ResetHardToCommit to PreFixSHA (the idiom around runner.go line 6327), status reverted, verdict stays REQUEST-CHANGES.
6. The PR body's Fix line (L2 renderer) carries the status; the pre-PR note that the self-review path used to add is now fed by the fix round. The execution event for stage pre_pr_fix carries status, both SHAs and elapsed; counters by outcome.
7. Tests, table-driven with the guardRecordingBackend idiom (fakes read their arguments): the fix call carries ResumeSessionID and the execution path and the prompt lists each blocking file:line; skipped when the task context is done; skipped under 12 minutes remaining; the fix context deadline is the minimum of fix_timeout and remaining; a failed re-gate resets HEAD to PreFixSHA in a real temp repo; no commit is no_change; the tracker name.

## Acceptance

- In enforce mode a REQUEST-CHANGES with a blocking defect leads to exactly one more backend call that resumes the session and runs in the execution path, followed by one gate check.
- When the re-gate fails, HEAD equals the pre-fix SHA and the verdict stays REQUEST-CHANGES.
- When fewer than 12 minutes of task time remain, no fix call happens and the outcome says skipped_budget.
- `go test -race ./internal/executor/ -run TestReviewFix` passes; paste the output into the PR body.
- drop the 12-minute floor -> TestReviewFix_SkippedUnder12mRemaining fails
- reset to HEAD instead of the pre-fix SHA -> TestReviewFix_RegateFailureResetsToPreFixSHA fails
- call the backend with task.ProjectPath -> TestReviewFix_UsesResumeSessionAndExecutionPath fails
- reuse buildRetryPrompt for the fix -> TestReviewFix_PromptListsBlockingDefectsOnly fails

## Out of scope

- A second review pass after the fix (max_fix_rounds stays 1). Retiring the old phases — L4.

## Refs

- #L2NUM

### LEG L5 — repo: qf-studio/pilot — title: feat(autopilot): a PR labelled pilot-review-rc whose pre-PR review section says REQUEST-CHANGES escalates to awaiting_approval from handleCIPassed, escalate-only and fail-open
probe: present qf-studio/pilot func SizeFloorReason\(
probe: present qf-studio/pilot func LiveSmokeNotVerifiedBullets\(
probe: absent  qf-studio/pilot func PreReviewReason\(

## Context

Depends on #L2NUM (the section parser). When the pre-PR review ends REQUEST-CHANGES and the run pushes anyway, a human must decide before the merge. Autopilot's handleCIPassed in `internal/autopilot/controller.go` already runs an escalate-only chain (size floor, scope drift, test evidence, live smoke) that sets an escalation reason and moves the PR to awaiting_approval (`internal/autopilot/scope_guard.go` documents the pattern: gates only escalate, never relax). The PR body is already fetched there for the live-smoke hold. This leg adds one more reason from the Pre-PR review section. Per the founder decision, a section whose Fix line says fixed does not hold: a clean fix round merges on green and the post-merge audit samples it.

## Implementation

1. PreReviewReason(logger, prBody) in `internal/autopilot/scope_guard.go` beside SizeFloorReason: parse the section with the executor's ParsePrePRReviewSection; return a reason prefixed "Pre-PR review requested changes:" only when the verdict is REQUEST-CHANGES and the fix outcome is not fixed; empty for APPROVE, APPROVE-WITH-NOTES, a fixed outcome, a missing section or a parse failure (fail-open).
2. In handleCIPassed, after the live-smoke block and using the already fetched PR body, append the reason to the escalation chain; record an execution event from ci_passed to awaiting_approval with the reason; the approval release path is the existing one.
3. Tests, table-driven: the reason function over the verdict and fix variants; handleCIPassed with a fake GitHub client returning a body with the section ends in awaiting_approval with the reason set (model: the live-smoke test in gh5568_test.go); a GetPullRequest error does not escalate.

## Acceptance

- A PR whose body section says REQUEST-CHANGES with no fix goes to awaiting_approval with a reason that starts with "Pre-PR review requested changes".
- A PR whose section says REQUEST-CHANGES with Fix: fixed merges on green.
- `go test -race ./internal/autopilot/ -run TestPreReviewReason` passes; paste the output into the PR body.
- `go test -race ./internal/autopilot/ -run TestHandleCIPassed_PreReview` passes; paste the output into the PR body.
- return a reason for APPROVE-WITH-NOTES -> TestPreReviewReason_RCBlocksMergeOnlyWhenRC fails
- hold when the fix outcome is fixed -> TestPreReviewReason_FixedDoesNotHold fails

## Out of scope

- Any change to the approval channel or the size guard.

## Refs

- #L2NUM

### LEG L4 — repo: qf-studio/pilot — title: refactor(executor): retire the self-review phase and the in-run intent judge now that the pre-PR review covers both; keep the pre-flight issue judge
probe: present qf-studio/pilot func \(r \*Runner\) runSelfReview\(
probe: present qf-studio/pilot func buildSelfReviewPrompt\(
probe: present qf-studio/pilot func \(j \*IntentJudge\) JudgeIssue\(

## Context

Depends on #L3NUM and on the enforce exit criteria in TASK-620 (do not dispatch before the founder marks them met). With the pre-PR review and its fix round live, the self-review phase (runSelfReview in `internal/executor/runner.go`, buildSelfReviewPrompt in `internal/executor/prompt_builder.go`) and the in-run intent judge (Judge in `internal/executor/intent_judge.go`, wired in the runner's parallel block) duplicate work: the self-review's build and lint checks are the quality gates, and the judge's text-only verdict reaches only a log string and a Telegram line. The pre-flight issue judge (JudgeIssue, used by `cmd/pilot/poller_github.go`) stays; IntentWarning stays because the pre-push lint path also writes it.

## Implementation

1. Delete runSelfReview and its caller block, buildSelfReviewPrompt, the in-run Judge call, the judge wiring, SetIntentJudge, HasIntentJudge and the intentRetried state; keep the pre-PR review call in their place; keep JudgeIssue and the diff payload helpers in `internal/executor/intent_judge.go`.
2. Config: skip_self_review and self_review_timeout become deprecated no-op keys with a one-line comment in `internal/executor/backend.go` and the example YAML; intent_judge stays for the pre-flight judge.
3. Rename the self-review hygiene and tracker names to the review-fix ones left by L3; update `cmd/pilot/handlers.go` where the warning line is built.
4. Tests: remove or port the self-review and in-run judge tests (the expired-context assertion from the GH-5342 test moves onto the fix round's skipped test); add a test that after the gates exactly one backend call can follow (the fix round) and that the pre-flight judge is still wired.

## Acceptance

- No backend call named self-review happens after the gates in any mode; the pre-flight issue judge still runs at admission.
- `go test -race ./internal/executor/ -run TestNoSelfReviewBackendCallAfterGates` passes; paste the output into the PR body.
- `go test -race ./cmd/pilot/ -run TestIntentJudgePreflightStillWired` passes; paste the output into the PR body.
- re-add a self-review backend call after the gates -> TestNoSelfReviewBackendCallAfterGates fails

## Out of scope

- Sampling (L6). Any change to the pre-flight judge.

## Refs

- #L3NUM

### LEG L6 — repo: qf-studio/pilot — title: feat(autopilot): post-merge review sampling — post_merge_review.sample_rate reviews one PR in N, always reviews a PR whose pre-PR review was not an enforce-mode approve
probe: present qf-studio/pilot type PostMergeReviewConfig struct
probe: present qf-studio/pilot func \(c \*Controller\) maybeStartPostMergeReview\(
probe: absent  qf-studio/pilot EffectiveSampleRate\(

## Context

Depends on #L5NUM and on the enforce exit criteria. Once the pre-PR review carries the load, the post-merge reviewer becomes an audit: it samples one merged PR in N to measure the pre-PR reviewer, and always reviews the PRs the pre-PR review did not clear — section missing, mode not enforce, verdict not an approve, fix outcome not clean, or the PR body could not be fetched. PostMergeReviewConfig lives in `internal/autopilot/types.go`; the start decision is maybeStartPostMergeReview in `internal/autopilot/post_merge_review.go`, where the daily budget is acquired. Sampling by PR number modulo N is restart-safe; a counter is not.

## Implementation

1. SampleRate on PostMergeReviewConfig with EffectiveSampleRate (0 or 1 = every PR); validate non-negative in `internal/config/config.go` beside daily_cap.
2. In maybeStartPostMergeReview, after the PostMergeReviewPosted check and before the budget is acquired: fetch the PR body once, parse the Pre-PR review section with the executor parser, compute forced as described; when not forced and PR number modulo N is not zero, record the metric label sampled_out, log one Info line and return without consuming the budget.
3. Metric help text in `internal/gateway/prometheus.go`; the key in `configs/pilot.example.yaml` under post_merge_review.
4. Tests, table-driven with a fake reviewer that reads the PR number: one in N over ten PR numbers; forced on each section variant; forced on a fetch error; a sampled-out PR leaves the budget unchanged.

## Acceptance

- With sample_rate 5, PRs 5 and 10 of 1..10 are reviewed and the others are sampled out, unless their pre-PR section forces a review.
- A sampled-out PR does not consume the daily budget.
- `go test -race ./internal/autopilot/ -run TestPostMergeReviewSampling` passes; paste the output into the PR body.
- move the sample check after the budget acquire -> TestPostMergeReviewSampling_SampledOutDoesNotConsumeBudget fails
- drop the forced path -> TestPostMergeReviewSampling_ForcedOnRCOrShadow fails

## Out of scope

- Changing the audit's prompt, cap or timeout.

## Refs

- #L5NUM

## Budget arithmetic (complex task, 60 m)

| Case | Impl | Gates | Review | Left | Fix | Re-gate | Added wall-clock |
|---|---|---|---|---|---|---|---|
| fast impl, RC | 35 | 5 (t=40, 20 m left) | 6 (t=46) | 14 ≥ 12 → fix | min(10, 14) = 10 (t=56) | fresh 5 m | ≤ 21 m; finalize/evidence/PR on detached windows as today |
| slow impl, RC | 50 | 5 (t=55, 5 m left) | 6 on the detached window | < 12 → fix skipped | — | — | +6 m, RC pushed, approval hold |
| APPROVE | any | | +6 | | — | — | +3 m net (self-review 2 m + judge 1 m retired) |

## Rollout and exit criteria
1. Shadow on the box after L1+L2 (`executor.pre_pr_review.mode: shadow`; post-merge unchanged): compare `pr_reviews` rows by (project_path, pr_number) across reviewer ids pre-pr-reviewer and post-merge-reviewer.
2. Shadow → enforce (≥ 20 PRs, ≥ 5 working days): error+unknown+exhausted ≤ 10 %; verdict-class agreement ≥ 70 %; pre-PR RC rate 10–40 %; median added minutes ≤ 7; zero new deadline failures at CreatePR.
3. Enforce (L3+L5; `mode: enforce`), next 20 merges: fixed ≥ 50 % of RC runs; reverted ≤ 20 %; post-merge RC on pre-PR-approved PRs ≤ 1 per 10; pilot-review-rc holds ≤ 2 per 10; median added minutes ≤ 12; no ErrProjectPathNotIsolated in logs.
4. Then L4 and L6 (`sample_rate: 5`).

## Box log lines to watch
`Pre-PR review` (task_id verdict defects blocking memories checkout files_read duration mode) · `Pre-PR review skipped` (reason) · `Pre-PR review fix` (status pre_fix_sha post_fix_sha elapsed) · `Pre-PR review: labelled pilot-review-rc` · autopilot `merge gate escalated … Pre-PR review requested changes:` · `post-merge review sampled out`.

## Refs

- L1 → https://github.com/qf-studio/pilot/issues/5949
