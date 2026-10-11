# Pitfall: A spec that reroutes a whole platform (e.g. all web chat turns) must name the co

## Summary
A spec that reroutes a whole platform (e.g. all web chat turns) must name the composed/integration tests that encode the old flow (internal/gateway TestChatAPI_Composed) and add paste-output bullets for their packages; otherwise Pilot runs only the named package tests, CI fails, and the autopilot size guard (>200 prod additions) refuses an auto-fix -> pilot-needs-human (TASK-520/#5635, 2026-10-11). Before dispatch: git grep the platform string in *_test.go outside the changed package.

## Context
Discovered during development.

## Details
A spec that reroutes a whole platform (e.g. all web chat turns) must name the composed/integration tests that encode the old flow (internal/gateway TestChatAPI_Composed) and add paste-output bullets for their packages; otherwise Pilot runs only the named package tests, CI fails, and the autopilot size guard (>200 prod additions) refuses an auto-fix -> pilot-needs-human (TASK-520/#5635, 2026-10-11). Before dispatch: git grep the platform string in *_test.go outside the changed package.

## Recommended Approach
Apply this knowledge when working on related topics.

## Related
- None documented

---
**Captured**: 2026-10-11
**Confidence**: 90%
**Concepts**: issue-authoring, testing, adapters, gateway, pilot-dispatch, chat
