# TASK-592: Console proxy — allow the daemon's docs/summary read so the Context panel gets its numbers

**Status**: ✅ DONE 2026-10-27 — X1 merged (console#453 → PR#454, 10-26) · X2 merged (ui#283 → PR#286, 12:04Z, after a manual rebase in a side session: one conflict in httpAdapter.ts imports, both sides kept; head 798897f). Post-merge review of ui PR#286 not posted. Archived.
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

## Legs — pilot-console-ui — dispatched 10-26 → ui#283

### LEG X2 — repo: qf-studio/pilot-console-ui — title: feat(context): Context panel reads the daemon docs/summary — created and updated this week, memory totals, graph nodes, edges and last updated

## Context
Blocked by pilot-console X1 (console#453, see TASK-592 Refs): the proxy forwards GET /api/v1/instances/{id}/pilot/docs/summary?project= to the daemon. The daemon body (pilot PR#5859, GH-5857) is exactly: docs with createdThisWeek, updatedThisWeek, readByPilotThisWeek (each an integer or null; readByPilotThisWeek is always null today); memory with total (integer), createdThisWeek, updatedThisWeek, readByPilotThisWeek (integer or null); graph with nodes (integer), edges (integer), updatedAt (RFC 3339 string or null), or graph itself null when the project has no graph.json. No health word on the wire: health is a UI word computed from updatedAt. Today `src/design-system/components/ContextPanel.vue` takes docs (the docs tree) and an optional graph prop that `src/views/DashboardView.vue` never passes, so Created this week, Read by Pilot this week and the whole Graph card render a dash. The adapter (`src/lib/api/httpAdapter.ts`, `src/lib/api/types.ts`, `src/lib/api/mockAdapter.ts`) has getDocsTree and no summary read.

probe: present qf-studio/pilot-console "docs/summary": true
probe: present qf-studio/pilot-console-ui interface WireDocsTreeResponse
probe: present qf-studio/pilot-console-ui data-context-health
probe: absent  qf-studio/pilot-console-ui docs/summary

## Scope
- Adapter: a WireDocsSummary type that mirrors the daemon body field for field as listed in Context (nullable leaves, graph nullable) and a getDocsSummary(instanceId) method on GET /api/v1/instances/{id}/pilot/docs/summary with the same project query the docs tree call uses. A 404 or 5xx from the proxy resolves to null (the proxy may predate X1 on a tenant), never throws into the view. The mock adapter returns one summary with all leaves set and one with graph null.
- ContextPanel: a new optional summary prop. Docs card: Created this week and Read by Pilot this week come from summary.docs; Updated this week prefers summary.docs.updatedThisWeek and falls back to the docs-tree computation when summary is null. Memory card: the header total prefers summary.memory.total; Created, Updated and Read rows come from summary.memory. Graph card: Nodes, Edges and Last updated from summary.graph; the health word from updatedAt by the existing HEALTH_RULE; the card shows the dash rows when summary.graph is null. A null leaf renders the dash; the component never invents a number.
- DashboardView: fetch the summary next to the docs tree for the same instance and pass it to ContextPanel; a null summary keeps today's rendering.
- No token or USD string anywhere; no new wire field beyond the daemon's.
- One line in the PR body names the adapter the view uses in dev and in the test (httpAdapter vs mockAdapter).

## Acceptance
- [ ] A wire-contract test decodes a fixture that is the exact JSON of GET /api/v1/docs/summary as the pilot repo's internal/gateway/docs.go emits (all leaves set) into WireDocsSummary and asserts every field; a second case with every nullable leaf null and graph null decodes to nulls. Rename the fixture key updatedAt to lastUpdated -> docsSummaryWireContract fails.
- [ ] ContextPanel tests: with a full summary, Created this week, Read by Pilot this week, Memory total, Nodes, Edges and Last updated render the fixture numbers and the health word is set; with summary null, the panel renders exactly what it renders today (snapshot or per-row assertions); with graph null the Graph card shows dashes.
- [ ] Adapter test: getDocsSummary GETs the summary route and maps a 404 to null.
- [ ] A test asserts the absence of the dollar sign and the word tokens in the rendered panel.
- [ ] `npm run build`, `npm test`, `npm run lint` pass — paste the output into the PR body.

## Out of scope
- A read counter for Read by Pilot this week (null until the daemon has a source).
- Changes to the docs tree read.

## Refs

## Refs

- X1 → https://github.com/qf-studio/pilot-console/issues/453
- X2 → https://github.com/qf-studio/pilot-console-ui/issues/283
- Pilot issue: https://github.com/qf-studio/pilot-console/issues/453

**Last Updated**: 2026-10-26
