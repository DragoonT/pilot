# Pitfall: Infra-classified re-picks bypass the 5-drop hard cap, the backoff window and the identical-failure streak; only dispatcherInfraRepickCap=8 bounds them

## Summary
A rejected push is classed infra (runner.go infraErrorSignatures 'push failed'). priorClaimWasInfra re-picks 'without counting toward repick hard cap' (dispatcher.go ~2105-2152); the only bound is dispatcherInfraRepickCap = 8 per task, no backoff, no cross-task coordination. A deterministic infra failure (branch owned by another run) therefore costs up to eight ~25-minute Sonnet runs before stallTaskAfterInfraCap.

## Context
GH-5731 re-pick loop 2026-10-16; nav-research 2026-10-17 on dispatcher.go:1422, 2105-2152, 1636-1651.

## Details
A rejected push is classed infra (runner.go infraErrorSignatures 'push failed'). priorClaimWasInfra re-picks 'without counting toward repick hard cap' (dispatcher.go ~2105-2152); the only bound is dispatcherInfraRepickCap = 8 per task, no backoff, no cross-task coordination. A deterministic infra failure (branch owned by another run) therefore costs up to eight ~25-minute Sonnet runs before stallTaskAfterInfraCap.

## Recommended Approach
When an infra failure repeats with the identical reason, treat it like a failed streak (count toward backoff) or stall after 2. Until then, break loops by hand (remove the pilot label). Check GetInfraDropCount reset on success before relying on the cap.

## Related
- TASK-573
- `internal/executor/dispatcher.go`
- `internal/executor/runner.go`

---
**Captured**: 2026-10-17
**Confidence**: 85%
**Concepts**: repick, infra, dispatcher, git-push
