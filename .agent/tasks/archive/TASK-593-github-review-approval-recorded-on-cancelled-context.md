# TASK-593: github-review approvals dropped since v2.290.0 — the poller records the decision on a context it just cancelled

**Status**: ✅ Merged 2026-10-26 — #5803 → PR#5872. Post-merge review posted 2026-10-27 **APPROVE-WITH-NOTES** (detached bounded write correct; defect: Manager early-return skips waiter cleanup on sql.ErrNoRows → TASK-603 / #5888).
**Spec refs**: #5764 (persist + rehydrate github-review approval requests, commit 27ff0d246, v2.290.0) introduced the path; #5716 / #5752 (per-repo approval lookup, head-SHA check) are the v2.289.0 baseline the reporter compares against.
**Origin**: external report by @scrappydog (2026-10-22). Verified against main at v2.295.0: every quoted log line exists verbatim; the cause the reporter suggested is the actual cause.

## Context

`internal/approval/github.go` polls GitHub for an APPROVED review. `pollForApproval` runs on a `pollCtx` created with `context.WithCancel`; its cancel function is stored on the pending entry as `CancelFn`. When `checkApproval` sees the approval it logs "PR approved", removes the entry from `pending`, calls `pending.CancelFn()` — and then calls `h.resolvePending(ctx, …)` with the same ctx it just cancelled. `resolvePending` → `Manager.RecordDecision` → `SetApprovalDecision` → `store.db.ExecContext(ctx, …)`, which fails at once with `context canceled`. `RecordDecision` wraps the error, deletes the pending entry and logs the misleading "approval decision race lost" line. The PR stays `awaiting_approval` with no waiter until the pre-merge timeout rejects it. Only the poller path is affected; the webhook and cancel paths pass the caller's own ctx. No commit between v2.290.0 and HEAD touches `internal/approval/github.go`; the existing tests build pending entries with a live cancel and never exercise a recorder on a cancelled ctx.

## Legs — pilot (daemon)

### LEG B1 — repo: qf-studio/pilot — title: fix(approval): github-review poller records the approval decision on the context it just cancelled, so every polled approval is dropped since v2.290.0

## Context
Reported by @scrappydog on v2.291.0 (original report in this issue's edit history): with approval_source github-review, every approval is detected and then dropped. 3 of 3 approvals across two repos, on both routes into awaiting_approval (CI pass and the >500-net-lines merge-gate escalation), and at every timing, including an approval already present when the waiter started. Worked on v2.289.0. The reporter rolled back.

```
level=INFO msg="PR approved" component=approval.github request_id=pr-N-… pr_number=N approver=<reviewer>
level=WARN msg="failed to persist approval decision to executions" component=autopilot pr=N request_id=pr-N-… op=SetApprovalDecision decision=approved error="SetApprovalDecision: context canceled"
level=INFO msg="approval decision race lost — waiter cleaned up without applying decision" component=approval request_id=pr-N-… decision=approved error="record decision: SetApprovalDecision: context canceled"
level=WARN msg="failed to record approval decision" component=approval.github request_id=pr-N-… error="record decision: SetApprovalDecision: context canceled"
```

Verified cause (main at v2.295.0): in `internal/approval/github.go`, checkApproval runs on the pollCtx that pollForApproval created with context.WithCancel; the entry's CancelFn cancels that same ctx. checkApproval calls pending.CancelFn() and then h.resolvePending(ctx, …) with the cancelled ctx. resolvePending calls Manager.RecordDecision (`internal/approval/manager.go`), which calls SetApprovalDecision, which reaches ExecContext in `internal/memory/store.go` and fails with context canceled. RecordDecision then deletes the pending entry and logs "race lost". The rehydrated-poll path (the request restored at startup by #5764) uses the same checkApproval and fails the same way. The webhook and cancel paths pass the caller's ctx and are unaffected. Introduced by #5764 (commit 27ff0d246, v2.290.0); nothing on main after v2.290.0 touches this file.

probe: present qf-studio/pilot pending\.CancelFn\(\)
probe: present qf-studio/pilot h\.resolvePending\(ctx, pending
probe: absent  qf-studio/pilot resolvePending\(context\.WithoutCancel

## Scope
- In checkApproval, record the decision on a context that survives the poll cancel: pass context.WithoutCancel(ctx) to resolvePending, bounded by a short timeout (10 s) so the write cannot hang. Keep the CancelFn call; its order relative to resolvePending no longer matters once the write context is detached.
- Apply the same change to every call site that resolves a pending entry from inside the poll goroutine (the fresh-request path and the rehydrated-request path share checkApproval; confirm there is no second copy).
- In Manager.RecordDecision, distinguish a real lost race from a write failure: when the recorder returns an error that is not memory.ErrApprovalAlreadyDecided, log it at WARN as a persistence failure with the error, not as "race lost", and do not delete the pending entry so the next poll tick can retry the write. Keep the current "race lost" INFO line only for ErrApprovalAlreadyDecided.
- No behaviour change for the webhook path, the cancel path, Slack or Telegram handlers.

## Acceptance
- [ ] New test in `internal/approval/github_test.go`: a fake DecisionRecorder returns ctx.Err() when its ctx is done; drive checkApproval with a fake client that returns an APPROVED review on a pollCtx whose cancel is wired as the pending entry's CancelFn; assert the recorder saw a non-cancelled ctx and recorded DecisionApproved, and that the waiter receives the approved Response.
- [ ] Same test on the rehydrated path: build the pending entry the way the startup rehydrate does and assert the same outcome.
- [ ] Manager test: RecordDecision with a recorder that returns a plain error keeps the pending entry and logs a persistence failure; with ErrApprovalAlreadyDecided it removes the entry and logs race lost.
- [ ] revert the resolvePending call to the cancelled poll ctx -> TestCheckApproval_RecordsDecisionOnDetachedContext fails
- [ ] make RecordDecision delete the pending entry on a plain recorder error -> TestRecordDecision_PersistenceErrorKeepsPending fails
- [ ] `go test -race ./internal/approval/` passes; paste the output into the PR body.
- [ ] Do not re-run make build, make test or make lint as evidence: the daemon's quality gates already run them on this repo (21–36 min on the box), and a second run overruns the 1-hour task budget before the PR is created.

## Out of scope
- Changing the approval poll interval, the pre-merge timeout or default_action.
- Persisting approval requests differently (#5764 stays as is).
- Slack and Telegram approval handlers.

## Refs
- B1 → https://github.com/qf-studio/pilot/issues/5803
- Pilot issue: https://github.com/qf-studio/pilot/issues/5803 (reporter @scrappydog; original text in the edit history)
- Introducing change: #5764 → commit 27ff0d246 (v2.290.0)
- Baseline the reporter compares against: #5716 → PR#5746, #5749 → PR#5752 (v2.289.0)

**Last Updated**: 2026-10-26
