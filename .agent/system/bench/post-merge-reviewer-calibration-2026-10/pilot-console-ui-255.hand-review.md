## Post-merge review — REQUEST CHANGES

Scope vs #243:
- ✓ Three cards render with the labels Docs / Memory / Graph, `Created this week`, `Updated this week`, `Read by Pilot this week`, `Nodes`, `Edges`, `Last updated`; a unit test asserts the labels and the `—` fallback (`src/design-system/components/ContextPanel.vue`, `src/design-system/components/__tests__/ContextPanel.spec.ts`). 270px column at `xl`, stacked below it (`src/views/DashboardView.vue`, grid `xl:grid-cols-[…_270px]`). No bare percentage (test: `not.toMatch(/\d+%/)`).
- ✗ PR body lists every field that fell back to `—` and the endpoint that would supply it: the body is the issue text plus make output. No "Needs API" section. 8 of 12 numbers render `—` (D1).
- ✓ `make build`, `make test`, `make lint` output pasted (954 tests). ✗ No one-line note on which adapter the view uses (mem-195).
Data path verified: `getDocsTree(instanceId)` → `GET /api/v1/instances/{id}/pilot/docs/tree` → console `internal/proxy/proxy.go` allowlist (`docs/tree`) → daemon `internal/gateway/docs.go handleDocsTree`. The response carries `entries[].modifiedAt` and `counts{patterns,pitfalls,learnings,decisions}`. Docs header = `entries.length` ✓; `Updated this week` = client-side count of `modifiedAt ≥ now−7d` ✓. No wire field for weekly deltas exists; the delta is computed from mtimes (N1). The Graph health label is `Healthy`/`Drift`/`Stale` from a `graph.updatedAt` prop with hard-coded 7d/30d thresholds; `DashboardView` never passes that prop (D3).
Tests: `ContextPanel.spec.ts` — labels + `—` fallback; docs count + updated-this-week; health word + tooltip title; 3. No test covers the mount in `DashboardView`. CI: lint + test green.

### D1 — "Needs API" list missing from the PR body
Acceptance line 2 asks for the list of every `—` field and its owing endpoint. The PR body has none. Consequence: the gap is invisible in the PR record and no daemon/console leg gets filed. The list, from the code: Docs `Created this week`, `Read by Pilot this week`; Memory header, `Created this week`, `Read by Pilot this week`; Graph header/health, `Nodes`, `Edges`, `Last updated`. The daemon docs read (`internal/gateway/docs.go`) has no created-at, no read counters, and excludes `graph.json` by contract (its line 39). Change: file the list as a daemon issue (follow-up below) and link it from `ContextPanel.vue`'s docblock.

### D2 — Memory card hides numbers the docs tree already serves
`memoryRows` is a constant of three `—` and the Memory header is `DASH`. The same `DocsTreeResponse` carries `counts` (server-authoritative memory count by kind; `types.ts` says "never client-recount") and `entries[]` with `type === 'knowledge'` and `modifiedAt`. Consequence: the one Memory number a tenant can get today (total memories) renders `—`; the spec says render `—` only when no existing endpoint has the number. Change: header = sum of `counts`; `Updated this week` = knowledge entries modified in the last 7 days; keep `Created` and `Read by Pilot` as `—`.

### D3 — Graph card is a dead prop on every tenant
`ContextPanel` accepts `graph?: { nodes, edges, updatedAt }`. `DashboardView.vue` passes only `:docs`. The health thresholds and the tooltip text are a hard-coded assumption (docblock: "assumed — no backend definition exists yet"). Consequence: the "labeled health value" never renders a label on any tenant; the unit test passes because it injects the prop. Change: record the three fields and the health rule in the Needs API issue; until a graph summary read exists, keep `—` and move the threshold constants next to a `// provisional, see pilot#N` comment so the rule lives in one place when the server defines it.

### D4 — Panel bypasses the U1 `ds-*` vocabulary
Cards use `rounded-2xl` (16px), `border-hairline`, `font-semibold` headers at 13.5px, `text-success` / `text-needs-you` / `text-error` / `text-muted` / `text-text-2`. The design facts for the Context column (TASK-583 Context) are radius 4px, border `#333` (`--color-ds-edge`), regular weight only, 13px rows, 16px padding, green `--color-ds-green`. No `ds-*` class appears in `ContextPanel.vue`. Consequence: the Context column renders in the pre-U1 theme next to a Queue that uses `ds-*`. Change: `rounded-ds-card`, `border-ds-edge`, `text-ds-text` (`/60` for row labels), `font-normal`, `p-[var(--ds-pad-panel)]`, `text-ds-green` for Healthy.

### Notes (no action)
- N1 `Updated this week` uses file mtime. A freshly provisioned instance clones the repo, so every file has the clone time as mtime and the number equals the total for the first week. The daemon summary read should use git dates.
- N2 `ContextPanel.vue` lives in `src/design-system/components/`; `DashboardQueue.vue` from the same wave lives in `src/components/dashboard/`. Pick one home for feature components.
- N3 The GH-243 paragraph in the `DashboardView.vue` docblock still says the column "sits right of the by-project list"; PR #261 removed that list.
- N4 `getDocsTree(id)` is called with no `limit`, so the Docs count is the full tree. If a `limit` is added later, the header must switch to a server count.

