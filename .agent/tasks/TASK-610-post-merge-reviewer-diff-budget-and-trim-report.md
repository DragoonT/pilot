# TASK-610: post-merge reviewer — own diff budget, largest-first trimming, and a trim report in the log, the prompt and the verdict

**Status**: 🚀 DISPATCHED 2026-10-28 → pilot#5906 (`pilot`+`no-decompose`). Verified by nav-research at main 44b8f7e1f.
**Spec refs**: TASK-591 (reviewer), first three live verdicts (PR#5902/#5904/#5905, 2026-10-27).
**Origin**: every verdict said "in the truncated part … I could not confirm". Verified: only PR#5902 was trimmed; #5904/#5905 "could not see" lines are counterpart files outside the diff (expected: bare `--print`, no tools).

## Why (verified)
- `internal/executor/post_merge_reviewer.go` Review() builds the prompt with buildJudgeDiffPayload(in.Diff, r.maxDiffChars); maxDiffChars = maxDiffCharsDefault from `internal/executor/intent_judge.go` = 32000, shared with the intent judge.
- buildJudgeDiffPayload trims per file with an equal share (budget / files, floor 500) and keeps the head of each file. Small files donate nothing; the floor can push the total over the cap (soft cap). No log line, no record in the verdict.
- PR#5902: 32127 bytes, 7 files → 127 bytes over → about 4.5 KB per file → the test file lost ~7.7 KB, runner.go ~3.4 KB, self_review_hygiene.go ~1.4 KB. Exactly the files the verdict could not confirm. #5904 17102 B, #5905 16696 B — sent whole.
- The system prompt forbids citing a marker as a defect but never asks the model to name what it could not see.
- `cmd/pilot/post_merge_reviewer.go` logs pmr.Model (empty) not the resolved model.

## Legs — pilot (daemon)

### LEG R1 — repo: qf-studio/pilot — title: fix(autopilot): post-merge reviewer gets its own diff budget with largest-first trimming, and reports what it trimmed in the log, the prompt and the verdict
probe: present qf-studio/pilot maxDiffCharsDefault = 32000
probe: present qf-studio/pilot func buildJudgeDiffPayload\(
probe: absent  qf-studio/pilot pmr\.MaxDiffChars
probe: absent  qf-studio/pilot DiffTrimmed

## Context

The post-merge reviewer in `internal/executor/post_merge_reviewer.go` builds its prompt with the intent judge's buildJudgeDiffPayload from `internal/executor/intent_judge.go`, under the judge's maxDiffCharsDefault of 32000 characters. Over the cap, the helper gives every file an equal share of the budget (floor 500) and keeps the head of each file with a marker. Small files do not donate their slack, the floor makes the cap soft, and nothing records that trimming happened: no log line, nothing in the posted comment, and the system prompt only tells the model not to treat a marker as a defect. On 2026-10-27 the first live verdict (PR#5902, diff 32127 bytes, 7 files) lost the tails of its three largest files and said "in the truncated part of runner.go, so I could not confirm" three times; a reader cannot tell a trimmed review from a thorough one. The two later verdicts were not trimmed. One model pass can read far more than 32 KB, and the reviewer's job is the whole diff.

## Implementation

1. Give the reviewer its own budget. The intent judge already has executor.intent_judge.max_diff_chars (IntentJudgeConfig in `internal/executor/backend.go`, default 32000); the reviewer must not share it. Add max_diff_chars to the post_merge_review config block (type in `internal/autopilot/types.go`, validation in `internal/config/config.go` next to daily_cap and timeout, example in `configs/pilot.example.yaml`): zero means the reviewer default of 200000 characters; negative is rejected with a message naming the key. Thread it to the reviewer field in `cmd/pilot/post_merge_reviewer.go`. Leave the intent judge's 32000 default unchanged.
2. Largest-first trimming with a hard cap. In `internal/executor/intent_judge.go` add a variant of buildJudgeDiffPayload that also returns a trim report (original bytes, sent bytes, file count, trimmed file paths with bytes cut). Trim bodies largest-first until the total fits; always keep each file's diff header, the --- and +++ lines and the first hunk header; the total never exceeds the cap after trimming. Keep the existing function as a wrapper with unchanged behaviour for the intent judge.
3. Prompt. In Review(), when the report says trimmed, put one line above the Merged Diff section: "Diff trimmed: sent X of Y bytes; trimmed files: a.go (N bytes cut), b.go (M bytes cut)". In the system prompt's truncation paragraph add: when content you needed was cut, list the affected files in NOTES under a "Not reviewed" bullet and do not guess at what the cut part contains.
4. Log. In Review() log one Info line with pr, budget, original bytes, sent bytes, files, trimmed files.
5. Verdict. Add DiffBytes, DiffFiles, DiffTrimmed and TrimmedFiles to the PostMergeReview struct; in `internal/autopilot/post_merge_review.go` buildPostMergeReviewComment write one line before the footer: "Diff: 32127 bytes, 7 files, trimmed: yes (3 files: …)" or "trimmed: no".
6. Resolved model. In `cmd/pilot/post_merge_reviewer.go` log the model the reviewer will pass to the CLI (the resolved value, or "cli-default" when empty), not the raw config field.
7. Tests: table-driven. The trimming helper with a seven-file fixture where three files exceed the share: the three largest are cut, the four small ones are whole, every header survives, the total is at or under the cap. The comment builder with trimmed and untrimmed reviews. Config validation for the new key.

## Acceptance

- A review of a 32127-byte seven-file diff under the default budget sends the diff whole, and the comment ends with a Diff line that says trimmed: no.
- A review under a 10000-character budget trims the largest files first, keeps every file header, stays at or under 10000 characters, and the comment's Diff line names the trimmed files.
- The log line for a trimmed review carries budget, original bytes, sent bytes and the trimmed paths.
- A negative max_diff_chars fails config validation with a message naming the key.
- `go test -race ./internal/executor/ -run TestBuildJudgeDiffPayloadReport` passes; paste the output into the PR body.
- `go test -race ./internal/autopilot/ -run TestPostMergeReviewCommentDiffLine` passes; paste the output into the PR body.
- revert to equal per-file shares -> TestBuildJudgeDiffPayloadReport_LargestFirstKeepsSmallFilesWhole fails
- drop the header-preservation branch -> TestBuildJudgeDiffPayloadReport_HeadersSurvive fails
- stop enforcing the total after the per-file floor -> TestBuildJudgeDiffPayloadReport_HardCap fails
- omit the Diff line from the comment -> TestPostMergeReviewCommentDiffLine_Trimmed fails

## Out of scope

- Changing the intent judge's own cap or trimming behaviour.
- Giving the reviewer repository tools or a working directory.
- Counterpart-file lookups (the "could not see" lines on untrimmed diffs are expected).

## Refs

- https://github.com/qf-studio/pilot/pull/5902
- https://github.com/qf-studio/pilot/pull/5868

## Refs

- R1 → https://github.com/qf-studio/pilot/issues/5906
