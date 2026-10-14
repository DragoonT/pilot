# feat(gateway): extend GET /api/v1/executions/usage with a kind field and chat_turn rows on top of GH-5676, keeping the chat_turns table, recording and metrics from PR #5682

**Status**: 🚀 Dispatched to Pilot 2026-10-14 → [#5690](https://github.com/qf-studio/pilot/issues/5690) (labels `pilot` + `no-decompose`; re-spec of #5677; supersedes PR #5682)
**Created**: 2026-10-14
**Repo**: qf-studio/pilot

Blocked by: none (GH-5676 and GH-5678 are on main)

## Context

PR #5682 (issue #5677) cannot rebase. It took the issue's fallback bullet ("if the key-source issue is not merged yet, add the endpoint here") after GH-5676 had already merged, so it registers `GET /api/v1/executions/usage` a second time with its own `handleUsage` and its own `ListUsageExecutionsSince`, which drops `keySource` and `reportedCostUSD` (a regression against #5681). GH-5678 also moved the chat handler and the Prometheus block it edits. The parts of PR #5682 that do not clash are correct and wanted: the `chat_turns` table and queries, the `ChatTurnResult` token, cost, model and duration fields, the per-turn recording, the two Prometheus series and the `/api/v1/metrics` chat fields.

The console ledger poller (console PR #405) reads this route with one call and expects a `kind` field so one feed carries executions and chat turns. The console decoder is fixed separately to the daemon's shipped shape (console issue filed with this one); this issue only adds `kind` and the chat rows. Keep everything GH-5676 ships: wrapper `executions`, `estimatedCostUSD` in dollars, `reportedCostUSD`, raw daemon `status`, `nextSince`, `hasMore`, the 1000-row cap and the inclusive `since`.

## Scope

- Start from main. Re-apply from branch `pilot/GH-5677` (head 0bd7ae810) by hand, not by merge: `internal/memory/chat_turns.go` (ChatTurn, SaveChatTurn, ListChatTurnsSince, GetChatTotalsByKeySource, GetChatTotalsSince, GetChatDailySince) and the `chat_turns` table in `internal/memory/store.go`; the `ChatTurnResult` fields and cost estimate in `internal/executor/chat_turn.go` plus the backend lines that fill them; `recordChatTurn` in `internal/comms/chat_turn_handler.go`; the Prometheus series and `SetChatSource` in `internal/gateway/prometheus.go`; the `ChatUsageStore` interface and the `chatTurns`, `chatCostUSD`, `chatTokens`, `chatDaily` metrics fields in `internal/gateway/dashboard.go`; the wiring in `internal/gateway/server.go` and `cmd/pilot/main.go`; the tests `internal/comms/chat_turn_record_test.go`, `internal/memory/chat_turns_test.go` and the chat cases in `internal/executor/chat_turn_test.go`. Do not bring `internal/gateway/usage.go`, `internal/memory/usage_rows.go`, the second route registration, or the handler's own `chatKeySource()`; use the key-source helper GH-5676 added in `internal/memory`.
- `recordChatTurn` runs only after `reserveDailyTurn` (GH-5678) admitted the turn. A cap-rejected turn writes no row.
- `internal/gateway/dashboard.go`: add `Kind string json:"kind"` ("execution" or "chat_turn") and `ConversationID string json:"conversationId,omitempty"` to `executionUsageRow`. `handleExecutionsUsage` returns one page merged from `GetExecutionUsageSince` and the chat rows: oldest first by `completedAt`, inclusive `since`, at most `MaxExecutionUsageRows` rows in total, `nextSince` = the newest `completedAt` in the page, `hasMore` true when either source had more. A chat row sets `kind` "chat_turn", `executionId` and `taskId` to the chat row id (the console skips rows with an empty `taskId`), `conversationId`, `startedAt` non-null, `prUrl` empty, `keySource` and `reportedCostUSD` from the row. Execution rows keep every GH-5676 field and get `kind` "execution". Put the merge in one store method `GetUsageSince(since, projectPath)` in `internal/memory` so the ordering key is one string form for both tables.
- Prometheus: the two chat series sit next to GH-5678's `pilot_chat_turns_rejected_total`.
- `.agent/system/FEATURE-MATRIX.md`: one row "Web chat turn metering", below the GH-5676 row.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go vet ./internal/gateway/ ./internal/memory/ ./internal/comms/` passes; paste the output into the PR body.
- `go test ./internal/gateway/ -run 'ExecutionsUsage|Metrics|Prometheus' -count=1` passes; paste the output into the PR body. TestExecutionsUsageEndpoint_RowCarriesAllFields is extended: every execution row carries `kind` "execution" and every field of GH-5676; a chat row carries `kind` "chat_turn", a non-empty `taskId`, `conversationId`, non-null `startedAt`, `keySource` and `reportedCostUSD`. Adds TestExecutionsUsageEndpoint_MergedPageOrderAndCursor: two execution rows and two chat rows interleaved in time come back oldest first in one page, `nextSince` is the newest `completedAt`, and with a cap of 3 (test override) `hasMore` is true and the oldest three come back.
- `go test ./internal/memory/ -run 'UsageSince|ChatTurn' -count=1` passes; paste the output into the PR body.
- `go test ./internal/comms/ -run 'ChatTurn' -count=1` passes; paste the output into the PR body. Adds TestChatTurn_CapRejectedTurnWritesNoRow.
- `grep -rn 'executions/usage' internal/gateway/server.go` prints exactly one line; paste the output into the PR body.
- drop the kind field from the execution rows -> TestExecutionsUsageEndpoint_RowCarriesAllFields fails
- sort the merged page newest first -> TestExecutionsUsageEndpoint_MergedPageOrderAndCursor fails
- call recordChatTurn before reserveDailyTurn -> TestChatTurn_CapRejectedTurnWritesNoRow fails

## Out of scope

- The console decoder (separate console issue).
- Any change to the daily chat-turn cap (GH-5678).
- The dollars-to-cents conversion; the daemon keeps dollars.

## Refs

- `internal/gateway/dashboard.go` (handleExecutionsUsage, executionUsageRow, DashboardStore), `internal/memory/store.go` (GetExecutionUsageSince, MaxExecutionUsageRows), `internal/gateway/executions_usage_test.go`, `internal/memory/execution_usage_test.go`, `internal/comms/chat_turn_handler.go` (reserveDailyTurn), `internal/gateway/prometheus.go`
- Branch `pilot/GH-5677` head 0bd7ae810 (PR #5682) — the source of the parts to re-apply
- Issue #5677 (superseded by this issue), #5676, #5678

- Pilot issue: https://github.com/qf-studio/pilot/issues/5690
