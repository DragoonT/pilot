# fix(autopilot): keep the release-backfill tag list across passes with a TTL and back off rows whose merge is in no tag

**Status**: ✅ MERGED + REVIEWED 2026-10-13 → [#5665](https://github.com/qf-studio/pilot/issues/5665) → PR#5669 merged 19:24Z, post-merge review APPROVE-w-defect (2/2 pins killed by the reviewer). Defect: the no-tag soft failure feeds the abandon rule → row flagged `ReleaseBackfillAbandoned` after ~6h with an "API failures" error; follow-up [TASK-547](TASK-547-release-backfill-no-tag-soft-failure-never-abandons.md) → #5671, to land before v2.284.0.
**Created**: 2026-10-13
**Repo**: qf-studio/pilot

Blocked by: none

## Context

After PR #5660 (issue #5658) the backfill tag walk is bounded, but the tag list cache in `internal/autopilot/release_backfill.go` (releaseBackfillTagCache, created per pass through the context) lives only for one pass, and a merged PR whose merge commit is in no tag calls releaseBackfillObserveSuccess, which deletes its back-off state, so the row is due again on the next pass 30 seconds later. On the pilot repo that is one full ListTags pagination (10 API calls over 903 tags) plus one compare every 30 seconds for as long as such a row exists, about 20 GitHub calls per minute against the shared user pool. Found in the post-merge review of PR #5660.

## Scope

- `internal/autopilot/release_backfill.go`: keep the tag list per owner/repo on the Controller (new field, mutex-guarded) with a TTL (new constant releaseBackfillTagTTL, value 10 minutes). A pass reuses the cached list when it is younger than the TTL and refetches otherwise. The per-pass context cache can stay as the hand-off, or be replaced; either way one ListTags per repo per TTL window.
- Treat the no-tag outcome as a soft failure: when earliestReleaseTagContaining returns no tag for a merged commit, call releaseBackfillObserveFailure instead of releaseBackfillObserveSuccess, so the row backs off with the existing doubling schedule (capped at one hour) and the existing abandon rule after ten consecutive failures inside the six-hour window still applies. A genuine heal (a tag found) still clears the state.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go vet ./internal/autopilot/` passes; paste the output into the PR body.
- `go test ./internal/autopilot/ -run TestReconcileReleaseBackfill -count=1` passes; paste the output into the PR body. Adds TestReconcileReleaseBackfill_TagListReusedAcrossPassesWithinTTL (two passes inside the TTL fetch the tag list once; a third pass after the TTL fetches again, using the injected releaseBackfillClock) and TestReconcileReleaseBackfill_NoTagRowBacksOff (a merged row in no tag is not due again on the very next pass and is due after its back-off).
- `go test ./internal/autopilot/ -run TestEarliestReleaseTagContaining -count=1` passes; paste the output into the PR body.
- drop the TTL check so every pass refetches -> TestReconcileReleaseBackfill_TagListReusedAcrossPassesWithinTTL fails
- call releaseBackfillObserveSuccess again for the no-tag outcome -> TestReconcileReleaseBackfill_NoTagRowBacksOff fails

## Out of scope

- The compare algorithm from PR #5660.
- ETag conditional requests on ListTags (a later optimisation).

## Refs

- `internal/autopilot/release_backfill.go` (releaseBackfillTagCache, releaseBackfillObserveSuccess, releaseBackfillObserveFailure, healReleaseBackfillRow), `internal/autopilot/release_backfill_test.go` (releaseBackfillServer, releaseBackfillClock)
- PR #5660 review note on the remaining cost
- Pilot issue: https://github.com/qf-studio/pilot/issues/5665
