# Pitfall: RestoreState (internal/autopilot/controller.go ~2713) skips every persisted Stag

## Summary
RestoreState (internal/autopilot/controller.go ~2713) skips every persisted StageFailed row except BreakerHoldActive, so size-guard holds and rebase holds are untracked after a daemon restart (every daily train) and their redrive/re-adopt paths never run; the 'persisted so the hold survives restart' comments are true only on paper. Fix: TASK-529 extends the exception to HoldActive and RebaseHoldActive.

## Context
Discovered during development.

## Details
RestoreState (internal/autopilot/controller.go ~2713) skips every persisted StageFailed row except BreakerHoldActive, so size-guard holds and rebase holds are untracked after a daemon restart (every daily train) and their redrive/re-adopt paths never run; the 'persisted so the hold survives restart' comments are true only on paper. Fix: TASK-529 extends the exception to HoldActive and RebaseHoldActive.

## Recommended Approach
Apply this knowledge when working on related topics.

## Related
- None documented

---
**Captured**: 2026-10-12
**Confidence**: 85%
**Concepts**: autopilot, hold, restart, state-store
