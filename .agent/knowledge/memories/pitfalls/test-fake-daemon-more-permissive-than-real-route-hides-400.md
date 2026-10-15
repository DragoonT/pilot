# Pitfall: A test fake that is more permissive than the real route hides a permanent 400

## Summary
console pollLedger omitted since on a zero cursor; the daemon route GET /api/v1/executions/usage requires since and answers 400 'since is required'. The fake daemon in TestPollLedger_FollowsHasMore served rows for an empty since, so the suite passed while prod failed every 15-min poll from 2026-10-14 14:xxZ (console-reconciler log: 'ledger: unexpected status 400'). Zero cursor + rejected request = permanent deadlock: no row ingests, the cursor never moves. Fixed by console#411 (TASK-558); predecessor TASK-554 fixed the body shape but not the request.

## Context
Verifying that ticket_ledger fills after v2.286.0 on 2026-10-15; the console-reconciler log showed the 400 every 15 min for the founder tenant org 425f9f99.

## Details
Rule: before writing a consumer's fake of a route owned by another repo, read that handler's http.Error / 4xx branches and mirror each one in the fake. The real contract is the handler's rejection branches, not the fixture's happy-path shape. Second rule: a cursor-driven poller must prove in a test that the very first request (empty state) is accepted by the real route; the empty state is what prod hits first and what fixtures skip.

## Recommended Approach
Mirror the producer's 4xx branches in the consumer's fake; add an explicit first-poll (zero cursor) test.

## Related
- TASK-558
- TASK-554
- `internal/fleet/usagepoller.go`
- `internal/fleet/ticket_ledger_test.go`
- `internal/gateway/dashboard.go`

---
**Captured**: 2026-10-15
**Confidence**: 95%
**Concepts**: false-success, test-fakes, wire-contract, usage-ledger, console
