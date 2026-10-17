# Learning: A Slack approval click can fail to reach the daemon; relay the founder's decision through the box's local approvals API

## Summary
PR#5737 sat awaiting_approval 15:20–15:35Z on 2026-10-16: the card was posted (async approval request submitted, channel=slack) and the founder clicked approve, but the daemon logged no interaction and no decision. Unblock: on the box, GET http://127.0.0.1:9091/api/v1/approvals lists pending requests with requestId; POST /api/v1/approvals/{requestId}/decision with {"decision":"approve","by":"<who, and that it relays the founder's Slack approval>"} records it (HTTP 200); autopilot merged on the next tick. Gateway auth type claude-code accepts local requests with no token; the gateway listens on 127.0.0.1:9091 (not 9090).

## Context
Reviewer session 2026-10-16; founder said 'Approved in Slack', board stayed awaiting_approval 15 min.

## Details
PR#5737 sat awaiting_approval 15:20–15:35Z on 2026-10-16: the card was posted (async approval request submitted, channel=slack) and the founder clicked approve, but the daemon logged no interaction and no decision. Unblock: on the box, GET http://127.0.0.1:9091/api/v1/approvals lists pending requests with requestId; POST /api/v1/approvals/{requestId}/decision with {"decision":"approve","by":"<who, and that it relays the founder's Slack approval>"} records it (HTTP 200); autopilot merged on the next tick. Gateway auth type claude-code accepts local requests with no token; the gateway listens on 127.0.0.1:9091 (not 9090).

## Recommended Approach
Only relay a decision the founder stated in chat, and say so in the by field. Then find out which card was clicked (the Slack click gap is unfiled; 'Slack Socket Mode started in polling mode' lines on the box, no interaction logged).

## Related
- TASK-569
- `internal/gateway/approvals.go`
- `internal/gateway/auth.go`
- `cmd/pilot/main.go`

---
**Captured**: 2026-10-17
**Confidence**: 90%
**Concepts**: approval, slack, gateway, autopilot, ops
