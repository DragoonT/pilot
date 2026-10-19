# Learning: Box Slack ingress is unclear: config socket_mode is false, but the daemon logs 'Slack Socket Mode started in polling mode'

## Summary
On 2026-10-19 the box config had adapters.slack.socket_mode: false, while daemon.log showed 'Slack Socket Mode started in polling mode' (10-16, 10-17) and a Socket Mode reconnect about every 5 h. Polling mode starts Socket Mode only when SocketMode is true (main.go GH-652 block), and the HTTP interactions route is registered only inside pilot.New (gateway mode). The SOP claim 'buttons work because socket_mode: false (HTTP interactivity)' is therefore unproven.

## Context
TASK-576 research 2026-10-19 while scoping leg C (#5758); the 10-16 lost Slack click (PR#5737) is still unexplained.

## Details
On 2026-10-19 the box config had adapters.slack.socket_mode: false, while daemon.log showed 'Slack Socket Mode started in polling mode' (10-16, 10-17) and a Socket Mode reconnect about every 5 h. Polling mode starts Socket Mode only when SocketMode is true (main.go GH-652 block), and the HTTP interactions route is registered only inside pilot.New (gateway mode). The SOP claim 'buttons work because socket_mode: false (HTTP interactivity)' is therefore unproven.

## Recommended Approach
Before changing Slack approval ingress (leg C) or the box config, establish which path delivers clicks today: check the effective config value at startup and log each received interaction at INFO.

## Related
- TASK-576
- SOP: approval-channel-routing
- `cmd/pilot/main.go`
- `internal/pilot/pilot.go`

---
**Captured**: 2026-10-19
**Confidence**: 70%
**Concepts**: approval, adapters, gateway
