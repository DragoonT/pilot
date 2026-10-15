# fix(usage): send since on the first ledger poll, so a fresh ticket ledger stops failing with 400 forever

**Status**: ✅ MERGED + REVIEWED 2026-10-15 → [console#411](https://github.com/qf-studio/pilot-console/issues/411) → PR#412 merged 11:44Z, post-merge review APPROVE-w-notes (reviewer ran the 3 DB-gated tests: PASS; pin kills: both tests fail with `ledger: unexpected status 400`). **PROD VERIFIED 12:10Z**: console prod-0.1.33 (reconciler td 46, 11:59Z); first tick 12:10:28Z had no 400 for org 425f9f99; `ticket_ledger` holds 4 execution rows for that org (GH-3/5/7/9, est 69.71 cents) — read via a one-off psql container on the fleet instance. Still 0 chat_turn rows (tenant `chat_turns` is empty: the 10-14 smoke predates chat recording, v2.285.0+) and `key_source=unknown`/NULL (rows predate PR#5681 = v2.285.0; AND this tenant's SSM path has no `PILOT_ANTHROPIC_KEY_SOURCE` — legacy layout from 09-25, so new runs will record `unknown` and the meter counts $0 platform for it). **Chat row PROVEN 12:55Z**: one web chat turn at 12:51:57Z (model claude-opus-5[1m], est 16.613 c, reported 16.719 c) was on the daemon wire as `kind=chat_turn` and landed in `ticket_ledger` on the 12:55:28Z tick. Ledger = 4 execution + 1 chat_turn for org 425f9f99. Remaining founder item: this tenant records `key_source=unknown` (legacy SSM layout) so the meter never counts it. Side observation, not filed: the side chat answered from a checkout on `pilot/GH-5`, not main.
**Created**: 2026-10-15
**Repo**: qf-studio/pilot-console

Blocked by: none

## Context

`pollLedger` in `internal/fleet/usagepoller.go` (PR #410, GH-409) reads `TicketLedgerCursor` and omits the `since` query parameter when the cursor is zero (comment: "omitted on the first poll"). The daemon route `GET /api/v1/executions/usage` (pilot GH-5676, handler handleExecutionsUsage in the pilot repo, gateway package, file dashboard.go) requires `since` and answers `400 since is required (RFC3339)` when it is absent. A ledger with zero rows has a zero cursor, so the first poll is rejected, no row is ingested, the cursor stays zero, and every later poll repeats the same request. Observed on prod: the console-reconciler log shows `usage poller: poll instance failed ... error: "ledger: unexpected status 400"` every 15 minutes for the founder tenant org `425f9f99` (instance `404746db`) from 2026-10-14 14:xxZ to now; `ticket_ledger` is empty for every org. The test fake in `internal/fleet/ticket_ledger_test.go` (`TestPollLedger_FollowsHasMore`) serves rows for an empty `since`, which the real daemon never does, so the gap was invisible to the suite.

## Scope

- `internal/fleet/usagepoller.go`: when the cursor is zero, send `since=1970-01-01T00:00:00Z` (the Unix epoch in RFC3339) instead of omitting the parameter. The daemon pages the backfill via `hasMore`, and `pollLedger` already follows up to `maxLedgerPages` pages per tick and resumes from the stored cursor on the next tick. Update the function comment to say the first poll sends the epoch.
- `internal/fleet/ticket_ledger_test.go`: make the fake daemon in `TestPollLedger_FollowsHasMore` answer `400` for an empty `since`, as the real route does, and branch its two pages on the epoch value and on `nextSince` instead of on empty and non-empty. Add `TestPollLedger_FirstPollSendsEpochSince`: zero cursor, fake daemon that answers `400` for an empty `since` and one row for `since=1970-01-01T00:00:00Z`; assert the first request carried the epoch, the row was upserted, and `TicketLedgerCursor` moved off zero.
- No daemon change. The console adapts to the daemon.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go vet ./internal/fleet/` passes; paste the output into the PR body.
- `DATABASE_URL` is set in CI; `go test ./internal/fleet/ -run 'PollLedger' -count=1 -v` prints `--- PASS` for `TestPollLedger_FirstPollSendsEpochSince` and `TestPollLedger_FollowsHasMore`; paste the `--- PASS` lines into the PR body. An `ok internal/fleet 0.0Xs` line alone is a skip and does not meet this acceptance.
- `internal/fleet/usagepoller.go` contains the literal `1970-01-01T00:00:00Z` exactly once, in the zero-cursor branch of `pollLedger`.
- Pin: restore the empty-string `since` on a zero cursor -> `TestPollLedger_FirstPollSendsEpochSince` fails.

## Out of scope

- Changing the daemon route to default `since`.
- The meter SQL in `internal/fleet/usage_meter.go`.
- The Testica org 503 (instance `aae5248c` is a stopped exhaustion-test box; expected).

## Refs

- `internal/fleet/usagepoller.go` (pollLedger, fetchLedgerPage), `internal/fleet/ticket_ledger_test.go` (TestPollLedger_FollowsHasMore)
- Daemon side: pilot repo, gateway package, file dashboard.go, handleExecutionsUsage (GH-5676); 400 branch `since is required (RFC3339)`
- Predecessor: [TASK-554](archive/TASK-554-console-ledger-decode-daemon-usage-shape.md) → console#409 → PR#410
- Pilot issue: https://github.com/qf-studio/pilot-console/issues/411
