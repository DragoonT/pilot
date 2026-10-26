# TASK-598: post-merge reviewer follow-ups — one daily cap for the whole daemon, and a follow-up issue that survives the epic and base-presence gates

**Status**: 🚀 Dispatched 2026-10-26 → pilot#5873 (`pilot`+`no-decompose`+`bug`), from the tier-1 review of PR#5868 (defects 1 and 2).
**Spec refs**: TASK-591 / #5861 (the reviewer), PR#5868 review comment (APPROVE-WITH-NOTES), SOP `sops/onboarding/new-project-issue-authoring.md` Rules 3b and 3c, GH-5527 (epic decomposition of a single-fix issue).
**Origin**: founder 2026-10-26: "File one pilot + no-decompose issue for the PR#5868 review defects 1 and 2".

## Legs — pilot (daemon)

### LEG R2 — repo: qf-studio/pilot — title: fix(autopilot): post-merge reviewer shares one daily cap across controllers, and its follow-up issue carries no-decompose with plain-text defect locations

## Context
Tier-1 review of PR#5868 (the GH-5861 post-merge reviewer) found two defects that matter on the founder box, which runs one autopilot controller per project.

First, the daily cap is per controller. In `internal/autopilot/post_merge_review.go`, postMergeBudget builds a postMergeReviewBudget lazily on each Controller from PostMergeReview.EffectiveDailyCap, and wirePostMergeReviewer in `cmd/pilot/post_merge_reviewer.go` installs the same reviewer on every controller in polling mode. With ten projects the real bound is ten times the configured daily_cap. The spec and the example config promise one cap per UTC day.

Second, the REQUEST-CHANGES follow-up issue built by CreatePostMergeReviewIssue in `internal/autopilot/feedback_loop.go` has four H2 sections plus a defect list, so it passes 200 words and the executor's epic detection decomposes it into sub-issues (the GH-5527 class, SOP Rule 3c). The same body renders each defect location in backticks; the checklist asks the model to name counterpart files, which on console-ui PRs live in another repository, and a backticked path that is not on the task repo's default branch holds the issue at the base-presence gate (SOP Rule 3b).

probe: present qf-studio/pilot func \(c \*Controller\) postMergeBudget\(\)
probe: present qf-studio/pilot func wirePostMergeReviewer\(
probe: present qf-studio/pilot func \(f \*FeedbackLoop\) CreatePostMergeReviewIssue\(
probe: absent  qf-studio/pilot SetPostMergeReviewBudget
probe: absent  qf-studio/pilot postMergeReviewNoDecomposeLabel

## Scope
- One budget per daemon: build a single postMergeReviewBudget in wirePostMergeReviewer and hand it to every controller through a new SetPostMergeReviewBudget; postMergeBudget keeps its lazy fallback for a controller that was never wired (tests, gateway mode with one controller). The budget stays in-memory and UTC-day keyed as today.
- Follow-up issue labels: CreatePostMergeReviewIssue adds a constant postMergeReviewNoDecomposeLabel with value no-decompose next to post-merge-review, deduplicated against the configured issue labels.
- Follow-up issue body: formatPostMergeDefects used by the issue body renders each location in plain text ("at internal/foo/bar.go:42"), never in backticks; the PR comment may keep backticks. Keep the existing sanitization and bounds.
- Document in the example config comment that the cap is daemon-wide.

## Acceptance
- [ ] Budget test: two controllers wired through wirePostMergeReviewer with daily_cap 2 run two reviews in total, not four; the third merged PR on either controller is skipped and the cap-reached line logs once. Build a budget per controller instead of the shared one -> TestPostMergeReview_SharedDailyCapAcrossControllers fails.
- [ ] Issue test: the filed follow-up issue carries labels pilot, post-merge-review and no-decompose exactly once each, and its body contains no backtick character in the defects section. Drop the no-decompose label -> TestCreatePostMergeReviewIssue_LabelsAndPlainLocations fails.
- [ ] Existing tests TestPostMergeReview_DailyCapAndTicketCap and TestPostMergeReview_Posting keep passing.
- [ ] `go test -race ./internal/autopilot/ -run PostMergeReview` passes; paste the output into the PR body.
- [ ] `go test -race ./cmd/pilot/ -run PostMergeReviewer` passes; paste the output into the PR body.

## Out of scope
- Persisting the budget across restarts.
- Retrying a review after a transient failure (defect 3 of the review).
- The post-merge CI result in the prompt, and tests for localMergedDiff (defects 4 and 5).

## Refs
- Review: https://github.com/qf-studio/pilot/pull/5868#issuecomment-6425323288
- R2 → - R2 → https://github.com/qf-studio/pilot/issues/5873
- Feature: TASK-591 → #5861 → PR#5868 (`018e450d0`)

**Last Updated**: 2026-10-26
