# fix(autopilot): redrive any human-held PR when its branch gets a new head, not only size-guard holds

**Status**: ✅ REVIEWED 2026-10-12 — [#5643](https://github.com/qf-studio/pilot/issues/5643) → PR#5645 (head e41601373, +651/-246), review **APPROVE-w-notes** posted while autopilot was merging (6/6 pins kill, full package green). Note: legacy size-guard holds need a backfill → folded into TASK-529. (labels `pilot` + `no-decompose`)
**Created**: 2026-10-12
**Repo**: qf-studio/pilot

## Context

On 2026-10-12 pilot-console PR #388 failed a custom CI gate whose log the classifier could not parse. The autopilot logged "CI failure classification: zero evidence gathered", then "escalateAndHold: PR held for human review, branch intact" with the reason "CI failure with zero gathered evidence", and moved the PR to StageFailed. A continuation fix issue pushed a new head at 08:31Z, CI went green at 08:40Z, and OnPRCreatedForFixIssue logged the registration at 08:33Z. Nothing else happened until a human merged the PR at 09:47Z. One day earlier pilot PR #5637 was held by the size guard, a continuation pushed a new head, redriveSizeGuardHeldPR logged "branch updated on size-guard-held PR, re-entering pipeline", and the PR merged on its own.

The cause is in `internal/autopilot/controller.go`. escalateAndHold has eleven call sites. Only the size-guard site sets SizeGuardHoldActive and SizeGuardHoldHeadSHA, and redriveSizeGuardHeldPR gates on exactly those two fields. ProcessPR treats StageFailed as terminal. registerPR returns early for a PR that is already tracked, so the fix-issue registration never touches Stage or HeadSHA. HeadSHA is only refreshed in handleWaitingCI, so it is stale for the whole hold. The tick in processOnePR still fetches the live PR for every tracked row and already calls checkExternalMergeOrClose, reAdoptHeldRebasePR, redriveFailedPRForBaseRetarget and redriveSizeGuardHeldPR in that order, so the hook point exists.

Research 2026-10-12 (navigator-research agent) mapped the eleven sites. CI-side holds that a new head can legitimately fix: "CI failure with zero gathered evidence", "CI fix size guard fired", "CI-fix continuation declined at preflight", "review-fix continuation declined at preflight". Holds that must stay parked: the two iteration-cap holds (existing tests pin that), the two post-merge holds (the PR is merged, a head change is impossible), and the two rebase holds (reAdoptHeldRebasePR owns them, out of scope here).

## Implementation

Generalize the size-guard pair into a hold triple on PRState in `internal/autopilot/types.go`: HoldActive bool, HoldHeadSHA string, HoldLabels string (comma-separated labels the hold added). Add HoldRedriveCount int. Keep SizeGuardHoldActive and SizeGuardHoldHeadSHA as deprecated fields that are no longer written; do not drop the columns.

Persistence in `internal/autopilot/state_store.go`: add the four columns with ALTER TABLE migrations next to the size_guard_hold_active migration, and add them to the create-table statement, the upsert, both select lists, both scans, and the struct copy in types.go. No backfill.

escalateAndHold in `internal/autopilot/controller.go`: add a parameter redrivable bool. When true, set HoldActive true, HoldHeadSHA to prState.HeadSHA, HoldLabels to the labels joined by comma. When false, clear the triple. Pass true at the four CI-side sites listed above and false everywhere else. Delete the two SizeGuardHoldActive assignments at the size-guard call site; the generic fields replace them.

Rename redriveSizeGuardHeldPR to redriveHeldPR and generalize the gate: Stage equals StageFailed, HoldActive true, ghPR non-nil, ghPR open and not merged, PostMergeSHA empty, newHead non-empty and different from HoldHeadSHA, HoldRedriveCount below 2. When HoldHeadSHA is empty, store the live head as the baseline and return without redrive. On redrive: increment HoldRedriveCount, clear HoldActive and HoldHeadSHA, set HeadSHA to the new head, Stage to StageWaitingCI, CIWaitStartedAt to now, Error and TerminalLabel to empty; keep RebaseAttempts, MergeAttempts, ReadoptCount and CIFixIterations as they are. Remove pilot-needs-human plus every label in HoldLabels through mutateIssueLabels, keeping the existing exception when GetIssue fails or the issue carries the exhausted-ladder label. Post the re-adoption comment with the stored reason from Error instead of the hard-coded size-guard wording. Update the call in processOnePR. Promote the duplicate-registration Debug log in registerPR to Info and include the current stage.

Tests in `internal/autopilot/gh5378_test.go` and `internal/autopilot/escalate_and_hold_test.go`, using the existing newRecordingGHServer harness and the NewController construction those files use:

- TestRedriveHeldPR_RevivesOnNewHead: table-driven over the four redrivable reasons; a held PR whose live head differs from HoldHeadSHA moves to StageWaitingCI, HeadSHA equals the new head, HoldActive is false, and the recorder saw the label removal.
- TestRedriveHeldPR_SameHeadSHA_NoOp.
- TestRedriveHeldPR_EmptyHoldHeadSHA_AdoptsBaselineWithoutRedrive.
- TestRedriveHeldPR_IgnoresMergedOrClosedPR.
- TestRedriveHeldPR_IgnoresPostMergeHolds: a post-merge hold has HoldActive false and never redrives even with a different head.
- TestRedriveHeldPR_CapReached_StaysParked: HoldRedriveCount 2 blocks a third redrive.
- TestRedriveHeldPR_ExhaustedRetryLadder_LeavesLabels.
- TestEscalateAndHold_SetsHoldFields and TestEscalateAndHold_NonRedrivableClearsHoldFields.
- TestController_ProcessAllPRs_RedrivesZeroEvidenceHeldPR: the PR #388 reproduction through the tick.
- TestController_OnPRCreatedForFixIssue_ExistingFailedPR_NoStageChange: pins that registration alone changes nothing.
- TestStateStore_HoldFieldsSurviveRoundTrip in the state store test file that holds TestStateStore_SizeGuardHoldFieldsSurviveRestart; keep that older test passing.
- Rename the existing TestRedriveSizeGuardHeldPR tests to the new function name; keep TestRedriveSizeGuardHeldPR_IgnoresNonSizeGuardHolds as TestRedriveHeldPR_IgnoresIterationCapHolds with the same assertion, and keep TestController_ProcessAllPRs_DoesNotRedriveIterationCapHold passing.

Do not change reAdoptHeldRebasePR, RestoreState, or the breaker redrive. Keep the diff under 550 changed lines.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go test ./internal/autopilot/ -run TestRedriveHeldPR -count=1` passes; paste the output into the PR body.
- `go test ./internal/autopilot/ -run TestEscalateAndHold -count=1` passes; paste the output into the PR body.
- `go test ./internal/autopilot/ -run TestController_ProcessAllPRs -count=1` passes; paste the output into the PR body.
- `go test ./internal/autopilot/ -run TestStateStore -count=1` passes; paste the output into the PR body.
- `go test ./internal/autopilot/ -count=1` passes; paste the output into the PR body.
- `go vet ./internal/autopilot/` passes; paste the output into the PR body.
- pass redrivable false at the zero-evidence call site -> TestController_ProcessAllPRs_RedrivesZeroEvidenceHeldPR fails
- drop the open-and-not-merged check from redriveHeldPR -> TestRedriveHeldPR_IgnoresMergedOrClosedPR fails
- redrive when the live head equals HoldHeadSHA -> TestRedriveHeldPR_SameHeadSHA_NoOp fails
- stop incrementing HoldRedriveCount -> TestRedriveHeldPR_CapReached_StaysParked fails
- leave HoldLabels out of the upsert -> TestStateStore_HoldFieldsSurviveRoundTrip fails
- pass redrivable true at the iteration-cap call site -> TestRedriveHeldPR_IgnoresIterationCapHolds fails

## Refs

- Pilot issue: https://github.com/qf-studio/pilot/issues/5643
- Incident: pilot-console PR #388 (held 07:41Z, continuation 08:31Z, hand-merged 09:47Z, 2026-10-12); contrast pilot PR #5637 (size-guard hold, self-redrove 2026-10-11)
- Prior: GH-5378 (size-guard redrive), GH-5391 (hold supersede clear)
- Code: `internal/autopilot/controller.go` (escalateAndHold, redriveSizeGuardHeldPR, processOnePR, registerPR), `internal/autopilot/types.go` (PRState), `internal/autopilot/state_store.go`
- Follow-up (separate issue): RestoreState skips every StageFailed row except breaker holds, so size-guard and rebase holds do not survive a daemon restart

**Last Updated**: 2026-10-12
