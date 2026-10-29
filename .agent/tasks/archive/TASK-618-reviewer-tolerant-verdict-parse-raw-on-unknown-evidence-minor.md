# TASK-618: post-merge reviewer — tolerant verdict parsing, raw output kept on unknown, files-read in the CLI output, and PR-body evidence gaps are minor

**Status**: ✅ MERGED 2026-10-29 — pilot#5946 → PR#5948 merged 13:05Z, post-merge review (Opus) APPROVE-WITH-NOTES (minor: stripPostMergeMarkup trims trailing markers too; the RawOutput mutation bullet only holds for the CLI site). Rides v2.299.0. Was: 🚀 DISPATCHED 2026-10-29 → pilot#5946 (`pilot`+`no-decompose`). From calibration run 3 (Opus): 2 of 14 reviews came back `unknown` with the model output discarded; runs 1–3 all over-escalate on PR-body evidence bullets.
**Spec refs**: `internal/executor/post_merge_reviewer.go` (parsePostMergeReview ~406: verdict must be the first non-empty line, regex `^VERDICT:`; system prompt ~135), `cmd/pilot/review_merge.go` (~229 returns "reviewer output did not follow the contract" and prints nothing else), `internal/autopilot/post_merge_review.go` (unknown → metric + skip, no text logged); TASK-591 note "markdown-wrapped VERDICT → unknown (watch the counter)"; bench report `.agent/system/bench/post_merge_reviewer_calibration_2026-10.md`.
**Origin**: founder switched the reviewer to claude-opus-5-5 on 2026-10-29 12:17Z.

## Why
- Run 3 (Opus): pilot#5872 and ui#246 returned `unknown`. The CLI printed only "reviewer output did not follow the contract (verdict unknown)"; the daemon path would count a metric and post nothing. The model's text is gone, so the cause is a guess (the TASK-591 note predicted a markdown-wrapped VERDICT line).
- Runs 1–3: four of five REQUEST-CHANGES on human-approved PRs rest on one [blocking] item about PR-body evidence (make output missing or showing a pre-existing lint failure). The human waived those via CI. That blocker drives the review→fix→review loop (10-28 evening: #5929/#5932/#5934/#5937/#5940/#5943).
- Nothing records how many files the reviewer read from its checkout in the CLI path (the posted comment carries it; the JSON and the log do not), so tool use cannot be measured offline.

## Legs — pilot (daemon)

### LEG P1 — repo: qf-studio/pilot — title: fix(autopilot): post-merge reviewer parses a markdown-wrapped or preceded VERDICT line, keeps the raw output on unknown, reports files read in the CLI JSON, and treats PR-body evidence gaps as minor
probe: present qf-studio/pilot func parsePostMergeReview\(text string\)
probe: present qf-studio/pilot reviewer output did not follow the contract
probe: absent  qf-studio/pilot RawOutput string

## Context

The post-merge reviewer's parser in `internal/executor/post_merge_reviewer.go` requires the first non-empty line of the model output to match a strict VERDICT regex; anything else yields the unknown verdict, and both callers — autopilot in `internal/autopilot/post_merge_review.go` and the CLI in `cmd/pilot/review_merge.go` — discard the text. On 2026-10-29 the reviewer model was switched to claude-opus-5-5 and two of fourteen calibration reviews came back unknown; the model output was not kept, so the failure cannot be diagnosed. The TASK-591 review already named a markdown-wrapped VERDICT line as the likely shape. Separately, three calibration runs show the reviewer escalating human-approved merges to REQUEST-CHANGES on one [blocking] item about PR-body evidence (make output missing, or a pre-existing lint failure in the paste), which the human waived via CI; that blocker is what makes the review→fix→review loop fire on bookkeeping. And the CLI JSON does not report how many files the reviewer read from its checkout, although the posted comment does, so offline runs cannot measure tool use.

## Implementation

1. Tolerant verdict parse: before matching, strip leading markdown emphasis and heading markers (asterisks, underscores, backticks, pound signs, bullet dashes) and surrounding whitespace from each line; accept the first line within the first ten non-empty lines that matches VERDICT; treat any text before it as preamble and ignore it. Section headers DEFECTS, NOT-VERIFIED and NOTES get the same stripping. Keep the downgrade rule for a REQUEST-CHANGES without a [blocking] defect.
2. Raw output kept: add RawOutput to PostMergeReview, filled on every parse. On unknown, the autopilot path logs the first 2000 characters at Warn with the PR number and increments the existing unknown metric; the CLI prints "verdict unknown" plus the raw output to stderr and, with --json, includes raw_output in the object. Never post raw output to GitHub.
3. Files read in the CLI: the review-merge JSON carries files_read and checkout (true/false) from the same counters the posted comment uses; the text output prints them on the Diff line.
4. Severity rule in the system prompt: an acceptance bullet about pasted build, test or lint output is [minor] unless the pasted output shows a failing test or build for code the diff changed; a pre-existing failure in an unrelated package is [minor] with the package named. State it in the blocking definition list.
5. Tests, table-driven: parser cases for a `**VERDICT: X**` line, a `# VERDICT: X` line, a one-line preamble before VERDICT, and a verdict beyond the tenth line (still unknown); RawOutput populated on unknown and on a good parse; the CLI JSON has files_read, checkout and raw_output on unknown; a prompt test that the blocking definition contains the evidence rule. Fakes read their arguments.

## Acceptance

- A model output whose first line is `**VERDICT: APPROVE-WITH-NOTES**` parses to APPROVE-WITH-NOTES.
- A model output with one sentence before the VERDICT line parses to that verdict.
- On an unparseable output the CLI prints the raw text to stderr and exits non-zero, and the autopilot log carries the first 2000 characters.
- The review-merge JSON contains files_read and checkout.
- `go test -race ./internal/executor/ -run TestParsePostMergeReviewTolerant` passes; paste the output into the PR body.
- `go test -race ./cmd/pilot/ -run TestReviewMergeUnknownKeepsRaw` passes; paste the output into the PR body.
- drop the emphasis stripping -> TestParsePostMergeReviewTolerant_MarkdownWrapped fails
- drop the preamble skip -> TestParsePostMergeReviewTolerant_PreambleLine fails
- stop filling RawOutput on unknown -> TestReviewMergeUnknownKeepsRaw fails

## Out of scope

- Changing the checklist beyond the evidence severity rule.
- The daily cap, timeout or budget.

## Refs

- .agent/system/bench/post_merge_reviewer_calibration_2026-10.md
- https://github.com/qf-studio/pilot/pull/5868

## Refs

- P1 → https://github.com/qf-studio/pilot/issues/5946
