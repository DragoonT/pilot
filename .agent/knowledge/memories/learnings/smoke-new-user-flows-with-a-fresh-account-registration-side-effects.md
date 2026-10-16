# Learning: The first real org-invite smoke (2026-10-16) passed every backend and UI test an

## Summary
The first real org-invite smoke (2026-10-16) passed every backend and UI test and still failed for a real invitee: RegisterView's one submit does register→createOrg, the console allows one org per user, and there is no org-delete route, so a new user who registered could never accept (409). Nobody had walked the flow as a brand-new account. Rule: for any user-facing flow that a NEW account enters (invites, shared links, referrals), the smoke must start from a fresh registration, and the spec must name the registration side effects (org creation, onboarding bounces, verification redirects) that can strand the flow. Fixed same morning by ui#237 → PR#238 (TASK-567). Also: a plus-address of a personal Gmail is not readable from a session whose Gmail MCP is the work account — pick the invitee mailbox before the smoke.

## Context
Discovered during development.

## Details
The first real org-invite smoke (2026-10-16) passed every backend and UI test and still failed for a real invitee: RegisterView's one submit does register→createOrg, the console allows one org per user, and there is no org-delete route, so a new user who registered could never accept (409). Nobody had walked the flow as a brand-new account. Rule: for any user-facing flow that a NEW account enters (invites, shared links, referrals), the smoke must start from a fresh registration, and the spec must name the registration side effects (org creation, onboarding bounces, verification redirects) that can strand the flow. Fixed same morning by ui#237 → PR#238 (TASK-567). Also: a plus-address of a personal Gmail is not readable from a session whose Gmail MCP is the work account — pick the invitee mailbox before the smoke.

## Recommended Approach
Apply this knowledge when working on related topics.

## Related
- None documented

---
**Captured**: 2026-10-16
**Confidence**: 90%
**Concepts**: onboarding, false-success, smoke-testing, invites, console-ui
