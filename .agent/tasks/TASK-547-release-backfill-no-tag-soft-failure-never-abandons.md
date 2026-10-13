# fix(autopilot): a merged-but-untagged release-backfill row backs off but never counts toward abandonment

**Status**: 🚀 Dispatched to Pilot 2026-10-13 → [#5671](https://github.com/qf-studio/pilot/issues/5671) (labels `pilot` + `no-decompose`; follow-up from the post-merge review of PR #5669 / TASK-542)
**Created**: 2026-10-13
**Repo**: qf-studio/pilot

Blocked by: none

## Context

PR #5669 (issue #5665) made the no-tag outcome in `healReleaseBackfillRow` (`internal/autopilot/release_backfill.go`) a soft failure: when earliestReleaseTagContaining returns no tag for a merged commit, the row now goes through releaseBackfillFail with errReleaseBackfillNoTag so it backs off instead of being due again 30 seconds later. That was the intended cost fix. But releaseBackfillFail calls releaseBackfillObserveFailure, which advances the same consecutive-failure streak the abandon rule reads (releaseBackfillAbandonThreshold 10 attempts and releaseBackfillAbandonMinWindow 6 hours). With the doubling schedule 30s, 1m, 2m, 4m, 8m, 16m, 32m, 1h, 1h, ... the 13th attempt lands about 6h03m after the first no-tag observation and satisfies both conditions. The row is then persisted ReleaseBackfillAbandoned=true, skipped by every future sweep, and its prState.Error reads "release-backfill: abandoned after 13 consecutive API failures" although no API call failed.

The sweep exists (GH-4370) to heal rows whose PR merged outside the train and got tagged later. On the daily 14:00Z train most such rows wait longer than six hours, so after PR #5669 the sweep gives up on the very class it was built for. The issue text of #5665 said the existing abandon rule "still applies"; that sentence was the defect. Not yet in production: the box runs v2.283.0 and v2.284.0 is not tagged.

## Scope

- `internal/autopilot/release_backfill.go`: add releaseBackfillObserveSoftFailure(key string, now time.Time) that schedules the next retry with the same doubling schedule and the same releaseBackfillMaxBackoff cap but does not advance the abandon streak. The simplest shape: keep a separate softFails counter on releaseBackfillRowState that drives the back-off exponent, leave consecutiveFails and firstFailAt untouched, and never return abandon. A later hard failure (API error) or success keeps today's behaviour; releaseBackfillObserveSuccess still clears the whole state.
- In healReleaseBackfillRow, the no-tag branch calls releaseBackfillObserveSoftFailure instead of releaseBackfillFail. Keep errReleaseBackfillNoTag only if something still uses it; otherwise delete it.
- Update the comment block above releaseBackfillAbandonThreshold so it states that abandonment counts API failures only, never the no-tag outcome.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go vet ./internal/autopilot/` passes; paste the output into the PR body.
- `go test ./internal/autopilot/ -run TestReconcileReleaseBackfill -count=1` passes; paste the output into the PR body. Adds TestReconcileReleaseBackfill_NoTagRowNeverAbandoned: on the injected releaseBackfillClock, a merged row in no tag is driven through 14 due passes spanning more than 7 hours; after every pass the stored PRState has ReleaseBackfillAbandoned false and an empty Error; then a tag that contains the merge commit is added to the fixture, and the next due pass heals the row (one released event recorded).
- `go test ./internal/autopilot/ -run TestReconcileReleaseBackfill_NoTagRowBacksOff -count=1` still passes; paste the output into the PR body.
- route the no-tag branch back through releaseBackfillFail -> TestReconcileReleaseBackfill_NoTagRowNeverAbandoned fails
- make releaseBackfillObserveSoftFailure set nextRetryAt to now (no back-off) -> TestReconcileReleaseBackfill_NoTagRowBacksOff fails

## Out of scope

- The cross-pass tag-list TTL from PR #5669.
- Changing the abandon threshold or window for real API failures.

## Refs

- `internal/autopilot/release_backfill.go` (healReleaseBackfillRow, releaseBackfillFail, releaseBackfillObserveFailure, releaseBackfillObserveSuccess, releaseBackfillRowState), `internal/autopilot/release_backfill_test.go` (untaggedBackfillController, releaseBackfillServer, backfillTagFixture)
- PR #5669 post-merge review comment (defect section)
- TASK-542 (`.agent/tasks/TASK-542-release-backfill-tag-cache-ttl-and-no-tag-backoff.md`)
- Pilot issue: https://github.com/qf-studio/pilot/issues/5671
