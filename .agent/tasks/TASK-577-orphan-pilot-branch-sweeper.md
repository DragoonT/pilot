# feat(autopilot): sweep orphaned `pilot/*` remote branches that no tracked PR will ever delete

**Status**: 🚀 DISPATCHED 2026-10-19 → [#5770](https://github.com/qf-studio/pilot/issues/5770) (`pilot`, `no-decompose`). **Parked `pilot-needs-human` 10-19 21:53Z** — base-presence hold on the two NEW file paths this doc backticked (8th recurrence of the pitfall). **Un-parked 10-20 07:40Z**: paths rewritten in prose here and on the issue, label removed; re-pick on the next tick · **Owner**: Navigator plans, Pilot executes · **Related**: #5762 (executor side of GH-5756: auto-preserve push collides with the re-pick; separate PR, do not duplicate), TASK-508 (post-merge branch borrowing)

## Summary

A branch audit on 2026-10-19 found **73 stale pilot/GH-* branches on origin** of the qf-studio/pilot repository. Their breakdown is the design input:

| Class | Count | Why the existing post-merge delete never ran |
|---|---|---|
| No PR at all | 59 | `removePR`/`safeDeleteBranch` only fire for PRs autopilot tracks. Auto-preserve pushes (`preserveDirtyWorktreeAsWIP`, `internal/executor/git_freshness.go:96`), failed runs that pushed and then died before `CreatePullRequest`, and runs whose PR creation failed leave a branch nobody owns. |
| Closed (not merged) PR | 7 | GitHub's `delete_branch_on_merge` (on for this repo) only fires on merge. Autopilot's close paths skip the delete in some flows (`removePRTracking(pr, false)` at `controller.go:10707`, `:10742` for GH-4458 self-close). |
| Merged PR, branch re-pushed or merged while daemon was down | 7 | Boot catch-up is limited to `startup_merged_pr_scan_window` (72h, `types.go:720`). Anything older is never revisited. |

Cost of the pile-up is not cosmetic: a stale remote branch named pilot/GH-5756 made six executor retries fail `non-fast-forward` on 2026-10-19 (≈2 h box time, ≈$3.50 model spend; see #5762 and `.agent/knowledge/memories/pitfalls/auto-preserve-push-then-rewrite-non-ff-infra-repick-loop.md`). #5762 fixes the executor's push so it tolerates its own preserved SHA. This task closes the other half: **branches must not survive indefinitely on origin once no open PR references them.**

## Scope

One opt-in periodic sweeper in the autopilot controller. Nothing in the executor.

### Config (opt-in, default off)

`internal/autopilot/types.go` — model on `LifecycleNotifications` (`types.go:129-133`):

```go
// StaleBranchSweep opts in to the periodic sweep that deletes orphaned
// pilot/* remote branches (no open PR references them). GH-<this issue>.
StaleBranchSweep bool `yaml:"stale_branch_sweep"`
// StaleBranchMinAge is how old a branch with NO PR must be before the sweep
// deletes it (guards a run that pushed but has not yet opened its PR). Default 24h.
StaleBranchMinAge time.Duration `yaml:"stale_branch_min_age"`
```

Defaults near `types.go:720`: `StaleBranchSweep: false`, `StaleBranchMinAge: 24 * time.Hour`. Mirror both keys with a comment in `configs/pilot.example.yaml` `autopilot:` block (after `lifecycle_notifications`, around line 361).

### GitHub client

`internal/adapters/github/client.go` has `GetBranch` (`:750`) and `DeleteBranch` (`:1055`) but no list. Add:

```go
// ListBranches returns every branch whose name starts with prefix, via
// GET /repos/{o}/{r}/git/matching-refs/heads/{prefix} (paginated).
func (c *Client) ListBranches(ctx context.Context, owner, repo, prefix string) ([]BranchRef, error)
```

`BranchRef{Name string; SHA string}`. Follow the pagination idiom already used by `ListPullRequests` (`:763`). Test with the httptest pattern at `client_test.go:2351` (`DeleteBranch`).

To get a branch's age without N extra calls, use the commit date from `GetBranch` only for candidates that have no PR (the rare path); PR-backed candidates are decided from PR state alone.

### Sweeper (a new file branch_sweeper.go under internal/autopilot)

`func (c *Controller) sweepStaleBranches(ctx context.Context)`:

1. Return immediately if `!c.config.StaleBranchSweep`.
2. `ListBranches(ctx, owner, repo, "pilot/")`.
3. For each branch, skip when any of these holds:
   - it is the head of an **open** PR (`ListPullRequests(ctx, owner, repo, "open")` once per sweep, index by `Head.Ref`);
   - autopilot currently tracks a PR on it (in-memory `c.prs`/tracking map — whatever `removePRTracking` reads);
   - it is the base of an open PR (`safeDeleteBranch` already does this, keep the call);
   - it has no PR and its tip commit is younger than `StaleBranchMinAge`;
   - an execution for its task ID is still live (reuse the lookup the dispatcher uses for a pilot/GH-N branch name → task; `controller.go:5497` trims the prefix).
4. Otherwise call `safeDeleteBranch(ctx, name, prNumber)` (`controller.go:2220`). `prNumber` is the newest closed/merged PR on that head, or 0.
5. Every failure is a `Warn` and the loop continues; never abort the sweep on one branch. 404/422 from `DeleteBranch` count as already gone.
6. Log one summary line per sweep: `stale branch sweep: scanned=N deleted=M skipped_open=K skipped_young=J errors=E`. Add a counter metric `autopilot_stale_branches_deleted_total` next to the existing autopilot metrics.

Wire the ticker in the main loop beside `mergedScanTicker` (`controller.go:9886-9890`), interval = `max(MergedPRScanWindow, 1h)`. Also run one sweep at startup after the merged-PR catch-up scan finishes, so a daemon that was down for days cleans up on boot.

### Operator run on the box

Once merged and released, the box's pilot config file (the one pilot start reads) needs `autopilot.stale_branch_sweep: true` (operator step, not Pilot's).

## Won't do

- No executor changes (that is #5762).
- No deletion of branches with an **open** PR, ever, regardless of age.
- No deletion of branches outside the pilot/ prefix.
- No force-push, no ref rewriting.
- No change to GitHub's `delete_branch_on_merge` setting.

## Tests (table-driven, in a new branch_sweeper_test.go next to the sweeper)

| Case | Expect |
|---|---|
| flag off | zero API calls |
| merged PR, old | deleted |
| closed PR, old | deleted |
| open PR | skipped, logged |
| no PR, tip 1h old, min age 24h | skipped (young) |
| no PR, tip 3d old | deleted |
| branch is base of open stacked PR | skipped via `safeDeleteBranch` guard |
| live execution for the task ID | skipped |
| `DeleteBranch` 404 | counted as gone, no error |
| `DeleteBranch` 500 on one branch | warned, sweep continues, other branch still deleted |
| pagination: 150 branches over 2 pages | all scanned |

Plus a `ListBranches` httptest in `client_test.go` (two pages, prefix filter).

## Acceptance

- `make test` and `make lint` green.
- With the flag on against a fake GitHub, a fixture mirroring the 2026-10-19 audit (59 no-PR old, 7 closed-PR, 7 merged-PR, 2 open-PR, 1 no-PR young) ends with exactly 73 deletions and 3 skips.
- The PR body states the config key, default, and the operator step.

## Execution limits

Single PR, `no-decompose`. Do not touch `internal/executor/`. Keep the sweeper under ~250 lines excluding tests.

## Refs

- Issue: https://github.com/qf-studio/pilot/issues/5770
- Audit evidence: 73 branches, deleted by hand 2026-10-19 after per-branch verification (session notes outside the repo).
- `internal/autopilot/controller.go:2220` `safeDeleteBranch` · `:5990-6001` post-merge delete (GH-1383) · `:8754-8790` `removePRTracking` · `:9886` `mergedScanTicker`
- `internal/adapters/github/client.go:750` `GetBranch` · `:763` `ListPullRequests` · `:1055` `DeleteBranch`
- `internal/autopilot/types.go:129-133` `LifecycleNotifications` (opt-in idiom) · `:720` defaults
- `configs/pilot.example.yaml:340-361` `autopilot:` block
- Pitfalls: `auto-preserve-push-then-rewrite-non-ff-infra-repick-loop`, `executor-swallowed-rejected-push-as-success-branch-exists-is-not-pushed`
