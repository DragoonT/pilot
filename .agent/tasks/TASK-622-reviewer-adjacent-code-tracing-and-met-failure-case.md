# TASK-622: Reviewer prompt step 3 — adjacent-code tracing and a failure-case rule for "met"

**Status**: 📋 PLANNED 2026-10-30 (founder "plan it" after calibration run 4). One leg, not dispatched. Measure = run 5 on the same 14 PRs; pass bar unchanged (RC 3/3 · recall ≥ 0.5 · false ≤ 1).
**Origin**: run 4 (`system/bench/post_merge_reviewer_calibration_2026-10.md`): recall 44.2 % on 52 hand defects. 25 misses: ~18 are behaviour in code the diff did not touch, ~4 are in-hunk lines quoted verbatim as "met". Recall does not track files_read (5874: 7 files, 0/5). TASK-619's rule sends the extra reads to producers/consumers of wire fields — that is where run 4's new HITs came from — not to sibling functions or the pre-existing branch next to the hunk.
**Spec refs**: `internal/executor/post_merge_reviewer.go` (system prompt: checklist items 1–5, `postMergeChecklistItem2` = TASK-619 tracing, severity paragraph, `postMergeReviewMaxTurns`), `internal/executor/post_merge_citation_test.go` (`TestPostMergeReviewCitation_PromptCarriesTracingRules` pins rule sentences), `internal/executor/post_merge_reviewer_test.go` (`TestPostMergeReviewer_PromptContract`, `TestPostMergeReviewerPrompt_PreMergeVariant`), the "met" demotion in `post_merge_reviewer.go` (`postMetClaimRe`, Untraced).

## Fixtures — the run-4 misses this step targets (all in `run4/scoring.md`)

| PR | Hand defect | Where the evidence lives | Class |
|---|---|---|---|
| pilot#5874 D1 | past reset rolls +24h → 6 h pause | `ratelimit.go`, pre-existing roll next to the changed parser | adjacent branch |
| pilot#5874 D3 | `Stop()` leaves `usageLimitResumeAt` and the owner | sibling method in the same file as the armed pause | sibling function |
| pilot#5874 D2 | two alerts (runner `rate_limit` + `usage_limit_pause`) | runner's existing alert path | adjacent path |
| pilot#5870 D4 | dirty refusal unreachable from the runner in direct mode | `git_clean` preflight ahead of the changed call | caller-side pre-check |
| pilot#5822 D2 | `merged_count` is 0 for families autopilot never tracks | `merged` events written only by autopilot | cross-subsystem producer |
| pilot#5870 D2 | `GetCurrentBranch` error swallowed | the hunk itself: `if curErr == nil && current == branchName` quoted as "met" | in-hunk "met" |
| pilot#5868 D4 / pilot#5875 D2 | `CIResult` is pre-merge; reused gate output not pinned to the pushed HEAD | the hunk itself: "passes the CI status: met", "Reuse: met" | in-hunk "met" |

## Legs — pilot (daemon)

