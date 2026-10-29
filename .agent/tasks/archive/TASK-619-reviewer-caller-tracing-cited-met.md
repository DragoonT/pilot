# TASK-619: post-merge reviewer traces callers and producers in the checkout — "met" needs a file:line citation from the checkout, 30 turns, files-read as a gate

**Status**: ✅ MERGED 2026-10-29 — pilot#5947 → PR#5950 merged 13:59Z (gates failed once, retried), post-merge review (Opus) APPROVE-WITH-NOTES. Notes worth a follow-up, NOT filed: (1) at the NOT-VERIFIED cap of 3 the untraced count overwrites the model's last entry; (2) an uncited DEFECTS line containing "met" is moved to NOT-VERIFIED and a REQUEST-CHANGES is lowered even when it is a real [blocking] finding. Rides v2.299.0. Was: 🚀 DISPATCHED 2026-10-29 → pilot#5947 (`pilot`+`no-decompose`, Depends on #5946). Founder "file it" after three calibration runs (recall 39 % / 35 % / 32 %; the miss class is identical: behaviour outside the diff hunks).
**Spec refs**: `internal/executor/post_merge_reviewer.go` (system prompt and checklist ~237; "Only report a defect you can anchor to a file and line you can see"), `internal/executor/post_merge_checkout.go` (postMergeCheckoutArgs: --tools/--allowedTools Read,Grep,Glob and --max-turns from postMergeReviewMaxTurns = 12; parsePostMergeStream counts files read), bench report `.agent/system/bench/post_merge_reviewer_calibration_2026-10.md` runs 1–3; navigator-research agent rules (sample callers, cite path:line, never guess).
**Origin**: question 2026-10-28 "does Pilot use nav-research principles on review?" — it did not; the checkout (TASK-613 M2) gave it the means, the prompt never required it.

## Why
- Across runs 1–3, ~21 of 27 non-format misses are behaviour outside the hunks: pre-existing code the change interacts with, callers of a changed function, cross-repo contracts, project conventions. The model writes "met" from the diff; the human traced callers.
- v2.298.0 gives the reviewer a read-only checkout with Read, Grep and Glob, but the prompt only asks to "name" the counterpart file and allows "met" without a citation. 12 turns is enough to read two or three files.
- The only tool-use evidence in the logs so far is one denied Grep into the Go module cache. #5946 (TASK-618) adds files_read to the CLI JSON so this leg can be measured.

## Legs — pilot (daemon)

### LEG C1 — repo: qf-studio/pilot — title: feat(autopilot): post-merge reviewer must open callers and producers in the checkout and cite file:line before marking a requirement met; max-turns 30; a review that read nothing is downgraded to not-verified
probe: present qf-studio/pilot postMergeReviewMaxTurns
probe: present qf-studio/pilot Only report a defect you can anchor to a file and line you can see
probe: absent  qf-studio/pilot checkoutCitationRe

## Context

Depends on #5946 (same prompt and parser files; it adds files_read to the CLI output this leg measures with). The post-merge reviewer in `internal/executor/post_merge_reviewer.go` runs a five-item checklist over the merged diff; since v2.298.0 it runs inside a read-only worktree of the merge commit with Read, Grep and Glob allowed and --max-turns 12 (`internal/executor/post_merge_checkout.go`). Three calibration runs on 14 hand-reviewed merges (Sonnet twice, Opus once) all land at 32–39 percent defect recall against the human reviews, and the misses are the same class every time: behaviour outside the diff hunks — pre-existing code the change touches, callers of a changed function, the producer of a wire field, a cross-repo consumer, a project convention. The model marks requirements "met" from the diff alone. The prompt asks it to name the counterpart file but never to open it, and nothing checks whether it read anything. The navigator-research rules this project uses for its own investigations — sample the callers, cite path:line, never guess — were never applied to the reviewer.

## Implementation

1. Prompt, checklist additions: for every exported function or method the diff changes, Grep the checkout for its callers and open at least the first two; for every wire field read or emitted, open the producer or consumer file; for every issue requirement, cite the checkout file:line that satisfies it. A requirement may be marked "met" only with a citation of the form path:line from the checkout (the diff alone does not count); without one it goes to NOT-VERIFIED with the reason "not traced". Add the rule: a claim about code outside the diff must quote the line it rests on.
2. Turns: raise postMergeReviewMaxTurns from 12 to 30; keep the timeout; log turns used and files read on the "post-merge review" result line.
3. Gate on tool use: when the checkout was available and files_read is 0, the verdict is posted as APPROVE-WITH-NOTES with a first note "reviewer read no files from the checkout; findings rest on the diff only" and never as REQUEST-CHANGES; count it in a metric label. (It cannot block the merge; the PR is merged already.)
4. Citation check in the parser: a NOTES or DEFECTS line that says "met" without a path:line reference is rewritten into NOT-VERIFIED by the daemon, so the contract holds even when the model ignores the rule. Use one regex for the citation shape (checkoutCitationRe) and test it against the three calibration output sets.
5. Keep the evidence severity rule from #5946 and the tolerant parse untouched.
6. Tests, table-driven: prompt contains the tracing rules; a fake runner that emits a stream with N Read tool calls yields files_read N; files_read 0 with a checkout downgrades REQUEST-CHANGES to APPROVE-WITH-NOTES with the note; a "met" line without a citation moves to NOT-VERIFIED; a "met" line with path:line stays. Fakes read their arguments.
7. After merge, rerun the TASK-612 recipe on the same 14 PRs (Opus) and append run 4 to the bench report with files_read per PR.

## Acceptance

- The system prompt instructs the model to open callers and producers and to cite checkout file:line before marking a requirement met.
- The review CLI runs with --max-turns 30.
- A review with a checkout and zero files read is posted as APPROVE-WITH-NOTES with the "read no files" note, never REQUEST-CHANGES.
- A requirement line marked met without a path:line citation is moved to NOT-VERIFIED by the parser.
- `go test -race ./internal/executor/ -run TestPostMergeReviewCitation` passes; paste the output into the PR body.
- `go test -race ./internal/executor/ -run TestPostMergeReviewNoFilesReadDowngrade` passes; paste the output into the PR body.
- drop the files_read zero downgrade -> TestPostMergeReviewNoFilesReadDowngrade fails
- accept "met" without a citation -> TestPostMergeReviewCitation_UncitedMetMovesToNotVerified fails
- keep max-turns at 12 -> TestPostMergeCheckoutArgs_MaxTurns30 fails

## Out of scope

- Giving the reviewer Bash or write tools.
- Changing the daily cap or the per-review timeout.
- Reviewing PRs without a local project path (diff-only path unchanged).

## Refs

- .agent/system/bench/post_merge_reviewer_calibration_2026-10.md
- https://github.com/qf-studio/pilot/issues/5946

## Refs

- C1 → https://github.com/qf-studio/pilot/issues/5947
