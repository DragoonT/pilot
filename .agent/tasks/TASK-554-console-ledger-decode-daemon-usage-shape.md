# fix(usage): decode the daemon's real GET /api/v1/executions/usage shape in the ledger poller, so the ticket ledger ingests rows at all

**Status**: 🚀 Dispatched to Pilot 2026-10-14 → [#409](https://github.com/qf-studio/pilot-console/issues/409) (labels `pilot` + `no-decompose`; found while re-specifying pilot#5677)
**Created**: 2026-10-14
**Repo**: qf-studio/pilot-console

Blocked by: none

## Context

`pollLedger` in `internal/fleet/usagepoller.go` (PR #405, GH-401) decodes the daemon's usage feed with `daemonUsageRow`: wrapper `{"rows": [...]}` or a bare array, fields `kind`, `taskId`, `estimatedUsdCents`, `reportedUsd`, and it counts a ticket only when `status == "succeeded"`. The daemon's route (pilot GH-5676, released in v2.284.0) serves `{"executions": [...], "nextSince": ..., "hasMore": ...}` with `executionId`, `estimatedCostUSD` in dollars, `reportedCostUSD`, raw daemon statuses such as `completed`, and no `kind`. The wrapper key never matches, so `buildTicketLedgerRows` returns zero rows and nothing is logged above debug. `ticket_ledger` stays empty; `ledgerUsage` in `internal/fleet/usage_meter.go` falls back to the rollup delta, so enforcement still runs but chat dollars (D10) can never be counted. The fixture in `internal/fleet/ticket_ledger_test.go` was written to the assumed shape and never to the daemon's. The daemon will add `kind` ("execution" or "chat_turn") and chat rows under the same shape in a follow-up (pilot issue filed with this one); this decoder must work both before and after that lands.

## Scope

- `internal/fleet/usagepoller.go`: `daemonUsageRow` gains `executionId`, `estimatedCostUSD *float64`, `reportedCostUSD *float64`, `completedAt`; keep `estimatedUsdCents` and `reportedUsd` as fallbacks. `buildTicketLedgerRows` accepts the wrapper key `executions` first, then `rows`, then a bare array. `kind` defaults to "execution" when absent. `estimatedCostUSD` becomes cents as `dollars * 100` kept fractional (the meter rounds once in SQL). Status maps `completed` and `succeeded` to `succeeded`, `failed` to `failed`, anything else is stored as received. A row with an empty `taskId` falls back to `executionId` before it is skipped.
- `pollLedger` follows `hasMore`: after a page with `hasMore` true it requests again with `since = nextSince`, at most 10 pages per tick, and advances `TicketLedgerCursor` to the last page's `nextSince`.
- Add `internal/fleet/testdata/daemon_executions_usage.json`: a verbatim response body of the daemon route as pinned by the daemon's own endpoint test (pilot repo, gateway package, test TestExecutionsUsageEndpoint_RowCarriesAllFields) with a header comment naming that source; the ledger tests decode this file, not a hand-written shape.
- Log at Warn, once per instance per tick, when a non-empty body decodes to zero rows.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go vet ./internal/fleet/` passes; paste the output into the PR body.
- `go test ./internal/fleet/ -run 'TicketLedger|UsagePoller|LedgerUsage' -count=1` passes; paste the output into the PR body. Adds TestBuildTicketLedgerRows_DaemonShape (decodes the testdata file: every row ingested, `kind` "execution", cents = dollars times 100, `reportedUsd` from `reportedCostUSD`, status `succeeded` for `completed`), TestBuildTicketLedgerRows_ChatTurnRow (a row with `kind` "chat_turn" and a `conversationId` is ingested as a chat_turn with its `taskId`), TestPollLedger_FollowsHasMore (two pages, second requested with `since` = first `nextSince`, cursor ends at the second `nextSince`), and TestBuildTicketLedgerRows_ZeroRowsWarns.
- `grep -n '"executions"' internal/fleet/usagepoller.go` prints at least one line; paste the output into the PR body.
- remove the executions wrapper branch -> TestBuildTicketLedgerRows_DaemonShape fails
- drop the completed-to-succeeded mapping -> TestBuildTicketLedgerRows_DaemonShape fails on the ticket status
- stop after the first page -> TestPollLedger_FollowsHasMore fails

## Out of scope

- Changing the daemon shape; the console adapts to it.
- The meter SQL in usage_meter.go.

## Refs

- `internal/fleet/usagepoller.go` (pollLedger, daemonUsageRow, buildTicketLedgerRows), `internal/fleet/ledger_store.go`, `internal/fleet/usage_meter.go` (ledgerUsage), `internal/fleet/ticket_ledger_test.go`, `internal/fleet/usagepoller_test.go`, `internal/db/migrations/0028_ticket_ledger.up.sql`
- Daemon side: pilot GH-5676 (route shipped in v2.284.0) and the pilot issue that adds `kind` + chat rows (filed with this one)

- Pilot issue: https://github.com/qf-studio/pilot-console/issues/409
