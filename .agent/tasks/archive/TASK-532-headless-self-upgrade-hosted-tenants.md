# feat(upgrade): headless self-upgrade so hosted tenants track the release train

**Status**: ✅ REVIEWED 2026-10-13 — [#5651](https://github.com/qf-studio/pilot/issues/5651) → PR#5654 (head d80d8ad97, +319/-166, autopilot merging at review time), review **APPROVE-w-notes** (3/3 pins kill; full cmd/pilot, config, upgrade suites ok). Notes-only: ErrBinaryNotWritable would alert every 5 min on a tenant whose binary dir is still root-owned (the alert gate only dedupes drain timeouts) — TASK-537 must chown BEFORE the console renders auto_hot_upgrade: true.
**Created**: 2026-10-13
**Repo**: qf-studio/pilot

Blocked by: none

## Context

The founder tenant ran Pilot 2.276.1 while the release train was at v2.281.0; a manual SSM binary swap was needed. The whole self-upgrade pipeline (version checker, hot upgrader, PerformHotUpgrade) starts only inside the dashboard branch of `cmd/pilot/main.go` (the block gated on dashboardMode and a non-nil TUI program), its only TUI dependency being program.Send in callbacks. The drain adapter runningOnlyTaskChecker in `cmd/pilot/upgrade.go` dereferences the dashboard monitor, which is nil outside dashboard mode. AssertHostedInvariants in `internal/config/config.go` also refuses upgrade.auto_hot_upgrade=true under PILOT_HOSTED=1 (the S0.7 assumption that the control plane redeploys), but no control-plane rollout exists today. Founder decision 2026-10-13: daemon self-upgrade is the tenant path; relax that one invariant and keep the tunnel invariant.

## Scope

- `internal/config/config.go`, AssertHostedInvariants: delete the AutoHotUpgrade branch, update the doc comment, keep the tunnel check.
- `cmd/pilot/main.go`: create upgradeRequestCh unconditionally next to its declaration (today it is created only inside the dashboard branch). Move the version-checker and hot-upgrade goroutine block above the dashboard gate. Replace each program.Send with a new helper upgradeNotify(program, msg, line) that sends only when program is non-nil and always logs the line through slog. Keep OnStale, reportUpgradeFailure, the drain-timeout alert gate (GH-4609), PauseAdmissionFor and ResumeAdmissionFor, and the 30 minute task timeout unchanged.
- `cmd/pilot/upgrade.go`: add liveWorkerTaskChecker, a TaskChecker over the executor LiveWorkerChecker interface. GetRunningTaskIDs delegates to the dispatcher's GetRunningTaskIDs. WaitForTasks polls every 2 seconds until the set is empty and on deadline returns an error that wraps executor.ErrDrainTimeout so the alert gate keeps classifying it. main.go selects runningOnlyTaskChecker when the monitor is non-nil, else liveWorkerTaskChecker over the dispatcher.
- Preflight stays unchanged: checkBinaryWritable in `internal/upgrade/upgrade.go` still fails loud with ErrBinaryNotWritable while a tenant's binary directory is root-owned. The bootstrap ownership change and the config template flip are a separate pilot-console ticket.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go vet ./cmd/pilot/ ./internal/config/` passes; paste the output into the PR body.
- `go test ./internal/config/ -run TestAssertHostedInvariants -count=1` passes; paste the output into the PR body. The subtest for auto_hot_upgrade true under hosted mode now expects no error; the tunnel subtest is unchanged.
- `go test ./cmd/pilot/ -run TestLiveWorkerTaskChecker -count=1` passes; paste the output into the PR body. Adds WaitForTasks_ReturnsWhenIdle and WaitForTasks_TimeoutIsErrDrainTimeout with a fake LiveWorkerChecker.
- `go test ./cmd/pilot/ -run TestUpgradeNotify_NilProgramLogsOnly -count=1` passes; paste the output into the PR body.
- `go test ./cmd/pilot/ -run TestDrainTimeoutAlertGate -count=1` passes; paste the output into the PR body.
- restore the auto_hot_upgrade branch in AssertHostedInvariants -> TestAssertHostedInvariants/Hosted_AutoHotUpgradeTrue_Allowed fails
- drop the ErrDrainTimeout wrap from liveWorkerTaskChecker.WaitForTasks -> TestLiveWorkerTaskChecker_WaitForTasks_TimeoutIsErrDrainTimeout fails
- call program.Send unconditionally in upgradeNotify -> TestUpgradeNotify_NilProgramLogsOnly fails

## Out of scope

- Checksum verification of the downloaded asset (separate issue).
- Console-driven rollout (pilot-console#390), bootstrap ownership and the tenant config template.
- The Windows restart path, the 5 minute check interval and the 30 minute drain timeout.

## Refs

- `cmd/pilot/main.go` (dashboard-gated upgrade block, upgradeRequestCh), `cmd/pilot/upgrade.go` (runningOnlyTaskChecker, drainTimeoutAlertGate), `cmd/pilot/upgrade_failure_test.go`
- `internal/config/config.go` (AssertHostedInvariants), `internal/config/hosted_test.go`
- `internal/upgrade/hot.go` (PerformHotUpgrade, TaskChecker), `internal/upgrade/checker.go` (VersionChecker)
- `internal/executor/dispatcher.go` (GetRunningTaskIDs), `internal/executor/monitor.go` (WaitForRunningTasks, ErrDrainTimeout)
- Memories: pitfall self-upgrade requires manual keypress (GH-3790), decision self-upgrade auto trigger and staleness check
- SOP: `.agent/sops/operations/tenant-binary-upgrade-ssm.md` (the manual path this replaces)
- Pilot issue: https://github.com/qf-studio/pilot/issues/5651
