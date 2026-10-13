# fix(autopilot): find the earliest release tag with a newest-first probe and a binary search, bounded per row

**Status**: 📋 Planned 2026-10-13
**Created**: 2026-10-13
**Repo**: qf-studio/pilot

Blocked by: none (independent of the epicParent pass issue; both must ship)

## Context

earliestReleaseTagContaining in `internal/autopilot/release_backfill.go` lists tags with page size maxReleaseBackfillTags (100), but the SDK ListTags paginates exhaustively, so on the pilot repo it sorts all 903 tags ascending and calls CompareStatus once per tag from the oldest until one contains the sha. A sha that is in no tag (the merged-but-unreleased case the backfill exists for) costs 903 compares, each a GitHub call with retries, inside the controller tick. On 2026-10-13 this held the qf-studio/pilot controller for 57 minutes and the 16:00 train never tagged. The comment at the top of the file that claims a 100-tag window is wrong.

## Scope

- `internal/autopilot/release_backfill.go`, earliestReleaseTagContaining: sort the versioned tags descending. Probe the newest tag first: if CompareStatus says the sha is not contained (not ahead and not identical), return no tag after one compare, because on a linear default branch no older tag can contain it. If the newest probe reports diverged, fall back to a capped linear scan of the 5 newest tags. Otherwise binary-search the ascending list for the earliest tag that contains the sha. Add a per-row compare budget (new constant maxReleaseBackfillCompares, value 12); when exceeded return an error that goes through the existing failure path so the row backs off.
- Cache the tag list for the duration of one reconcileReleaseBackfill pass (all rows in a pass share it) instead of refetching per row.
- Fix the stale comment about the 100-tag window at the top of the file.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go vet ./internal/autopilot/` passes; paste the output into the PR body.
- `go test ./internal/autopilot/ -run TestEarliestReleaseTagContaining -count=1` passes; paste the output into the PR body. Adds a compare call counter to releaseBackfillServer and the cases: ShaInNoTagCostsOneCompare (900 semver tags, sha in none, exactly 1 compare), ShaInMiddleTagResolvesWithinBudget (sha first contained in tag 450, at most 12 compares, correct tag returned), ShaInNewestTagOnly, DivergedNewestFallsBackToCappedScan, BudgetExceededReturnsError.
- `go test ./internal/autopilot/ -run TestReconcileReleaseBackfill -count=1` passes; paste the output into the PR body. Adds TestReconcileReleaseBackfill_TagListFetchedOncePerPass.
- remove the newest-first probe -> TestEarliestReleaseTagContaining/ShaInNoTagCostsOneCompare fails
- replace the binary search with the old linear scan -> TestEarliestReleaseTagContaining/ShaInMiddleTagResolvesWithinBudget fails
- remove the per-row compare budget -> TestEarliestReleaseTagContaining/BudgetExceededReturnsError fails
- fetch the tag list per row again -> TestReconcileReleaseBackfill_TagListFetchedOncePerPass fails

## Out of scope

- The Run-loop deadline and row cap (separate issue).
- tagCoveringCommit in `internal/autopilot/controller.go` and the sibling ListTags call in `internal/autopilot/releaser.go`.
- Changes to the studio-sdk ListTags pagination.

## Refs

- `internal/autopilot/release_backfill.go` (earliestReleaseTagContaining, reconcileReleaseBackfill, healReleaseBackfillRow)
- `internal/autopilot/release_backfill_test.go` (releaseBackfillServer compare keyed base...head)
- Precedents: GH-4370 introduced the backfill (healing semantics must stay), GH-4919 backoff and abandon
