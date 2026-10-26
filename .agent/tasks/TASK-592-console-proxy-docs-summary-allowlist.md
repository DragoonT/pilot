# TASK-592: Console proxy — allow the daemon's docs/summary read so the Context panel gets its numbers

**Status**: 🚀 Dispatched to Pilot 2026-10-26 → console#453 (`pilot`+`no-decompose`) → qf-studio/pilot-console, labels pilot + no-decompose.
**Spec refs**: positioning §8.1 Context panel; pilot#5857 (P18, merged as PR#5859) names this as the console follow-up.
**Origin**: post-merge review of ui PR#255 (U5): the Context panel renders dashes because no daemon read existed; the daemon read shipped 2026-10-26, the proxy does not forward it yet.

## Context

The console reaches a tenant daemon only through the proxy in pilot-console internal/proxy/proxy.go, which forwards GET /api/v1/instances/{id}/pilot/{tail} for a closed set of tails (allowedTails) and forwards the query string only for queryPassthroughTails. The daemon now serves GET /api/v1/docs/summary?project= (pilot PR#5859, GH-5857): docs (createdThisWeek, updatedThisWeek, readByPilotThisWeek null), memory (total, createdThisWeek, updatedThisWeek), graph (nodes, edges, updatedAt) or null. The tail docs/summary is not on the list, so the proxy answers 404 before any upstream call.

## Legs — pilot-console

### LEG X1 — repo: qf-studio/pilot-console — title: feat(proxy): allow docs/summary with query passthrough — relay the daemon's GET /api/v1/docs/summary for the Context panel

## Context
The daemon (pilot v2.294.x, GH-5857 / PR#5859) serves GET /api/v1/docs/summary?project= with a body of docs, memory and graph (graph null when the repo has no graph.json). The proxy in `internal/proxy/proxy.go` exposes a closed allowlist of daemon tails (allowedTails: status, metrics, queue, history, tasks, logs, docs/tree, docs/file) and forwards the query string only for queryPassthroughTails (logs, history, docs/tree, docs/file). docs/summary is on neither list, so the console's GET /api/v1/instances/{id}/pilot/docs/summary answers 404 without an upstream call and the Context panel (pilot-console-ui, Docs / Memory / Graph cards) keeps rendering dashes. The body carries no cost or token field, so the metrics-style USD stripping does not apply; this is a byte-faithful relay like docs/tree.

probe: present qf-studio/pilot-console "docs/file": true
probe: present qf-studio/pilot-console func TestAllowlistEnforcement
probe: absent  qf-studio/pilot-console docs/summary
probe: present qf-studio/pilot GET /api/v1/docs/summary

## Scope
- Add docs/summary to allowedTails and to queryPassthroughTails in `internal/proxy/proxy.go` (the daemon takes ?project=). Update the comment block that lists the Docs tails.
- No response rewriting: the body is relayed byte for byte, the daemon's status code is relayed as is (200, 404 for an unknown project, 401 for a bad token).
- Tests in `internal/proxy/proxy_test.go`: extend TestAllowlistEnforcement with docs/summary allowed; a relay test with a fake upstream that serves a fixture body copied from the daemon's docsSummaryResponse shape asserts the console body is byte-identical and that ?project= reaches the upstream verbatim; a traversal case docs/summary/.. still 404s without an upstream call.
- One line in the PR body quotes the daemon route registration line (pilot repo, internal/gateway/server.go, the docs/summary HandleFunc) as the producer evidence.

## Acceptance
- [ ] Remove docs/summary from allowedTails -> TestAllowlistEnforcement fails.
- [ ] `go test ./internal/proxy/` passes; paste the output into the PR body.
- [ ] `make build`, `make test`, `make lint`, `make check-fleet-org-scoping` pass — paste the output into the PR body.

## Out of scope
- The UI change that reads docs/summary into the Context panel cards (separate pilot-console-ui leg).
- Any cost or token stripping (the body has none).

## Refs

## Refs

- X1 → https://github.com/qf-studio/pilot-console/issues/453
- Pilot issue: https://github.com/qf-studio/pilot-console/issues/453

**Last Updated**: 2026-10-26
