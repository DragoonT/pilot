# Pitfall: An approval request with no registered handler returns success; the controller clock then applies default_action

## Summary
Manager.SubmitApprovalRequest returns (req.ID, nil) when the stage is enabled but no handler is registered: nothing is sent, no pending entry. The autopilot controller waits, and its wall-clock guard applies approval.pre_merge.default_action - with 'approved' an ask no human saw approves the PR; with 'rejected' the PR waits the full timeout with no signal.

## Context
nav-research mapping of outbound message paths, 2026-10-19 (origin/main dc2ae0295). manager.go handler==nil branch; controller.go handleAwaitApproval wall-clock guard (post-restart path 3).

## Details
Only the live-smoke hold (GH-5599) fails closed on the clock. preferredMissing (GH-4380) already errors for an explicit unregistered channel; the no-handler-at-all branch was the gap. Fix dispatched as #5756 (TASK-576 leg A).

## Recommended Approach
Treat any 'request accepted, nothing sent' path as a gate bypass. When reviewing approval code, check every success return that does not create a pending entry, and check what the controller clock does with it.

## Related
- TASK-576
- `internal/approval/manager.go`
- `internal/autopilot/controller.go`

---
**Captured**: 2026-10-19
**Confidence**: 90%
**Concepts**: approval, autopilot
