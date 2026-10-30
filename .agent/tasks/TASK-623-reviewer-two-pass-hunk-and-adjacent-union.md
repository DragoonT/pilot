# TASK-623: Reviewer two passes — a hunk pass and an adjacent pass, defects united by location, verdict from the union

**Status**: 🚀 P1 DISPATCHED 2026-10-30 → pilot#5977 (`pilot`+`no-decompose`). Was: 📋 PLANNED 2026-10-30 (founder "two passes" after calibration run 5). Measure = run 6 on the same 14 PRs with `--passes 2`; pass bar unchanged (RC 3/3 · recall ≥ 0.5 · false ≤ 1); also report pass-A-only and pass-B-only recall from the same JSONs.
**Origin**: runs 4 and 5 (`system/bench/post_merge_reviewer_calibration_2026-10.md`): one pass finds 18–19 of 52 hand defects at ~5 files and ~70 s whatever the prompt tells it to look at. Run 5's adjacent-code item moved 5 misses to hits and 7 hits to misses (in-hunk items displaced): a fixed finding budget redistributed. The union of run 4 and run 5 outputs would have hit 24 + the partials — that is the number this task buys with a second pass.
**Spec refs**: `internal/executor/post_merge_reviewer.go` (`Review`, `PostMergeReview`, `PostMergeDefect{Severity, Location, Claim, Evidence}`, `parsePostMergeReview`, `enforcePostMergeCitations`, `downgradePostMergeNoFilesRead`, `postMergeChecklistItemAdjacent`, `SetMaxDiffChars` setter idiom, `postMergeReviewMaxTurns`), callers `internal/autopilot/post_merge_review.go` (daemon), `internal/executor/pre_pr_review.go` (pre-PR), `cmd/pilot/review_merge.go` (CLI JSON: `verdict`, `defects`, `not_verified`, `notes`, `files_read`, `duration_ms`), config `internal/autopilot/types.go` (`PostMergeReviewConfig`), `internal/executor/backend.go` (`PrePRReviewConfig`), `internal/config/config.go` (`validatePrePRReview`).

## Why two passes and not more turns
- Run 5 raised max-turns 30 → 40; files_read stayed 5.0 → 5.1 and time 68 → 72 s. The model stops when it has a verdict, not when the budget ends. A bigger budget alone is unlikely to change what it opens.
- Two passes with two different reading orders are the cheapest way to make the model open both the hunk and the one-hop neighbourhood. Cost: ~2× time (~140 s) and ~2× tokens per review. Pre-PR has a 6 m budget, post-merge 5 m: both fit two 70 s passes.
- The union must be deduplicated by location so one PR does not get the same defect twice, and the verdict must come from the union's severities, not from either pass's VERDICT line.

## Legs — pilot (daemon)

