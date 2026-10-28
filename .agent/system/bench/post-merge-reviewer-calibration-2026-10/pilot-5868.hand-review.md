**VERDICT: APPROVE-WITH-NOTES** — tier-1 post-merge review (hand-opened head `3d8f958`, merged as `018e450d0`; the feature posts to GitHub and files issues from the daemon).

### Verified
- Spec (#5861) bullet by bullet: knob default off, own daily counter, attempt-once guard persisted (`post_merge_review_posted` in `autopilot_pr_state` incl. the repo-scoping rebuild), one comment per PR, one follow-up issue on REQUEST-CHANGES with exact-title dedup, ledger upsert as reviewer `post-merge-reviewer`, per-verdict counter exported as `pilot_post_merge_reviews_total`, placement in `handleMerged` ahead of the `SkipPostMergeCI` branch. Unknown verdict posts nothing. Prompt goes through stdin (the intent-judge runner, GH-4583), so a 32k diff is safe on Linux argv limits. Model output is sanitized and bounded before it lands in a `pilot`-labeled issue.
- `go test -race` on `./internal/autopilot/ -run PostMergeReview`, `./internal/executor/ -run PostMergeReview`, `./internal/config/`, `./cmd/pilot/`, `./internal/gateway/`: all `ok` locally on main.
- Mutation pins (applied, run, reverted): removing the `PostMergeReviewPosted` guard → `TestHandleMerged_PostMergeReviewRunsOnce` fails (`reviewer calls after second pass = 2, want still 1`); changing the cap check `>=` to `>` → `TestPostMergeReview_ConfiguredCap` fails (`reviews run = 3, want 2`).
- Two independent reads (own + unanchored) reached the same verdict.

### Defects (non-blocking)
1. `internal/autopilot/post_merge_review.go` `postMergeBudget()` — the daily cap is **per controller**, built lazily on each. `wirePostMergeReviewer` installs the reviewer on every per-project controller in polling mode, so the real daily bound on the box is `projects × daily_cap` (≈10 × 20), not the configured 20. The spec says one cap. Fix: share one budget across controllers (build it in `wirePostMergeReviewer` and pass it in).
2. `internal/autopilot/feedback_loop.go` `CreatePostMergeReviewIssue` — the follow-up issue carries four `##` sections and a defect list, so it will exceed 200 words and `detectEpic` will decompose it into sub-issues (SOP Rule 3c, GH-5527 class). Add `no-decompose` to its labels. Related: the checklist tells the model to name counterpart files, which on console-ui PRs live in another repo; a backticked cross-repo path in a defect `Location` trips the base-presence hold (Rule 3b). Render locations in plain text, not backticks.
3. Attempt-once is set and persisted before any side effect, so a transient failure (gather timeout, `git fetch`, `AddComment`) drops the review for good and still consumes budget; the ledger row is skipped too when the comment failed (`commentID <= 0`). Acceptable for "never post twice", but it is silent beyond a WARN and the `error` counter.
4. `CIResult` is the pre-merge `prState.CIStatus`; the spec's "post-merge CI result when known" is never available at `handleMerged` time. The prompt labels it honestly.
5. `localMergedDiff` (rev-parse / fetch / diff in the project checkout) has no test; every controller test uses the `postMergeDiff` override.

### Notes
- In-flight review goroutines are not awaited on daemon shutdown (`postMergeReviewWG` is only waited in tests); a hot self-upgrade mid-review loses that PR's review (flag already persisted).
- The verdict regex needs `VERDICT:` as the first non-empty line; a markdown-wrapped answer (`**VERDICT: …**`) is `unknown` and a silent no-op — watch the `unknown` counter after enabling.
- `GetReviewVerdictCountsByModel` has no `reviewer` filter, so bench defect-rate columns now mix model and human verdicts; filter on `reviewer='post-merge-reviewer'` where that matters.
- Follow-up title is `fix(#<PR>): …` (conventional-commit type first), a documented deviation from "prefixed with the PR number".

