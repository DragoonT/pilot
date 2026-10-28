## Post-merge review — REQUEST CHANGES (epic #240: PRs #250 / #251 / #252)

Scope vs #240 (epic; sub-issues #247 / #248 / #249):
✓ Four `StatCard`s in order Delivered / Review needed / Time to PR / Projects — `src/views/DashboardView.vue`; test asserts `[data-stat-label]` order and `[data-stat-value][0]` = `8/100`.
✗ `N/100` split: `/100` is muted (`#secondary` → `text-ds-num-muted`) but N is plain `text-ds-text`, not green `#8cd68c` (`text-ds-green`). The view does not use the `numerator` / `denominator` variant PR #251 built for exactly this. `/100` is a literal; `N` is `stats.shipped` for the selected 7–90-day window, not tickets this billing month.
✗ Review needed: whole card is a `RouterLink` to `/board?lane=needs-you` (test asserts the href) but there is no `Review` pill — the count sits alone in `text-needs-you`. The `pill` + `count` variant from #251 is unused; the outer `<RouterLink>` wrapper is used instead of StatCard's `to`.
✓ Time to PR: `~N` with muted ` m`; honest-degrade note (`DEGRADED_METRIC_NOTE`) kept when the field is absent.
✓ Projects count.
✗ Header `Last shipped X ago · Pool N%`: all three values bind to wire fields that do not exist (`orgName`, `lastShippedAt`, `poolPercentUsed`, `stats.timeToPrMinutes` on `GET /api/v1/dashboard`) — see D1. On both adapters the header renders `— · Last shipped —` with no Pool.
✓ No `$` / `tokens` in the header; test asserts on `[data-dashboard-header]` text.
✗ PR body: none of #250 / #251 / #252 pastes `make build` / `make test` / `make lint` output or names the adapter used in dev vs test (CI lint + test green on all three).
✗ Missing-field notes the spec asked for ("name the missing field in the PR body") are absent from all three bodies.
Tests: #250 — 1 new adapter test + fixture updates; #251 — 4 new `StatCard.spec.ts` tests (split, unit, pill+count, RouterLink); #252 — 4 new `DashboardView.spec.ts` tests (order + split, link target, header text, absent-field dashes) + 4 updated assertions.

Per-PR:
- #250 (api, #247): APPROVE with notes. `WireAllowance.percent_used` matches the console (`allowanceapi/routes.go` `PercentUsed int json:"percent_used"`); `Allowance.percentUsed` mapped in `toAllowance`, mock + fixtures updated in lockstep. The docblock says "percent of the dollar allowance" and the older-API fallback derives from USD only, but the console's `percent_used` is the pool meter = max(tickets %, USD %). Fix the comment; the fallback is rare and acceptable.
- #251 (design-system, #248): APPROVE with notes. Variants use tokens only (`text-ds-green`, `text-ds-num-muted`, `Pill`), docblock cites `design/dashboard-v4.html`, `to` renders a RouterLink. Dead code until #252 uses it (D2).
- #252 (view, #249): REQUEST CHANGES — D1, D2.

### D1 — Pool, org name and Last shipped are wired to fields that no backend sends
`httpAdapter.toDashboard` was extended with `orgName`, `lastShippedAt`, `poolPercentUsed`, `stats.timeToPrMinutes`; the console DTO (`dashboardapi/dto.go`) has only `window / stats{shipped, needsYou} / activity / projects`, and `mockAdapter.buildDashboard` returns none of them. Result: the header never shows Pool on any tenant, and the one method this epic added — `getAllowance().percentUsed` (#250) — is never called by the view. Three of the four values are already available without any wire change: org name from `useAuthStore().org.name`; Last shipped from the newest `projects[].cards[].doneAt` (the view already computes `latestShipped` for the mobile glance); Pool from `getAllowance().percentUsed`. Only median time-to-PR is genuinely missing on the console. Rewire, drop the four invented wire fields, and name the one real gap.

### D2 — View ignores the StatCard variants and the spec's visual contract
Delivered should be `<StatCard label="Delivered" :numerator="n" :denominator="d" />` (green N, muted /d); Review needed should be `<StatCard label="Review needed" pill="Review" :count="n" :to="…" />`; Time to PR should use `value` + `unit`. The denominator and N exist on the allowance: `included_tickets` and `usage.tickets` (tickets consumed this billing period) — that is the spec's "N/100 this billing month", not the window-scoped `stats.shipped` the view uses today (changing the window pill changes N while /100 stays).

### D3 — Mobile glance still renders per-ticket USD
`Cost / shipped` in the `md:hidden` block renders `formatCurrencyUsd(...)` for every tenant. The epic's Context: "Per-ticket cost never appears on a platform-key tenant". Pre-existing, but the header test covers the desktop header only. Gate the tile on `allowance.usage.keySource === 'own'`.

### Notes (no action)
- N1 Header uses `font-semibold`, `text-[13.5px]`, `text-ink` / `text-text-2` — U1 is Inter regular only, 12 / 13 / 15px, `ds-*` tokens. Align when D1 is fixed.
- N2 `BoardView.vue` does not read `?lane=`; the Needs You strip is always on top, so the link lands correctly. The query is inert today.
- N3 Stat row is `grid-cols-2 xl:grid-cols-4` — one row only at ≥1280px; design is 1440px, acceptable.
- N4 `StatCard` calls `resolveComponent('RouterLink')` at setup; outside a router (bare unit tests) Vue warns. Tests stub it. Fine.
- N5 Mobile tiles still say "Needs you" and "Median → PR" while desktop says "Review needed" / "Time to PR".