### LEG P1 — repo: qf-studio/pilot — title: feat(executor): post-merge and pre-PR reviewer run two passes — a hunk pass and an adjacent pass — and unite the defects by location with the verdict derived from the union; passes knob on both configs and the CLI
probe: present qf-studio/pilot ^func \(r \*PostMergeReviewer\) Review\(
probe: present qf-studio/pilot ^const postMergeChecklistItemAdjacent
probe: present qf-studio/pilot ^func \(r \*PostMergeReviewer\) SetMaxDiffChars\(
probe: absent  qf-studio/pilot ^func \(r \*PostMergeReviewer\) SetPasses\(

## Context

The reviewer in `internal/executor/post_merge_reviewer.go` runs one claude invocation per review: Review builds the system prompt (checklist items 1–5, item 2b from TASK-622 when a checkout exists, memories, the pre-merge sentence swap), runs it on the confined checkout, parses the VERDICT / DEFECTS / NOT-VERIFIED / NOTES text with parsePostMergeReview, enforces citations, downgrades when no file was read, and returns one PostMergeReview with FilesRead and Turns. Five calibration runs on the same 14 hand-reviewed PRs show the pass finds 18 to 19 of 52 hand defects at about 5 files read and 70 seconds, independent of the prompt: run 5's adjacent-code item (2b) turned 5 misses into hits and 7 hits into misses. The two reading orders find different defects; their union would have scored about 24 hits. The same Review method serves the daemon (`internal/autopilot/post_merge_review.go`), the pre-PR review (`internal/executor/pre_pr_review.go`, shadow mode, 6 minute budget) and the calibration CLI (`cmd/pilot/review_merge.go`, `--json`). Defects carry Severity, Location (file:line), Claim and Evidence; the verdict rule in the prompt is REQUEST-CHANGES only with a blocking defect, APPROVE-WITH-NOTES with minor defects or a non-empty NOT-VERIFIED list, APPROVE otherwise.

## Implementation

1. Add a `passes` setting (1 or 2, default 1) to PostMergeReviewConfig in `internal/autopilot/types.go` and to PrePRReviewConfig in `internal/executor/backend.go`, validated in `internal/config/config.go` beside the existing fields, documented in `configs/pilot.example.yaml` next to each block; a SetPasses setter on PostMergeReviewer in the SetMaxDiffChars idiom; the three construction sites pass the value through; `pilot review-merge` gains `--passes` (default from config, override 1 or 2).
2. Split the prompt into two variants built from the existing pieces: pass A (hunk) = the run-4 prompt — checklist items 1 to 5 with the TASK-619 item 2 and no item 2b; pass B (adjacent) = the same prompt with item 2b in place of item 2 and one added sentence: "The hunk itself has already been reviewed; spend your reads on the sibling functions, the untouched branches and the preflight or guard before each changed call." Keep every other sentence identical so the citation, severity and output rules apply to both.
3. In Review, when passes is 2, run pass A and then pass B on the same checkout and confinement (one checkout, one HOME, two claude invocations, each with its own max-turns and a share of the timeout: pass A gets the first half of the remaining time, pass B the rest, and a pass that times out contributes nothing but is recorded). Parse, enforce citations and apply the no-files-read downgrade per pass as today.
4. Unite: defects from both passes keyed by normalised Location (path with the checkout prefix stripped, line kept; a defect without a line keys on path plus the first 40 characters of the claim); on a key collision keep the higher severity and the longer evidence. NOT-VERIFIED lines are united as a set; NOTES are concatenated with a pass label. The verdict is derived from the union by the prompt's own rule (blocking present → REQUEST-CHANGES; any defect or any NOT-VERIFIED → APPROVE-WITH-NOTES; else APPROVE); the per-pass VERDICT lines are kept only in the raw output. Downgraded stays true when both passes were downgraded.
5. Record per-pass stats on PostMergeReview (FilesReadByPass, TurnsByPass, DurationByPass, DefectsByPass, and the overlap count) and surface them in the CLI JSON as `passes`, `files_read_by_pass`, `duration_ms_by_pass`, `defects_by_pass`, `overlap`; the daemon log line gains passes and overlap; the pre-PR execution event gains passes.
6. Tests, table-driven with the existing fake runner idioms: union keeps the higher severity on a collision; union of a blocking from pass B and minors from pass A yields REQUEST-CHANGES even when pass A said APPROVE; passes=1 produces byte-identical prompt and result to today; pass B timeout leaves pass A's result with passes recorded as 2 and the second pass marked failed; the pre-merge variant applies to both passes; the CLI JSON carries the per-pass fields.

## Acceptance

- With passes set to 2, one review makes exactly two claude invocations against one checkout, and the returned defects are the deduplicated union of both.
- With passes set to 1 (the default), the prompt and the result are unchanged from today.
- `go test -race ./internal/executor/ -run TestPostMergeReviewTwoPass` passes; paste the output into the PR body.
- `go test -race ./internal/executor/ -run TestPostMergeReviewer_PromptContract` passes; paste the output into the PR body.
- `go test -race ./cmd/pilot/ -run TestReviewMergePasses` passes; paste the output into the PR body.
- derive the verdict from pass A instead of the union -> TestPostMergeReviewTwoPass_VerdictFromUnion fails
- key the union on claim text instead of location -> TestPostMergeReviewTwoPass_UnionDedupesByLocation fails
- run pass B on a second checkout -> TestPostMergeReviewTwoPass_OneCheckout fails

## Out of scope

- Changing the checklist text of either pass beyond the one added sentence.
- Sampling (TASK-620 L6), enforce mode, the fix round.
- The box config switch (operator step below).

## Refs

- .agent/tasks/TASK-623-reviewer-two-pass-hunk-and-adjacent-union.md
- .agent/system/bench/post_merge_reviewer_calibration_2026-10.md
- .agent/tasks/TASK-622-reviewer-adjacent-code-tracing-and-met-failure-case.md

## Operator steps (after the leg merges and a release lands)

1. Run 6 on the box: copy `~/calibration-v5/calib.sh` to `~/calibration-v6/` (sed the path) and add `--passes 2` to the review-merge command; same 14 PRs; pull the JSONs; score with the run-5 scorer prompt verbatim. Report recall for the union and, from the per-pass fields, for pass A alone and pass B alone.
2. Pass bar: RC 3/3 · recall ≥ 0.5 · false ≤ 1. Expected from the run-4/run-5 union: about 24 HIT + partials ≈ 50–52 %.
3. If the union clears the bar: box `post_merge_review.passes: 2` and `executor.pre_pr_review.passes: 2`, then watch mean time (expect ~140 s; cap 20/day unchanged) and the pre-PR 6 m budget.
4. If the union does not clear the bar: the remaining misses are two hops out or in notes-only hand reviews; that is a different class and not another pass.

## Refs

- P1 → https://github.com/qf-studio/pilot/issues/5977
