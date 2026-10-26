# TASK-576: Outbound messaging gaps — approvals and notices that silently go nowhere

**Status**: ✅ ALL 5 LEGS + #5755 MERGED AND POST-MERGE REVIEWED 2026-10-19 (PR#5763/#5764/#5765/#5766/#5767/#5768, 16:37→19:00Z). Box operator steps after v2.290.0 (10-20 14:00Z train): `Slack ingress` line read ✅ 15:09Z · `lifecycle_notifications: true` ✅ 15:04Z (no Telegram notice confirmed yet) · `approvers_by_channel.telegram` hold lift — **not verified**.
**Created**: 2026-10-19
**Assignee**: Pilot

---

## Context

**Problem**:
A navigator-research mapping of every outbound message path (approvals, alerts, task lifecycle, PR notices, briefs, chat) found five places where a message or decision silently goes nowhere. Two of them can release or stall the human merge gate without any signal. The mapping was done on origin/main `dc2ae0295` after the #5716 / #5749 / #5753 approval fixes.

**Goal**:
Every outbound path either delivers or fails loudly, and every approval request has exactly one deterministic handler that survives a restart.

**Wiring summary** (from the 2026-10-19 research; line numbers on origin/main):

- Approvals: autopilot controller (`submitAsyncApprovalRequest`, the only producer, pre-merge only) → `approval.Manager.SubmitApprovalRequest` → one handler by `approval_source` (Slack / Telegram / GitHub) → handler resolves its own destination. Decisions come back through Telegram callbacks, Slack interactions (Socket Mode in polling mode, HTTP webhook in gateway mode) or GitHub review polling.
- Alerts: executor and autopilot → `alerts.Engine` → `Dispatcher` → channels from `alerts.channels[]` (global only).
- Task lifecycle: orchestrator → `slack.Notifier` → `adapters.slack.channel` (gateway `pilot.New` path).
- PR notices: autopilot controller → `Notifier` interface → **nothing** (never wired).
- Briefs and receipts: schedulers → delivery service → `daily_brief.channels[]` / Telegram chat.
- Chat: inbound message → comms handler → reply to the same chat.
- Transport clients are not shared: each site builds its own Slack or Telegram client from the same bot token.

---

## Known Pitfalls & Patterns

- **LEARNING** (95%, slack-routing-three-keys-alerts-vs-approvals-vs-chat): Slack destinations come from three keys (`alerts.channels[].slack.channel`, `adapters.slack.approval.channel`, `adapters.slack.channel`). Leg C and leg D must not add a fourth key without a reason.
- **LEARNING** (90%, slack-approval-click-not-received-relay-via-local-decision-api): on 2026-10-16 a Slack approve click never reached the box daemon. Leg C adds an INFO log per received interaction so the next lost click is visible.
- **PITFALL** (95%, slack-approval-socket-mode-unroutable): Slack buttons were unroutable on Socket Mode before #4411/#4431. Leg C must keep both ingress paths (Socket Mode and HTTP) working.
- **PITFALL** (95%, box-logs-info-debug-lines-never-land): the box logs at INFO. Every new observability line in these legs is INFO or WARN.
- **PITFALL** (90%, spec-rerouting-a-platform-must-rewrite-composed-tests-of-the-old-flow): leg C changes how gateway mode builds the Slack approval handler. Its issue names the gateway and pilot packages for tests.

---

## Legs (ordered by risk, chained with `Blocked by`)

