## Post-merge review — APPROVE with defects

Scope vs #241:
✓ Panel card "Activity" (12px) left, `1D · 7D · 30D` (12px) right, bars 9.67px / 8px gap / 2px radius, height scaled to max bucket — `src/design-system/components/DashboardActivityChart.vue`, mounted in `src/views/DashboardView.vue` (`<DashboardActivityChart :events="boardActivity" />`, fed by `getAdapter().listBoardActivity()` on mount).
✓ Range switch changes bucket size (1D = 24 hourly, 7D = 7 daily, 30D = 30 daily); endpoint has no range param (confirmed: console `boardapi/handlers.go handleActivity` reads only `limit`), bucketed client-side, stated in PR body and docblock.
✓ Unit test: three range buttons, click changes bar count 7 → 24 → 30 (`DashboardActivityChart.spec.ts`).
✓ Highlighted / muted distinction: `bg-needs-you` vs `bg-ink/30`; test asserts 1 + 6 for the mixed fixture.
✓ Existing chart tests untouched and passing; `make build` / `make test` (951) / `make lint` output pasted. CI lint + test green.
Tests: 3 new (range buttons + bucket count, highlight/mute classes, max-bucket scaling).

### D1 — Dashboard now renders two activity charts
The spec said restyle `DashboardShippedChart.vue` or replace its use in `DashboardView.vue`. The PR did neither: the old "Shipped Activity" section (server calendar-day buckets, per-project series, window pill) still renders directly above the new panel. The docblock's reason ("still used by Settings → Usage") is true (`SettingsUsageView.vue`) but only argues for keeping the component, not for keeping it on the dashboard. Remove the old section from `DashboardView.vue` (or wrap the new panel into it) so the page has one activity chart.

### D2 — 7D / 30D ranges are silently truncated to the newest 50 events
`httpAdapter.listBoardActivity()` calls `/api/v1/board/activity` with no `limit`; the console defaults to 50 and caps at 200. On an active tenant 50 journal entries cover a day or two, so 7D and 30D bars beyond that render as zero with no hint. Interim: pass `?limit=200`. Proper fix: a `since` / `range` query param on the console endpoint, then re-request on range change as the spec intended.

### D3 — Buckets are rolling windows ending at `now`, not calendar hours / days
`start = now − buckets × bucketMs`; each bar is a window ending at the mount time in no timezone. The "daily" bars therefore disagree with the calendar-day `activity[].date` buckets of the chart above (D1) and with the user's notion of "today". There are no axis labels or dates in the tooltip (`title` = event count only), so the shift is invisible. Align bucket edges to local hour / local midnight and put the bucket date in the tooltip.

### Notes (no action)
- N1 Highlight colour: `dashboardShippedColors.ts` holds only neutral grey series (`--color-chart-1..3`), so the PR used the `needs-you` token (magenta) and said so. Token-based, no raw hex — fine, but the designer should confirm the accent.
- N2 Uses U1 tokens (`text-ds-label`, `rounded-ds-card`, `border-ds-edge`); muted bars use `ink` at 30% (reads as white/30% in dark). Good.
- N3 `make lint` in this repo is `vue-tsc --noEmit` only (no eslint). Repo-wide, not this PR.
- N4 `t >= end` drops events with a timestamp ahead of the client clock (skew). Negligible.

