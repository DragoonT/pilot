# fix(autopilot): rehydrate human-held PRs on daemon restart so their redrive survives a train

**Status**: 🚀 Dispatched to Pilot 2026-10-12 → [#5644](https://github.com/qf-studio/pilot/issues/5644), blocked by #5643 (labels `pilot` + `no-decompose`)
**Created**: 2026-10-12
**Repo**: qf-studio/pilot

Blocked by: #5643

## Context

RestoreState in `internal/autopilot/controller.go` skips every persisted PR row whose stage is StageFailed, with one exception for BreakerHoldActive. A PR held for human review by escalateAndHold therefore exists in SQLite but is not tracked after a restart, so the tick never fetches its live head and the redrive added by the previous issue (HoldActive, HoldHeadSHA) cannot fire. The same loss applies to RebaseHoldActive rows, whose re-adoption path reAdoptHeldRebasePR also runs only on tracked PRs. The daemon restarts on every daily train, so a held PR that gets its fix pushed after a train is stranded exactly like pilot-console PR #388 was on 2026-10-12, with no log line.

## Implementation

In RestoreState, extend the StageFailed exception: keep a row tracked when BreakerHoldActive, HoldActive or RebaseHoldActive is true. Log one Info line per rehydrated held row with the PR number, the stage and which hold flag kept it. Do not change any redrive function.

Tests in `internal/autopilot/escalate_and_hold_test.go` or the file that holds the existing RestoreState tests, with the newTestStateStore and NewController helpers used there:

- TestRestoreState_RehydratesHeldFailedPR: a persisted StageFailed row with HoldActive true is present in the controller's tracked PRs after RestoreState.
- TestRestoreState_RehydratesRebaseHeldFailedPR: same for RebaseHoldActive.
- TestRestoreState_StillSkipsPlainFailedPR: a StageFailed row with no hold flag stays untracked, as today.
- TestController_ProcessAllPRs_RedrivesHeldPRAfterRestart: persist a held row, build a fresh controller, RestoreState, run one tick against a fake GitHub whose PR head differs from HoldHeadSHA, and assert the PR is in StageWaitingCI.

Keep the diff under 150 changed lines.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go test ./internal/autopilot/ -run TestRestoreState -count=1` passes; paste the output into the PR body.
- `go test ./internal/autopilot/ -run TestController_ProcessAllPRs -count=1` passes; paste the output into the PR body.
- `go test ./internal/autopilot/ -count=1` passes; paste the output into the PR body.
- `go vet ./internal/autopilot/` passes; paste the output into the PR body.
- skip HoldActive rows in RestoreState as before -> TestRestoreState_RehydratesHeldFailedPR fails
- skip RebaseHoldActive rows in RestoreState -> TestRestoreState_RehydratesRebaseHeldFailedPR fails
- keep every StageFailed row tracked -> TestRestoreState_StillSkipsPlainFailedPR fails

## Refs

- Pilot issue: https://github.com/qf-studio/pilot/issues/5644
- Depends on the hold triple from the previous issue (HoldActive, HoldHeadSHA, HoldLabels)
- Code: `internal/autopilot/controller.go` (RestoreState, reAdoptHeldRebasePR), `internal/autopilot/types.go`
- Research 2026-10-12 (navigator-research agent): RestoreState exception covers BreakerHoldActive only

**Last Updated**: 2026-10-12
