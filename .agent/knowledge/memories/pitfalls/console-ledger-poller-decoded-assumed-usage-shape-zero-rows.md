# Pitfall: Console ledger poller and daemon usage route were built to two different wire shapes — zero rows ingested silently (doc-vs-wire, 6th incident)

## Summary
console PR#405 (GH-401) decoded {rows|array} with kind, estimatedUsdCents, reportedUsd, status=succeeded; daemon GH-5676 served {executions,nextSince,hasMore} with estimatedCostUSD, reportedCostUSD, status=completed, no kind. Both merged the same morning from one plan (TASK-546) that never fixed the shape; fixtures on each side were written to their own assumption. Result: ticket_ledger stayed empty with no error above debug; the meter fell back to the rollup delta so enforcement ran but chat dollars (D10) could never land. Fixed: console#409→PR#410 (decoder to the shipped shape + hasMore paging + verbatim daemon fixture) and pilot#5690→PR#5693 (kind + chat rows on the existing route). PR#5682 had tried to add a second handler on the same route and could not rebase.

## Context
navigator-research run while re-specifying pilot#5677 (2026-10-14), verified in both repos.

## Details
console PR#405 (GH-401) decoded {rows|array} with kind, estimatedUsdCents, reportedUsd, status=succeeded; daemon GH-5676 served {executions,nextSince,hasMore} with estimatedCostUSD, reportedCostUSD, status=completed, no kind. Both merged the same morning from one plan (TASK-546) that never fixed the shape; fixtures on each side were written to their own assumption. Result: ticket_ledger stayed empty with no error above debug; the meter fell back to the rollup delta so enforcement ran but chat dollars (D10) could never land. Fixed: console#409→PR#410 (decoder to the shipped shape + hasMore paging + verbatim daemon fixture) and pilot#5690→PR#5693 (kind + chat rows on the existing route). PR#5682 had tried to add a second handler on the same route and could not rebase.

## Recommended Approach
When one plan spans producer and consumer repos, fix the wire shape in the plan with one fixture copied verbatim from the producer's endpoint test into the consumer's testdata; a consumer that decodes to zero rows from a non-empty body must warn. The shipped producer shape is the truth (TASK-460 rule).

## Related
- TASK-546
- TASK-553
- TASK-554
- TASK-460
- `internal/gateway/dashboard.go`
- `internal/memory/store.go`

---
**Captured**: 2026-10-15
**Confidence**: 90%
**Concepts**: pricing-v3, usage-ledger, contract-drift, doc-vs-wire, console
