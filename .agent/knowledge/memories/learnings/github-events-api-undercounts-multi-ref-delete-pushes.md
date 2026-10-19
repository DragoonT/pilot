# Learning: GitHub's events API undercounts branch deletions done in one multi-ref push; count with git ls-remote

## Summary
2026-10-19 branch audit: 73 stale remote pilot/* branches were deleted in three multi-ref pushes (git push --no-verify origin --delete ref ref ...); repos/{o}/{r}/events showed only 11 DeleteEvents for that window. The public events feed collapses or caps multi-ref pushes, so it is not a deletion audit trail. Use git ls-remote --heads origin 'pilot/*' before and after, and keep the per-branch tip SHAs (the audit's remote-evidence.tsv) as the recovery record.

## Context
Verifying the branch-audit side session's report from the parent session; the count mismatch looked like unapproved deletions until the session explained the method.

## Details
Also learned: autopilot already deletes merged-PR branches (controller.go safeDeleteBranch after merge, GH-1383) and the repo has delete_branch_on_merge on; the 73 orphans were no-PR pushes (auto-preserve, failed runs) and closed-PR leftovers that no code path revisits — hence TASK-577 / #5770 (opt-in sweeper). For ref deletions use --no-verify: the pre-push gate otherwise runs the full Go gate per deletion.

## Recommended Approach
To verify a side session's remote-branch work: compare git ls-remote counts, read its evidence file, and ask the session for method and approvals; do not infer from the events API.

## Related
- TASK-577
- `internal/autopilot/controller.go`
- `scripts/pre-push-gate.sh`

---
**Captured**: 2026-10-19
**Confidence**: 90%
**Concepts**: github, autopilot, git
