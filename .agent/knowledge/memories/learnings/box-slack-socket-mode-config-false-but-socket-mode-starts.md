# Learning: Box Slack ingress is Socket Mode: the `--slack` start flag overrides config socket_mode: false

## Summary
The box config has adapters.slack.socket_mode: false, yet daemon.log shows 'Slack Socket Mode started in polling mode'. Cause: the daemon starts with `--slack`, and cmd/pilot/main.go sets `cfg.Adapters.Slack.SocketMode = slackFlag` whenever the flag is present. The flag overrides the config file. Clicks reach the box through Socket Mode. The old SOP claim 'buttons work because socket_mode: false (HTTP interactivity)' was wrong; corrected 2026-10-19.

## Context
TASK-576 research 2026-10-19 while scoping leg C (#5758); the 10-16 lost Slack click (PR#5737) is still unexplained.

## Details
On 2026-10-19 the box config had adapters.slack.socket_mode: false, while daemon.log showed 'Slack Socket Mode started in polling mode' (10-16, 10-17) and a Socket Mode reconnect about every 5 h. Polling mode starts Socket Mode only when SocketMode is true (main.go GH-652 block), and the HTTP interactions route is registered only inside pilot.New (gateway mode). The SOP claim 'buttons work because socket_mode: false (HTTP interactivity)' is therefore unproven.

## Recommended Approach
Read the run mode from the start command line, not from the config file, when any `--<adapter>` flag is present. Leg C (#5758) adds a startup INFO line with the effective socket_mode and the interactions-route state so the log is the source of truth. The 10-16 lost click (PR#5737) is still unexplained; the leg C per-interaction INFO log is the next diagnostic.

## Related
- TASK-576
- SOP: approval-channel-routing
- `cmd/pilot/main.go`
- `internal/pilot/pilot.go`

---
**Captured**: 2026-10-19
**Confidence**: 95%
**Concepts**: approval, adapters, gateway
