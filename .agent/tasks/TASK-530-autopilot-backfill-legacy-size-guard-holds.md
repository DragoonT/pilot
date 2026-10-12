# fix(autopilot): backfill legacy size-guard holds into the generic hold fields

**Status**: 🚀 Dispatched to Pilot 2026-10-12 → [#5647](https://github.com/qf-studio/pilot/issues/5647) (labels `pilot` + `no-decompose`)
**Created**: 2026-10-12
**Repo**: qf-studio/pilot

## Context

PR #5645 replaced the size-guard hold pair (SizeGuardHoldActive, SizeGuardHoldHeadSHA) with the generic hold fields (HoldActive, HoldHeadSHA, HoldLabels, HoldRedriveCount) and redriveHeldPR reads only the generic fields. The old columns stay in `internal/autopilot/state_store.go` but nothing writes or reads them any more. A PR that was held by the size guard before that release has size_guard_hold_active 1 and hold_active 0 in SQLite, so after the next daemon restart it is rehydrated by PR #5646 but never redrives on a new head. PR #5646 was meant to carry the backfill, but the issue was picked up before the body amendment, so the migration is missing.

## Implementation

In `internal/autopilot/state_store.go`, add one migration after the hold_redrive_count migration:

UPDATE autopilot_pr_state SET hold_active = 1, hold_head_sha = size_guard_hold_head_sha WHERE size_guard_hold_active = 1 AND hold_active = 0

It must be idempotent: a second run changes zero rows. Rows with hold_active already 1 keep their own hold_head_sha.

Test in `internal/autopilot/gh5378_test.go`, next to TestStateStore_HoldFieldsSurviveRoundTrip, using newTestStateStore: TestStateStore_BackfillsLegacySizeGuardHold inserts through raw SQL one row with size_guard_hold_active 1, size_guard_hold_head_sha abc and hold_active 0, and one row with hold_active 1 and hold_head_sha keep and size_guard_hold_active 1 and size_guard_hold_head_sha other; opens the store again; asserts the first row loads with HoldActive true and HoldHeadSHA abc, and the second row still has HoldHeadSHA keep.

Keep the diff under 80 changed lines.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go test ./internal/autopilot/ -run TestStateStore -count=1` passes; paste the output into the PR body.
- `go vet ./internal/autopilot/` passes; paste the output into the PR body.
- drop the backfill migration -> TestStateStore_BackfillsLegacySizeGuardHold fails
- drop the hold_active = 0 condition from the WHERE clause -> TestStateStore_BackfillsLegacySizeGuardHold fails

## Refs

- Pilot issue: https://github.com/qf-studio/pilot/issues/5647
- Predecessors: https://github.com/qf-studio/pilot/pull/5645 (hold triple), https://github.com/qf-studio/pilot/pull/5646 (restart rehydration; backfill missed because of pickup timing)
- Code: `internal/autopilot/state_store.go`, `internal/autopilot/gh5378_test.go`

**Last Updated**: 2026-10-12
