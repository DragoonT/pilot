# TASK-612: post-merge reviewer calibration — an offline `pilot review-merge` command, then a scored run against 14 hand-reviewed merges

**Run 6 (2026-10-30 14:13Z, v2.303.0, two passes): recall 51.0 % — BAR MET (A 34.6 / B 42.3 / union 51.0), RC 3/3, false 0.07, 162 s, 10.4 files; union mechanics need one fix leg before the box switch. Report + `run6/scoring.md`.**

**Run 5 (2026-10-30 11:22Z, v2.302.0, TASK-622 adjacent-code item): recall 43.3 % (flat), fixtures 3.5/8, 7 in-hunk HIT→MISS flips — prompt rules redistribute a fixed finding budget; next lever is budget-shaped (two passes / per-file loop / more turns). Report + `run5/scoring.md`.**

**Run 4 (2026-10-29 20:58Z, v2.301.0, Opus + TASK-618/619): RC 3/3 · recall 44.2 % (best; bar 0.5 not met) · false 0.07 · 0 format failures · over-escalation 5→3 · files_read 5.0 mean. Report + `run4/scoring.md`.**

**Status**: 📊 CALIBRATION RUN DONE 2026-10-28 14:53Z (K1 merged as PR#5912, v2.297.0 on the box). **RC caught 2/3 PASS · recall 39.4 % FAIL (threshold 0.5) · false notes 0.14/verdict PASS · 44 new valid findings · 16 hedges.** Report: `.agent/system/bench/post_merge_reviewer_calibration_2026-10.md`. Rule applied: below threshold → M2 (checkout+tools, TASK-613) gate MET (miss class = code outside the diff) + prompt/parser tuning (TASK-614 candidate). Was: Founder "calibrate" after six live verdicts (pilot PR#5902/#5904/#5905/#5907, studio-sdk PR#150/#151) were all APPROVE-WITH-NOTES with zero defects, while hand reviews on 10-22 found 3 REQUEST-CHANGES and 26 follow-ups on 10 merges.
**Spec refs**: TASK-591 (reviewer), TASK-610 (diff budget, merged PR#5907), `internal/autopilot/post_merge_review.go` runPostMergeReview (the gather path), `internal/executor/post_merge_reviewer.go` Review.
**Origin**: review-policy decision 2026-10-26 13:00Z — humans review tier-1 only once the daemon reviewer is trusted. Trust needs a measured catch rate.

## Why
- The reviewer has never produced REQUEST-CHANGES live, so the follow-up-issue path is unexercised and the catch rate is unknown.
- The only entry point is autopilot's handleMerged: there is no way to run the reviewer on a past PR without re-merging it.
- Ground truth exists: 11 merged PRs carry a hand verdict comment with a defect list; the three REQUEST-CHANGES (ui#252/#261/#255) were recorded as follow-up issues (ui#262–#266, #271, #272) and in the 2026-10-22 marker, not on the PRs.

## Labeled set (hand verdict → expected daemon verdict)
| PR | Hand verdict | Ground truth location |
|---|---|---|
| pilot-console-ui#252 | REQUEST-CHANGES (U2: orgName/poolPercentUsed bound to fields the console never sends) | not on the PR — follow-up issue ui#262 + marker 2026-10-22 |
| pilot-console-ui#261 | REQUEST-CHANGES (U4: project/parentId/durationMs on board cards, not on the wire) | not on the PR — follow-up issue ui#263/#272 + marker 2026-10-22 |
| pilot-console-ui#255 | REQUEST-CHANGES (U5: a graph prop nothing passes) | not on the PR — follow-up issue ui#271 + marker 2026-10-22 |
| pilot-console-ui#254, #246 | APPROVE-with-defects | comment "## Post-merge review — APPROVE with defects" |
| pilot#5799, #5822 | APPROVE-with-defects | same |
| pilot#5868, #5874, #5870, #5871, #5872, #5875 | APPROVE-WITH-NOTES with named defects → follow-ups #5873/#5879/#5888–#5891 | comment |
| pilot-console#427 | APPROVE-with-notes | comment |

## Legs

### LEG K1 — repo: qf-studio/pilot — title: feat(cli): pilot review-merge runs the post-merge reviewer on any merged PR offline and prints the verdict without posting
probe: present qf-studio/pilot func \(c \*Controller\) runPostMergeReview
probe: present qf-studio/pilot type PostMergeReviewInput struct
probe: absent  qf-studio/pilot Use: +"review-merge

## Context

The post-merge reviewer (`internal/executor/post_merge_reviewer.go`, Review) is reachable only from autopilot's merged-PR path: runPostMergeReview in `internal/autopilot/post_merge_review.go` fetches the PR, the merged diff (local checkout, first parent of the merge commit), and the linked issue, builds PostMergeReviewInput, runs the reviewer and posts the comment. To measure the reviewer against merges that already carry a human verdict, and to tune its prompt, an operator needs to run the same gather-and-review on any past PR of any configured project and read the verdict without posting it. Six live verdicts so far were all APPROVE-WITH-NOTES with zero defects; the REQUEST-CHANGES path has never fired.

## Implementation

1. Extract the gather step from runPostMergeReview into one exported function in `internal/autopilot/post_merge_review.go` (for example GatherPostMergeReviewInput(ctx, ghClient, owner, repo, projectPath, prNumber, issueNumber)) that returns the PostMergeReviewInput. The controller path calls it; no behaviour change there.
2. Issue resolution: when the caller gives no issue number, take the first closing issue reference of the PR, else the GH-N in the head branch name, else fail with a message asking for the issue.
3. Diff source: use the local checkout when the project path is configured and the merge commit is present (fetch first); else fall back to the GitHub compare of the merge commit's first parent to the merge commit, through the existing GitHub client. Say in the output which source was used.
4. Add the subcommand in `cmd/pilot/commands.go`: pilot review-merge --repo owner/name --pr N [--issue M] [--json] [--post]. It loads the config, resolves the project by repo, builds the reviewer exactly as `cmd/pilot/post_merge_reviewer.go` does (same model, timeout and max_diff_chars), runs it, and prints: verdict, defect list (file, line, claim), notes, the Diff line (bytes, files, trimmed), model, duration. --json prints the PostMergeReview struct plus the input sizes. --post is off by default; with it, post the same comment the controller would, through the same comment builder, and never file a follow-up issue from the CLI.
5. Never touch pr_reviews, the daily cap or the metrics from the CLI; the run is diagnostic.
6. Tests, table-driven: the gather helper with a fake GitHub client (closing-issue resolution, branch-name fallback, missing-issue error); the command with a fake reviewer that reads its input (prints the verdict; --json shape; --post absent means no comment call). Fakes must read their arguments (mocks gate).
7. Docs: one section in the CLI reference under docs/content for the command and its flags, and a line in `configs/pilot.example.yaml` next to post_merge_review pointing at it.

## Acceptance

- pilot review-merge --repo qf-studio/pilot --pr 5902 prints VERDICT, the defect list, the notes and a Diff line, and posts nothing.
- With --json the output parses as JSON and carries verdict, defects, notes, diff_bytes, diff_files, diff_trimmed, model, duration_ms.
- A PR with no closing issue and a non-GH branch name fails with a message that names --issue.
- `go test -race ./internal/autopilot/ -run TestGatherPostMergeReviewInput` passes; paste the output into the PR body.
- `go test -race ./cmd/pilot/ -run TestReviewMergeCommand` passes; paste the output into the PR body.
- drop the branch-name fallback -> TestGatherPostMergeReviewInput_BranchNameFallback fails
- post the comment when --post is absent -> TestReviewMergeCommand_NoPostByDefault fails

## Out of scope

- Changing the reviewer prompt or verdict schema.
- A batch runner over many PRs (the calibration run below is a shell loop over this command).
- Filing follow-up issues from the CLI.

## Refs

- https://github.com/qf-studio/pilot/pull/5868
- https://github.com/qf-studio/pilot/pull/5907

## Rerun 3 — 2026-10-29 12:16Z, reviewer model switched to claude-opus-5-5 (founder call: "best pick for this type of task"; box config `post_merge_review.model`, backup `config.yaml.bak-pmr-opus-20261029`, daemon restarted 12:17Z, boot line model=claude-opus-5-5): same 14 PRs, outputs under box `~/calibration-v3/`; numbers appended to the bench report when scored.

## Rerun 2 — 2026-10-29 ~11:55Z on v2.298.0 (TASK-614 prompt/parser, TASK-613 M1 memory injection + M2 checkout + M3 confinement, TASK-610 budget): same 14 PRs, outputs under box `~/calibration-v2/`; scoring and numbers appended to the bench report when done.

## Calibration run (operator leg, after K1 ships; not a Pilot issue)

1. On the box (same claude CLI and model as live), run pilot review-merge --json for each PR in the labeled set; save outputs under .agent/system/bench/post-merge-reviewer-calibration-2026-10/.
2. Score: verdict match (REQUEST-CHANGES expected on 3; a defect-bearing verdict expected on 11); defect recall = hand-listed defects the daemon names at the same file, over all hand-listed defects; false notes = daemon notes that are wrong on reading.
3. Write `.agent/system/bench/post_merge_reviewer_calibration_2026-10.md` with the table and the three numbers.
4. Thresholds (founder to confirm): ≥2 of 3 REQUEST-CHANGES caught as REQUEST-CHANGES; defect recall ≥ 0.5; false notes ≤ 1 per verdict. Below any threshold → a prompt-tuning task with the misses as fixtures; above → hand reviews of non-tier-1 merges end, and the follow-up issue the reviewer files is the only human signal.

## Refs

- K1 → https://github.com/qf-studio/pilot/issues/5910
