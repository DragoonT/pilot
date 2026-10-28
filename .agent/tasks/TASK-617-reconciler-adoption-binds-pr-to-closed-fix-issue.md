# TASK-617: reconciler adoption binds a reopened PR to a closed fix issue, so the post-merge review judges the diff against the wrong issue

**Status**: 🚀 DISPATCHED 2026-10-28 → pilot#5927 (`pilot`+`no-decompose`). First live REQUEST-CHANGES (PR#5921, 17:38Z) was wrong on its main point for this reason; follow-up #5925 closed by hand.
**Spec refs**: `internal/autopilot/controller.go` reconciler adoption (~9330–9372: parses the issue from the pilot/GH-N branch, then registers), `internal/autopilot/types.go` PRState.RegisteredViaFixIssue / SelfClosedFixIssue (~1525), FixIssueForBranch (borrowed-branch registry, GH-5430), `internal/autopilot/post_merge_review.go` (review input uses PRState.IssueNumber), `cmd/pilot/review_merge.go` (JSON output).
**Origin**: 2026-10-28 queue check. PR#5921 (#5917) failed CI on a flaky test; autopilot closed it and filed fix issue #5922 for branch pilot/GH-5917; #5922 was declined at pre-flight and closed by hand; the PR was reopened and CI rerun; the reconciler re-adopted it ("adopting untracked open PR … issue=5917") but registered it with issue=5922; after the merge the reviewer compared #5917's diff with #5922's body ("fix the CI failure"), returned REQUEST-CHANGES, and filed #5925.

## Why
- The borrowed-branch registry entry (branch → fix issue) written when #5922 was created survives the fix issue's closure. Adoption consumes it and overrides the issue parsed from the branch name.
- Every downstream consumer of PRState.IssueNumber then points at the wrong issue: the post-merge review input, the follow-up issue title fix(#PR), the merge completion comment, the done-label flow.
- The PR itself carries the truth: "Closes #5917" in its body, and the branch name.

## Legs — pilot (daemon)

### LEG B1 — repo: qf-studio/pilot — title: fix(autopilot): adoption never binds a PR to a closed or unlabeled fix issue; the review input and the follow-up title use the issue the PR closes
probe: present qf-studio/pilot reconciler: adopting untracked open PR
probe: present qf-studio/pilot RegisteredViaFixIssue bool
probe: absent  qf-studio/pilot func resolveAdoptedIssueNumber\(

## Context

When the reconciler in `internal/autopilot/controller.go` adopts an untracked open pilot/GH-N PR it parses N from the branch, then consults the borrowed-branch registry (FixIssueForBranch, GH-5430) and, when an entry exists, registers the PR under the fix issue instead (PRState.RegisteredViaFixIssue). The entry is written when autopilot files a CI-fix issue for that branch and is not removed when that fix issue is closed without a run, declined at pre-flight, or unlabeled. On 2026-10-28 PR#5921 (branch pilot/GH-5917) was closed by autopilot on a flaky test, fix issue #5922 was filed then declined and closed by hand, the PR was reopened, and adoption registered it with issue=5922. The post-merge reviewer in `internal/autopilot/post_merge_review.go` builds its input from PRState.IssueNumber, so it compared the #5917 diff with the #5922 body, returned REQUEST-CHANGES ("the failing test is not addressed") and filed follow-up #5925 titled fix(#5921). The same wrong number reaches the merge completion comment and the done-label flow.

## Implementation

1. Add one resolver used by adoption: resolveAdoptedIssueNumber(ctx, pr) returns, in order, the first closing-issue reference of the PR body (Closes/Fixes/Resolves #N) when that issue is open or was closed by this PR's merge; else the registry's fix issue only when that issue is open and still carries the autopilot-fix label; else the number parsed from the branch. Log which source won.
2. Registry hygiene: when a fix issue is closed, unlabeled, declined at pre-flight or cancelled, remove its borrowed-branch entry (hook the existing issue-close and label-change paths in `internal/autopilot/feedback_loop.go` and the dispatcher's declined-preflight outcome); also drop an entry whose fix issue is closed at adoption time.
3. Post-merge review input: take the issue from the PR's closing references first, then PRState.IssueNumber; the follow-up issue title and body name both the PR and the issue reviewed.
4. cmd/pilot/review_merge.go: add table-driven tests for the JSON output fields severity and not_verified (the valid second defect from the PR#5921 verdict).
5. Tests, table-driven with a fake GitHub client: registry entry for a closed fix issue is ignored and removed; an open labeled fix issue still wins; a PR with Closes #N binds to N; a PR with no closing reference and no registry entry binds to the branch number.

## Acceptance

- Adoption of a reopened pilot/GH-5917 PR whose body says Closes #5917, with a registry entry for a closed fix issue #5922, registers issue=5917 and logs source=closing-reference.
- The registry entry for the closed fix issue is gone after that adoption.
- The post-merge review of that PR fetches issue #5917.
- `go test -race ./internal/autopilot/ -run TestResolveAdoptedIssueNumber` passes; paste the output into the PR body.
- `go test -race ./cmd/pilot/ -run TestReviewMergeJSONSeverityFields` passes; paste the output into the PR body.
- let a closed fix issue's registry entry win -> TestResolveAdoptedIssueNumber_ClosedFixIssueIgnored fails
- skip the closing-reference lookup -> TestResolveAdoptedIssueNumber_ClosingReferenceWins fails

## Out of scope

- The CI-failure classifier's handling of flaky tests (separate task).
- The reviewer prompt (TASK-614, merged as PR#5921).

## Refs

- https://github.com/qf-studio/pilot/pull/5921
- https://github.com/qf-studio/pilot/issues/5922
- https://github.com/qf-studio/pilot/issues/5925

## Refs

- B1 → https://github.com/qf-studio/pilot/issues/5927
