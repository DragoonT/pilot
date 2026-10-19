# Learning: Approver identity is per channel: use approvers_by_channel or projects[].approval.approvers, not one flat list

## Summary
Slack and Telegram user IDs are different identity systems. A flat approval.<stage>.approvers list of Slack IDs makes every Telegram tap 'Not an approver' when a project routes to Telegram. Since PR#5754 (#5753): projects[].approval.approvers > approval.<stage>.approvers_by_channel.<channel> > flat approvers. Caveat until #5755: a valid Telegram ID as the first approver moves the Telegram ask from chat_id to that user's DM (resolveDestChatID is approver-first; Slack is channel-first since GH-4808).

## Context
Founder question 2026-10-19: route Pilot approvals to Slack and Navigator approvals to Telegram. Per-project approval_source already existed (projects[].approval.approval_source).

## Details
Slack and Telegram user IDs are different identity systems. A flat approval.<stage>.approvers list of Slack IDs makes every Telegram tap 'Not an approver' when a project routes to Telegram. Since PR#5754 (#5753): projects[].approval.approvers > approval.<stage>.approvers_by_channel.<channel> > flat approvers. Caveat until #5755: a valid Telegram ID as the first approver moves the Telegram ask from chat_id to that user's DM (resolveDestChatID is approver-first; Slack is channel-first since GH-4808).

## Recommended Approach
For mixed routing set approvers_by_channel per channel. Do not set approvers_by_channel.telegram on the box until #5755 ships.

## Related
- TASK-576
- SOP: approval-channel-routing
- `internal/approval/manager.go`
- `internal/approval/telegram.go`

---
**Captured**: 2026-10-19
**Confidence**: 90%
**Concepts**: approval, config
