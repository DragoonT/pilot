## Post-merge review — REQUEST CHANGES

Epic ui#242 (LEG U4) = ui#256 (PR #259) + ui#257 (PR #260, closed; its code merged inside PR #261) + ui#258 (PR #261).

Scope vs #242:
- ✗ Group cards from `GET /api/v1/board/cards` by project: `src/components/dashboard/queue.ts buildQueue` groups on `card.project`, a field PR #261 added to `WireBoardCard`/`BoardCard` (`src/lib/api/httpAdapter.ts`, `src/lib/api/types.ts`). The console `cardDTO` (`internal/boardapi/dto.go`) has no `project`. Every tenant gets one group named "Board" with avatar "B" (D1).
- ✗ Epic children at `depth=1` with the tree line: nesting keys on `card.parentId`. The console `cardDTO` has no `parentId`. No tenant ever sees a tree (D1).
- ✗ Meta `12 min · +184 −32` from `GET /api/v1/board/cards/{id}/execution`: PR #259's `WireCardExecution { durationMs, linesAdded, linesRemoved }` does not match the console. Its `executionDTO` is `{ linked, provider, sequenceId, nativeUrl, instanceId, instanceStatus }` (`internal/boardapi/dto.go`, `handleExecution` in `internal/boardapi/handlers.go`). `toCardExecution` nulls all three, `buildMeta` returns `''`, every row has empty meta (D2).
- ✓ Rows use `ListRow` (id at 60%, green when running; truncated title; right-aligned meta; chip) and `Chip` variants `neutral` / `pilot` / `done` (`src/components/dashboard/DashboardQueue.vue`). Group header: 24px initial circle, 15px name, `N shipped` at 40%.
- ✓ Group order: running first, then `updatedAt` recency. ✓ 3×3 cap with `+N more` → `/board` (`MAX_GROUPS`, `MAX_ROWS`; `more` = hidden rows in shown groups + all rows of hidden groups).
- ✓ Never tokens: no `token`, `$` or `cost` string in `queue.ts` / `DashboardQueue.vue`.
- ✓ "Queue" `SectionHeader` with "Show history" → `/board` under the activity panel (`src/views/DashboardView.vue`; no history view exists). ✓ `DashboardShippedByProject.vue` and its spec deleted (absent on `main`); `DashboardView.spec.ts` updated.
Acceptance:
- ✓ Unit tests cover grouping, child indentation, meta with and without diff fields, chip per status, the 3×3 cap with `+N more` (`src/components/dashboard/__tests__/DashboardQueue.spec.ts`, 5) + `httpAdapter.spec.ts` 1 + `mockAdapter.spec.ts` 1 + `DashboardView.spec.ts` 1 (GH-258). All mock the adapter; none can see that the wire fields do not exist.
- ✓ A test asserts no row text matches `/token|\$/i`.
- ✗ `make build`, `make test`, `make lint` output: neither PR #259 nor PR #261 body pastes it, and neither names the adapter (D3). CI lint + test green on both.
Per PR: PR #259 (ui#256) — adapter, mock and fixture move in lockstep, but `src/lib/api/__tests__/fixtures/README.md` admits `board-execution.json` is "hand-authored from the GH-256 spec until captured from the live BFF"; the issue's own "audit the endpoint" step was skipped. PR #261 (ui#257 + ui#258) — component, mount and deletion delivered; it adds `project` / `parentId` to the wire and domain types without touching `src/lib/api/mockAdapter.ts` (PR #260's mock hunk was dropped in the stack), so the mock also shows one "Board" group.

### D1 — Queue binds to `project` and `parentId`, which the console never sends
`WireBoardCard.project?: { key, name }` and `parentId?: string` were added in PR #261 with no console counterpart. `buildQueue` falls back to `NO_PROJECT = { key: '_none', name: 'Board' }`. Consequence: on every real tenant and in the mock, the Queue is one flat "Board" group with a "B" avatar; project groups and epic trees — the two headline behaviours of #242 — are unreachable. Tests pass because `card()` in the spec sets `project` on every card. Change: (a) console leg: `cardDTO` gains `project{key,name}` (same key/name as the dashboard aggregate's `projects[]`) and `parentId`; (b) until then the UI must not fabricate a "Board" group — render the flat list without avatar/header, and mark `project` / `parentId` in `httpAdapter.ts` as "not served yet, console#N".

### D2 — Execution meta binds to three fields the console never sends; N+1 fetch for nothing
`toCardExecution` reads `durationMs`, `linesAdded`, `linesRemoved` from a payload that carries `linked`, `provider`, `sequenceId`, `nativeUrl`, `instanceId`, `instanceStatus`. Every row renders an empty meta column. `DashboardQueue.onMounted` calls `getCardExecution` once per card over the full `listCards()` result (no cap) — a 200-card board makes 200 requests on dashboard load, each returning a join the UI discards. Daemon side: `durationMs` exists today on the `history` tail (`internal/gateway/dashboard.go historyEntryResponse`); lines added/removed are pilot#5790 (P1, OPEN). Change: console leg extends `executionDTO` (duration now, diff stats after P1); UI removes the per-card fetch until those fields ship and keeps `buildMeta` and its tests.

### D3 — No build/test/lint evidence and no adapter note on either PR
Acceptance line 3 of #242 (mem-195) is not delivered by PR #259 or PR #261. The bodies are the sub-issue text only. Change: the follow-up PRs paste the three outputs and state the adapter the view uses.

### Notes (no action)
- N1 `chipFor(card, exec)` ignores `exec`; `queued` and `in_review` both map to `CI`. Matches the spec, but "CI" on a queued card is a design question for D-legs.
- N2 The running id uses `text-success` (pre-U1 token); the design accent is `--color-ds-green` → `text-ds-green`.
- N3 `N shipped` counts `done` cards in `listCards()` — all-time, not the dashboard window. The removed tile said "N shipped in 30d". Label the window or accept all-time.
- N4 Stale references: the `DashboardView.vue` docblock still cites `DashboardShippedByProject` in `latestShipped`, `filteredActivity` and the GH-243 paragraph. `design/dashboard-v4-spec.md` and `design/dashboard-v4.html` still describe the by-project list; `DashboardQueue.vue` cites them as its source.
- N5 `DashboardQueue` has no loading, error or empty state. A rejected `listCards()` is an unhandled rejection inside `onMounted` and the section renders nothing.
- N6 The token/`$` invariant test runs on synthetic titles. The mock card "Ship StatusDot needs-you token" (asserted by `DashboardView.spec.ts`) shows the rule targets metrics, not titles. Name the test accordingly.

