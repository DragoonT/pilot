# Pitfall: PR numbers collide across repos: a github-review approval check keyed on PR number alone approves the wrong PR

## Summary
With projects: on several repos, the GitHub approval handler checked every PR number against adapters.github.repo. A PR #N in another repo resolved as approved when the default repo's PR #N (even an old merged one) had an approval - a human-gate bypass. Fixed: per-request owner/repo resolved from Request.Project, fail closed when unresolvable (#5716 -> PR#5746); HasApprovalReview now requires an open PR and an approval on the current head SHA (#5749 -> PR#5752).

## Context
External report scrappydog #5716 (404 loop); the false-approval half found by nav-research verification 2026-10-19.

## Details
Same class for any PR-number-keyed map: HandleReviewEvent/HandleChangesRequestedEvent now match (owner, repo, number). Remaining: ListPullRequestReviews reads only the first 30 reviews (no pagination).

## Recommended Approach
Any lookup keyed on a PR or issue number must also key on owner/repo. Never fall back to the default repo for a request that names another project.

## Related
- TASK-576
- `internal/approval/github.go`
- `internal/adapters/github/client.go`

---
**Captured**: 2026-10-19
**Confidence**: 95%
**Concepts**: approval, github
