# TASK-614: post-merge reviewer prompt and parser tuning — defects on every verdict, PR-body evidence read, severity-weighted verdict, " - " defect lines parsed, hedges capped

**Status**: 🚀 DISPATCHED 2026-10-28 → pilot#5917 (`pilot`+`no-decompose`, Depends on #5916). From the TASK-612 calibration (recall 39.4 % vs 0.5; report `.agent/system/bench/post_merge_reviewer_calibration_2026-10.md`). Founder: "yes, both" (with TASK-613 M2).
**Spec refs**: `internal/executor/post_merge_reviewer.go` (system prompt ~line 135, Review ~158, parsePostMergeReview ~228, parsePostMergeDefect ~283); the 14 raw outputs in `.agent/system/bench/post-merge-reviewer-calibration-2026-10/`.
**Origin**: five structural findings from the calibration, none of which need a checkout.

## Why (from the calibration)
- Every APPROVE-WITH-NOTES verdict had an empty defects list: the model fills DEFECTS only when it escalates, so 10 of 14 verdicts gave prose instead of an actionable list. ui#255 wrote two REQUEST-CHANGES reasons into NOTES and approved.
- About 6 of 28 misses were PR-body evidence checks it declined ("no build/test/lint output in the diff") although the PR body was in the prompt.
- 7 of 14 verdicts were REQUEST-CHANGES vs the human's 3: escalation follows checklist hits (a wire field with no producer, a failed paste), not defect weight.
- Defect lines came back as "file:line - claim - evidence"; parsePostMergeDefect splits on "," or " | ", so the claim lands inside the location field (see pilot#5799 output).
- 16 "could not see / please verify" hedges across 14 verdicts, inline in the notes.

## Legs — pilot (daemon)

### LEG T1 — repo: qf-studio/pilot — title: fix(autopilot): post-merge reviewer lists defects on every verdict, reads the PR-body evidence it is given, weighs the verdict by severity, parses dash-separated defect lines, and caps hedges in a Not-verified list
probe: present qf-studio/pilot func parsePostMergeDefect\(line string\)
probe: present qf-studio/pilot Use REQUEST-CHANGES only when there is at least one defect
probe: absent  qf-studio/pilot NOT-VERIFIED:

## Context

Depends on #5916 (it changes the same prompt and runner; this leg lands after it). The post-merge reviewer in `internal/executor/post_merge_reviewer.go` runs a fixed checklist and parses "VERDICT / DEFECTS / NOTES". A calibration on 2026-10-28 over 14 merged PRs with hand reviews measured defect recall at 39.4 percent and found five structural causes that do not need a checkout: the model fills DEFECTS only when it escalates (every APPROVE-WITH-NOTES came back with an empty list, and one REQUEST-CHANGES-worthy PR wrote its reasons into NOTES and approved); it declined PR-body evidence checks although the PR body was in the prompt; it escalated on checklist hits rather than on defect weight (7 of 14 REQUEST-CHANGES against the human's 3); it wrote defect lines with " - " separators, which parsePostMergeDefect does not split; and it padded notes with 16 inline "could not see" hedges.

## Implementation

1. Output contract: DEFECTS is always a list, on every verdict. Each defect line carries a severity prefix: "[blocking]" or "[minor]". Add a fourth section NOT-VERIFIED: a list of at most three items naming what the reviewer could not confirm and why (counterpart file not in the diff, evidence truncated). NOTES keeps only requirement-by-requirement outcomes and must not contain "could not", "please verify" or "I assume" phrasing — tell the model that hedges go to NOT-VERIFIED.
2. Verdict rule in the prompt: REQUEST-CHANGES only when at least one defect is [blocking]; APPROVE-WITH-NOTES when every defect is [minor] or when NOT-VERIFIED is non-empty; APPROVE when both lists are empty. Define blocking in the prompt: a requirement of the issue not met, a wire field with no producer, a test that proves nothing about the contract it guards, data loss in a migration, out-of-scope change that alters behaviour. Everything else is minor.
3. PR-body evidence: the prompt states that the PR body is supplied in full under its own heading and that its Evidence block is the place to check build, test, lint and adapter bullets; "not in the diff" is not an acceptable reason to skip them.
4. Parser in parsePostMergeDefect: accept " - " (space-dash-space) as a separator next to "," and " | "; strip a leading "[blocking]" or "[minor]" into a new Severity field on PostMergeDefect (default minor when absent); keep the "none" handling. parsePostMergeReview parses the NOT-VERIFIED section into a new NotVerified slice; a verdict of REQUEST-CHANGES with no [blocking] defect is downgraded to APPROVE-WITH-NOTES and logged, not dropped as unknown.
5. Posted comment in `internal/autopilot/post_merge_review.go`: render DEFECTS with the severity tag, then "Not verified" as its own short list, then Notes. The Diff line stays last.
6. Follow-up issue filing (REQUEST-CHANGES path) uses only [blocking] defects for the issue body.
7. Tests, table-driven: parser cases for ",", " | ", " - " separators and both severity tags; a REQUEST-CHANGES output with only [minor] defects downgrades; NOT-VERIFIED parsed and capped at three; the comment renderer shows the three sections. Fakes read their arguments.
8. Rerun: after merge, run the TASK-612 recipe (the 14 PRs on the box) and append the three numbers to the calibration report.

## Acceptance

- An APPROVE-WITH-NOTES verdict for a diff with one minor finding carries that finding in DEFECTS with the [minor] tag, not only in NOTES.
- An output with a REQUEST-CHANGES verdict and only [minor] defects is posted as APPROVE-WITH-NOTES with a log line naming the downgrade.
- A defect line "internal/x.go:12 - claim text - evidence text" parses into location, claim and evidence.
- The posted comment has a "Not verified" list with at most three items when the model emitted them.
- `go test -race ./internal/executor/ -run TestParsePostMergeDefectSeparators` passes; paste the output into the PR body.
- `go test -race ./internal/executor/ -run TestParsePostMergeReviewSeverity` passes; paste the output into the PR body.
- `go test -race ./internal/autopilot/ -run TestPostMergeReviewCommentSections` passes; paste the output into the PR body.
- remove the " - " separator branch -> TestParsePostMergeDefectSeparators_Dash fails
- drop the minor-only downgrade -> TestParsePostMergeReviewSeverity_MinorOnlyDowngrades fails
- let a fourth NOT-VERIFIED item through -> TestParsePostMergeReviewSeverity_NotVerifiedCap fails

## Out of scope

- A checkout or tools for the reviewer (TASK-613 M2).
- Memory injection (#5911).
- Changing the daily cap, the timeout or the diff budget.

## Refs

- https://github.com/qf-studio/pilot/pull/5868
- .agent/system/bench/post_merge_reviewer_calibration_2026-10.md

## Refs

- T1 → https://github.com/qf-studio/pilot/issues/5917
