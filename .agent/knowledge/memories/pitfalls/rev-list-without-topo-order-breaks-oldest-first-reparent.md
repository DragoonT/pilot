# Pitfall: git rev-list without --topo-order breaks an oldest-first rewrite walk across a merge; and 'HEAD --not --remotes=origin' is unbounded with no origin refs

## Summary
PR#5723 rewrote co-author trailers over 'rev-list HEAD ^base' walked oldest-first, assuming every parent follows its children in the list; with two lines of history and tied timestamps the order inverts, a child is processed before its parent, and the branch ends with duplicated commits and the trailer still reachable (review repro: 6 commits instead of 5). --topo-order fixes it (PR#5737). The replacement range 'HEAD --not --remotes=origin' returns the whole history with exit 0 when no origin refs exist, so a no-remote clone rewrites back to the root silently (PR#5740 adds the WARN + HEAD-only return).

## Context
Post-merge reviews of PR#5723 and PR#5733 (2026-10-16), scratch experiments in a detached worktree.

## Details
PR#5723 rewrote co-author trailers over 'rev-list HEAD ^base' walked oldest-first, assuming every parent follows its children in the list; with two lines of history and tied timestamps the order inverts, a child is processed before its parent, and the branch ends with duplicated commits and the trailer still reachable (review repro: 6 commits instead of 5). --topo-order fixes it (PR#5737). The replacement range 'HEAD --not --remotes=origin' returns the whole history with exit 0 when no origin refs exist, so a no-remote clone rewrites back to the root silently (PR#5740 adds the WARN + HEAD-only return).

## Recommended Approach
Any history-rewrite walk: list with --topo-order (children before parents), re-parent from a rewritten map, and guard the bound (check refs/remotes/origin/ exists before --not --remotes=origin). Pin with a same-second two-line merge subtest and a no-remote subtest.

## Related
- TASK-571
- TASK-569
- TASK-561
- `internal/executor/git.go`
- `internal/executor/git_test.go`

---
**Captured**: 2026-10-17
**Confidence**: 90%
**Concepts**: git, co-author, history-rewrite, executor
