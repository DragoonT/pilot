# TASK-589: Daemon-owned daily ticket cap — one hold at `Begin`, console renders the cap and shows the notice

**Status**: 🚀 C14 DISPATCHED 2026-10-26 → console#441 (P16 pilot#5794 → #5807/#5808/#5809 all merged, PR#5835 10-23 12:38Z, in v2.294.0; box on v2.294.1). U19 held until C14 merges. Was: 🚀 P16 DISPATCHED 2026-10-22 → pilot#5794. Design 3 chosen by the founder after nav-research (see § Context). Dispatch order: P16 first; C14 and U19 are held until P16 merges and a daemon release carries it.
**Spec refs**: positioning §4 (pricing v3: daily cap 15), §8.7; roadmap rows P16, C14, U19.
**Origin**: post-merge review of console PR#425 (GH-424, 2026-10-22), defect D1.

## Context

`daily_ticket_cap` (plan allowance, default 15, migration 0030 / GH-403) is enforced in two places with different counters:

| | Reconciler (`enforceDailyTicketCap`, GH-403) | Board gate (`AdmitDispatch`, GH-424 / PR#425) |
|---|---|---|
| Counts | succeeded executions from the ticket ledger | admitted board dispatches, failed ones included |
| Day | UTC | org timezone |
| Key | platform only | any key |
| Effect | switch to own key, or stop the EC2 box | one 429 `daily_cap_reached` |
| Lag | up to the usage poll interval (1 h default) | real time |
| Sees | every path, after the fact | board verb and drag only |

Dispatch paths that never pass the board gate: a `pilot` label set directly in the tracker, chat tasks, epic sub-issues the daemon creates, autopilot fix issues. The pack draw in the board gate counts plan tickets from `ticket_dispatches` (board only) while the billing meter counts the ledger, so packs draw late or never on those paths.

**Decision (founder, 2026-10-22): the daemon owns the cap.** Every execution-creating path already funnels through `ExecutionLifecycle.Begin` (TASK-404), the daemon already enforces a daily chat-turn cap from rendered config (`adapters.chat.daily_turn_cap`, GH-403), and `ErrDispatchGated` already models a pre-dispatch decline. The console renders cap and timezone into the tenant config, reads the daemon's standing for the board notice, deletes both of its gates, and moves the pack draw to ledger ingest where the truthful ticket meter lives.

## Known pitfalls (from memory)

- Base-presence gate: a backticked path that is not on `origin/main` of the target repo parks the issue `pilot-needs-human`. New files are named in prose only.
- Cross-repo `Blocked by:` is not understood by the poller; cross-repo order is handled by holding legs in this doc.
- The executor session has no `DATABASE_URL`, so DB-backed `make test` evidence pasted into a PR body is a failing run; CI on fresh Postgres is the evidence. The box gate itself uses the shared Postgres (prefix fix: console#428).
- The console test fake for the daemon has been more permissive than the real route (mem: `test-fake-daemon-more-permissive-than-real-route-hides-400`): the standing endpoint needs a wire-contract test on both sides.

## Legs — pilot (daemon)

### LEG P16 — repo: qf-studio/pilot — title: feat(executor): daily ticket cap held at ExecutionLifecycle.Begin — config key, org-local day, standing endpoint

## Context
Pilot Cloud caps an org at N tickets per calendar day (plan default 15). Today the console enforces it after the fact from the ticket ledger (lagging, UTC, stops the box) and at its board dispatch verb (misses direct labels, chat-created tickets, epic children and autopilot fix issues). Decision 2026-10-22: the daemon owns the hold, the way it already owns `adapters.chat.daily_turn_cap`. The console will render the two keys below into the tenant config and read the standing endpoint for its board notice (separate console issue).

## Scope
- Config, in `internal/config/config.go` and documented in `configs/pilot.example.yaml` under `executor`:
  - `daily_ticket_cap` (int, 0 = unlimited, default 0 so self-hosted installs are unchanged).
  - `daily_ticket_cap_timezone` (IANA name, default `UTC`; `Local` and unknown names fail validation at load with a clear error naming the key).
- Hold in `ExecutionLifecycle.Begin` (`internal/executor/lifecycle.go`): before a row is created, count distinct task ids that already have an execution row created inside the current org-local calendar day. Counting rules:
  - A retry or repick of the same task id (generation+1) is free: it was counted when first begun.
  - Chat turns are not tickets and are never counted; they keep their own cap.
  - At or above the cap, `Begin` returns an error that wraps `ErrDispatchGated` (new sentinel, for example ErrDailyTicketCapReached, carrying the resume instant) and writes nothing.
- Callers honour the hold without churn:
  - The dispatcher leaves the task where it is (no label change, no comment on the issue) and re-tries on its normal poll after the resume instant. One Info log line per held task per day; one `daily_ticket_cap_hit` alert event per org per day (existing alert engine; cooldown is per rule, so include the day in the message, not the seconds).
  - Epic sub-issue creation (`internal/executor/epic.go`) and autopilot fix issues go through the same `Begin` and are held the same way; the parent is not failed.
  - The chat path (`internal/comms/handler.go`) is unaffected.
- Standing endpoint `GET /api/v1/executions/daily-cap`, same auth as `GET /api/v1/executions/usage` (`internal/gateway/dashboard.go`), JSON:
  `{"cap": 15, "timezone": "Europe/Berlin", "dispatched_today": 15, "reached": true, "resumes_at": "2026-10-23T00:00:00+02:00"}`
  `cap` 0 renders `reached` false and `resumes_at` null. The count query lives in `internal/memory/store.go` next to the usage query the ledger route uses.
- Metric `pilot_daily_ticket_cap_dispatched_today` (gauge) alongside the existing queue metrics.

## Acceptance
- [ ] Table tests in `internal/executor/`: the 16th `Begin` on cap 15 returns the gated error and leaves the executions table unchanged; a generation+1 retry of an already-counted task passes; cap 0 never holds; a chat task is neither counted nor held; the day boundary follows `daily_ticket_cap_timezone` (a `Europe/Berlin` case that differs from UTC).
- [ ] A dispatcher test shows a held task is re-picked after the resume instant with no label mutation and no issue comment.
- [ ] A gateway test asserts the exact JSON shape above for reached and not-reached, and `cap` 0.
- [ ] Config tests: both keys load; `Local` and a bad name fail with the key in the error.
- [ ] `configs/pilot.example.yaml` documents both keys.
- [ ] `make build`, `make test`, `make lint` pass — paste the output into the PR body.

## Out of scope
- Any console or UI change (separate issues).
- The monthly USD ceiling and the chat-turn cap (unchanged).

## Legs — pilot-console (API) — dispatched 10-26 → console#441

### LEG C14 — repo: qf-studio/pilot-console — title: feat(fleet): daily ticket cap owned by the daemon — render cap and timezone into tenant config, read the daemon standing for the board notice, delete both console gates, draw packs at ledger ingest

## Context
The daemon now holds dispatches at the cap (pilot leg TASK-589 P16, standing on GET /api/v1/executions/daily-cap). The console had two enforcers of `daily_ticket_cap` that disagree on day, key source and what counts (post-merge review of PR#425, defect D1): the reconciler in `internal/fleet/allowanceenforce.go` and the board gate from PR#425. Both go. The pack draw moves to ledger ingest, where the billing meter already lives, so packs are drawn for every path and never for a failed run.

## Scope
- Config render (`internal/fleet/configrender.go`): render `executor.daily_ticket_cap` from the org's effective allowance `DailyTicketCap` and `executor.daily_ticket_cap_timezone` from `organizations.timezone`, with the same nil-means-converge rule `DailyChatTurnCap` uses. A timezone change bumps the config generation like a cap change does.
- Reconciler (`internal/fleet/allowanceenforce.go`): remove `enforceDailyTicketCap`, `enforceDailyCapSuspended` and their two call sites; the monthly allowance sweep stays. A new migration drops the daily-cap state table that migration 0030 created, and the `allowance.daily_ticket_cap_hit` event constant goes with it.
- Board (`internal/boardapi/dispatch.go`, `internal/boardapi/handlers.go`): remove the `admitDispatch` holds and the 429 `daily_cap_reached` response. `notice` on the cards response and `daily_cap`, `dispatched_today`, `timezone` on `GET /api/v1/billing/allowance` come from the daemon standing: a small reader in `internal/fleet/` that calls the tenant's daily-cap route the way `internal/fleet/usagepoller.go` calls the usage route, cached per org for 60 s; unreachable daemon renders `notice` null and `dispatched_today` 0 (a notice is an extra, never a reason to fail the board).
- Pack draw (`internal/orgs/tickets.go`, `internal/allowance/status.go`): `AdmitDispatch` goes. A new migration replaces `ticket_dispatches` with a pack-draw table keyed `(org_id, task_id)` (task id as text, the ledger's key), with `pack_id` and `drawn_at`. The draw happens in the usage poller's ledger ingest (`internal/fleet/usagepoller.go`): for each newly ingested succeeded execution on the platform key, once the period's succeeded platform-key ticket count exceeds the plan's included tickets, draw one ticket from the oldest unexpired pack; idempotent per task id; own-key runs never draw. `PackSummary` reads the new table. `Status.PackTickets` semantics unchanged.
- Wiring (`main.go`): drop the board gate; wire the standing reader into the board and allowance deps.

## Acceptance
- [ ] Config-render test shows both `executor` keys for an org with timezone `Europe/Berlin` and cap 15, and the generation bump on a timezone change.
- [ ] Reconciler tests for the daily cap are deleted; the monthly sweep tests still pass.
- [ ] Board tests: dispatch verb and drag to queued never return 429; `notice` is the daemon's text when the standing says reached, null when not reached or unreachable.
- [ ] A wire-contract test on the standing reader uses the exact JSON the daemon leg specifies (`cap`, `timezone`, `dispatched_today`, `reached`, `resumes_at`) and fails on a missing field.
- [ ] Pack-draw tests: ingesting the first succeeded platform-key execution past the plan's included tickets draws from the oldest unexpired pack; a re-ingest of the same task id draws nothing; an own-key execution draws nothing; an expired pack is skipped.
- [ ] Migration test: `ticket_dispatches` rows with a `pack_id` migrate into the new table; the daily-cap state table is gone.
- [ ] `make build`, `make test`, `make lint` pass — paste the output into the PR body.

## Out of scope
- The UI banner (separate issue).
- Changing the cap value or the plan rows.

## Legs — pilot-console-ui — HELD until C14 merges

### LEG U19 — repo: qf-studio/pilot-console-ui — title: feat(board): daily cap banner from the cards response notice; daily_cap_reached toast names the resume time

## Context
The board API returns `notice` on the cards response while the org's daily ticket cap is reached ("Daily cap reached — resumes at 00:00 <tz>"). The UI drops it today: a grep finds no `daily_cap_reached` and `src/views/BoardView.vue` toasts the generic error message. After the console change the hold happens on the daemon, so the banner is the only signal the user gets.

## Scope
- `src/lib/api/httpAdapter.ts`: surface `notice` from the cards response on the board model; map a 429 body with `code` `daily_cap_reached` (still possible from an older console) to a typed error carrying `notice` and `resumes_at`.
- `src/views/BoardView.vue`: render `notice` as a one-line banner above the columns using the SectionHeader and Chip primitives from the 2026-10 tokens; hide it when `notice` is null. The toast for the typed error shows `notice`, not the generic message.
- No layout change beyond the banner row.

## Acceptance
- [ ] A component test renders the banner for a non-null `notice` and nothing for null.
- [ ] An adapter test maps the 429 `daily_cap_reached` body to the typed error with `notice` and `resumes_at`.
- [ ] `npm run build`, `npm test`, `npm run lint` pass — paste the output into the PR body.

## Held legs

| Leg | Repo | After | Why held |
|---|---|---|---|
| C14 | pilot-console | P16 merged and in a daemon release on the fleet AMI / self-upgrade train | needs the standing route on tenants |
| U19 | pilot-console-ui | C14 merged | needs `notice` sourced from the daemon |

## Refs

- P16 → https://github.com/qf-studio/pilot/issues/5794
- C14 → https://github.com/qf-studio/pilot-console/issues/441