### LEG R1 — repo: qf-studio/pilot — title: feat(autopilot): post-merge reviewer opens the sibling functions and the untouched branch beside each hunk, and a "met" must name the input that would break it
probe: present qf-studio/pilot const postMergeChecklistItem2
probe: present qf-studio/pilot func TestPostMergeReviewCitation_PromptCarriesTracingRules\(
probe: present qf-studio/pilot postMergeReviewMaxTurns
probe: absent  qf-studio/pilot const postMergeChecklistItemAdjacent

## Context

Calibration run 4 of the post-merge reviewer (same 14 hand-reviewed PRs, Opus, v2.301.0) reached 44.2 percent defect recall with 0 format failures and 0.07 false notes per verdict; the bar is 0.5. Of the 25 misses, about 18 are behaviour in code the diff did not change and about 4 are hunk lines the model quoted verbatim as meeting the requirement. The TASK-619 rule in postMergeChecklistItem2 in `internal/executor/post_merge_reviewer.go` sends the reviewer to the callers and to the producer or consumer of each wire field; run 4 shows that is exactly where the new hits came from, and that files_read (2 to 7 per review) does not correlate with recall because the extra reads never go to the sibling functions in the changed file or to the pre-existing branch next to the hunk. Examples from run 4: pilot#5874 missed the +24h roll in ratelimit.go beside the changed parser and the Stop method that leaves usageLimitResumeAt set; pilot#5870 missed the git_clean preflight that makes the new dirty refusal unreachable; pilot#5870 quoted the line if curErr == nil && current == branchName as meeting the spec while that line swallows the error. The prompt is shared with the pre-PR reviewer (TASK-620, one sentence swapped), so this change moves both. The prompt sentences are pinned by TestPostMergeReviewCitation_PromptCarriesTracingRules in `internal/executor/post_merge_citation_test.go` and the contract by TestPostMergeReviewer_PromptContract in `internal/executor/post_merge_reviewer_test.go`.

## Implementation

1. Add a checklist item after item 2, as a new constant postMergeChecklistItemAdjacent, with this content: for every function the diff changes, open the whole enclosing file and read the sibling functions that touch the same state, fields or flags; for every branch the diff adds, read the pre-existing branches and early returns around it that the diff did not change, including any preflight or guard that runs before the changed call; for each requirement name the one pre-existing path that could still defeat it, with its file and line, or say "no adjacent path found" with the files read. Keep the TASK-619 item unchanged.
2. Tighten the "met" rule in the same prompt: a requirement may be written "met" only with a checkout citation (existing rule) and one sentence that names the input or state under which the cited line would fail and why it does not; quoting the hunk line is not evidence. Keep the daemon-side demotion of uncited "met" lines unchanged.
3. Raise postMergeReviewMaxTurns from 30 to 40 so the extra file reads do not starve the verdict; keep the 6 minute review timeout. If the mean review time on the box exceeds 120 seconds after the change, say so in the PR body.
4. Pin the new sentences in TestPostMergeReviewCitation_PromptCarriesTracingRules (add the three new phrases to its want list) and add TestPostMergeReviewerPrompt_AdjacentItemInBothVariants asserting the item appears in the post-merge and the pre-merge prompt.
5. Record the new item in `.agent/system/bench/post_merge_reviewer_calibration_2026-10.md` under a "Run 5 recipe" line: same 14 PRs, same scorer rules, compare against run 4.

## Acceptance

- `go test -race ./internal/executor/ -run TestPostMergeReviewCitation_PromptCarriesTracingRules` passes; paste the output into the PR body.
- `go test -race ./internal/executor/ -run TestPostMergeReviewerPrompt_AdjacentItemInBothVariants` passes; paste the output into the PR body.
- `go test -race ./internal/executor/ -run TestPostMergeReviewer_PromptContract` passes; paste the output into the PR body.
- The system prompt names the sibling-function read, the untouched-branch read and the failure-case sentence for "met".
- drop the adjacent checklist item from the pre-merge variant -> TestPostMergeReviewerPrompt_AdjacentItemInBothVariants fails
- remove the failure-case sentence from the met rule -> TestPostMergeReviewCitation_PromptCarriesTracingRules fails

## Out of scope

- The scorer, the calibration set and the hand reviews.
- Severity rules and the verdict parser.
- Any change to what the daemon posts to GitHub.

## Refs

- .agent/tasks/TASK-622-reviewer-adjacent-code-tracing-and-met-failure-case.md
- .agent/system/bench/post_merge_reviewer_calibration_2026-10.md

## Operator steps (after the leg merges and a release lands)

1. Run 5 on the box: `~/calibration-v4/calib.sh` copied to `~/calibration-v5/` (sed the path), same 14 PRs, pull the JSONs (`/tmp/pull3.sh` idiom, 3 per SSM call), score with the run-4 scorer prompt verbatim, append to the bench report with files_read and mean time.
2. Pass bar: RC 3/3 · recall ≥ 0.5 · false ≤ 1. Also report recall on the seven fixtures above by name.
3. If recall is still under 0.5 with the fixtures mostly hit, the remaining misses are cross-repo contracts and notes-only hand reviews (5870, 427); treat those as a different class, not another prompt step.