| Leg | Risk | Gap | Issue |
|-----|------|-----|-------|
| A | **High** | `handler == nil` returns success; the wall-clock guard then applies `default_action` — with `approved` an unrouted ask auto-approves | [#5756](https://github.com/qf-studio/pilot/issues/5756) |
| B | High | GitHub-review approvals are not persisted; after a restart a GitHub approval is never detected | [#5757](https://github.com/qf-studio/pilot/issues/5757) |
| C | Medium | Gateway mode builds two Slack approval stacks; polling mode without Socket Mode has no click ingress | [#5758](https://github.com/qf-studio/pilot/issues/5758) |
| D | Medium | Autopilot `Notifier` is never wired: merged / CI failed / approval required / fix issue / released notices are never sent; `notify_on_release` is dead | [#5759](https://github.com/qf-studio/pilot/issues/5759) |
| E | Low | Empty `PreferredChannel` picks a handler by Go map order; rehydrate gives empty rows to Telegram | [#5760](https://github.com/qf-studio/pilot/issues/5760) |

The legs are chained (A → B → C → D → E) because A and E both edit `internal/approval/manager.go`, and B, C and D all edit `cmd/pilot/main.go`.

**Leg C open question (found after dispatch, 2026-10-19):** the box config has `adapters.slack.socket_mode: false`, but daemon.log shows "Slack Socket Mode started in polling mode" and a reconnect about every 5 h. The polling-mode Socket Mode block requires `SocketMode` true, and the HTTP interactions route exists only in `pilot.New`. So the effective value differs from the file, or the research missed a path. Settle this before leg C's PR is reviewed: the PR must not break the path that delivers clicks on the box today. Memory `box-slack-socket-mode-config-false-but-socket-mode-starts`. The #5758 body does not carry this yet.

---

## Acceptance Criteria

- [x] A: an enabled approval stage with no resolvable handler makes `SubmitApprovalRequest` return an error; the PR is never merged by the clock.
- [x] B: a github-review approval request survives a daemon restart and resolves when the PR is approved after the restart.
- [x] C: each run mode has exactly one Slack approval handler instance, and a click on a card resolves the request that card belongs to.
- [x] D: with Telegram configured and the new opt-in key enabled, a merged PR produces one Telegram notice; with the key off, behavior is unchanged.
- [x] E: approval routing never depends on Go map iteration order.

---

## Technical Decisions

| Decision | Options | Chosen | Reasoning |
|----------|---------|--------|-----------|
| No handler registered | auto-approve · wait for clock · error | Error (fail closed) | Same rule as GH-4380 (`preferredMissing`). The controller already alerts once on submit errors. |
| GitHub rehydrate, project not resolvable | default repo · skip | Skip and log WARN | #5716 rule: never check the default repo for another project's PR. |
| Gateway double Slack stack | keep two · inject one | Inject main.go's handler and manager into `pilot.New` | One `pending` map per process; matches the existing `WithTelegramApprovalHandler` option. |
| Polling mode, Slack HTTP interactivity | register route · refuse config | Register the route on the background gateway when the gateway runs; otherwise fail validation | Buttons that cannot work must not be posted. |
| PR notices default | on · off | Opt-in key, default off | Turning on new Telegram traffic for every existing user on upgrade is a behavior change. The founder box enables it explicitly. |
| Empty `PreferredChannel` | map order · default channel · error | `DefaultChannelName` handler, else error | Matches the existing rehydrate ownership rule (`ownsChannel`). |

---

## Out of Scope

- Per-project routing for alerts and briefs (global only today).
- Sharing one Slack or Telegram client per bot token across senders (rate-limit state is per client).
- The Telegram channel-first destination rule — tracked separately in #5755.
- Alert dispatch backlog drops and the int64 vs string Telegram `chat_id` mismatch.

---

## Verify

```bash
go test ./internal/approval/... ./internal/autopilot/... ./internal/pilot/... ./cmd/pilot/...
make lint
```

---

## Done

- [x] [#5756](https://github.com/qf-studio/pilot/issues/5756)–[#5760](https://github.com/qf-studio/pilot/issues/5760) merged and post-merge reviewed.
  - Leg A ran 6× `status=infra` on 2026-10-19 (stale `origin/pilot/GH-5756` from an auto-preserve push; executor bug, not the leg). Remote branch deleted 15:32Z; bug filed as [#5762](https://github.com/qf-studio/pilot/issues/5762). **PR#5763 reviewed 2026-10-19 15:55Z: APPROVE-w-notes** (mutation verified locally: both new tests kill the old success return; notes: operator-facing fail-closed behaviour worth a docs line, handler map-iteration is leg E). **Leg A merged 16:37Z (4191a47) after a platform-breaker hold during the GitHub Actions incident. Leg B PR#5764 reviewed 17:10Z: APPROVE-w-notes** (mutation + race verified; unresolvable project rows skipped with WARN and no GitHub call; box has no GitHub handler, so no behaviour change there).
  - **Legs C/D/E + #5755 autopilot-merged 17:36Z / 18:06Z / 18:35Z / 19:00Z (PR#5765 / #5766 / #5767 / #5768); all four post-merge reviewed 19:30Z, APPROVE (C, D, #5755 with notes; E clean).** Each verified on main: uncached tests, lint 0 issues, one mutation per leg killed (C: ignore injected manager → wiring test fails; D: never SetNotifier → wiring test fails; E: map-range pick → determinism test fails, Slack won ~75% of picks; #5755: approver-first → 5 tests fail). Notes: box polling+`--slack` = Socket Mode effective, read the new `Slack ingress` INFO line after v2.290.0; D needs the operator opt-in on the box; E only changes producers with an explicitly empty `approval_source`; #5768's `make lint` showed 3 pre-existing `SA4023` hits in `cmd/pilot/tunnel.go` on the box toolchain only (CI lint green).
- [ ] Box: after the release that carries leg D, enable the opt-in key and confirm one Telegram notice for the next merged PR. (Key enabled 10-20 15:04Z; notice not yet confirmed.)
- [ ] `.agent/system/references/reference_slack_notifications_routing.md` row for Telegram PR notices corrected after leg D ships.

---

## Refs

- #5716, #5749, #5753, #5755 (approval routing fixes of 2026-10-19)
- `.agent/system/references/reference_slack_notifications_routing.md`
- `.agent/sops/autopilot/approval-channel-routing.md`

---

**Last Updated**: 2026-10-19
