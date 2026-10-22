# TASK-583: Wave 1 — design update + proof surface (Run Story, Review needed, briefs, pen test)

**Status**: 🚧 10-22 pm (16:00Z) — MERGED: U1 (PR#245) · U2 (epic ui#247–249, PR#250–252) · U3 (PR#254) · U4 (epic ui#256–258 via stacked PR#261; PR#260 leftover) · U5 (PR#255) · U9 (PR#246) · C3 (PR#426, D1 → pilot#5797) · C7 (PR#427) · C8 (PR#425, D1 → TASK-589) · P9 (PR#5799, v2.293.0) · P11 (PR#5795 REQUEST-CHANGES → #5798, gate open). REVIEWED 16:00Z: C7 APPROVE-w-notes → console#431/#432, ui#263 · U3 APPROVE-w-defects → ui#264, console#430 · U9 APPROVE-w-defects → ui#265, pilot#5810 (P17, design), ui#266 (decision) · **U2 REQUEST-CHANGES → ui#262** (header bound to invented dashboard fields; StatCard variants unused). Reviews still owed: U4 (PR#259/#261), U5 (PR#255), P9 (PR#5799). IN FLIGHT: P1 #5790, P10 #5792. Was: 🚀 DISPATCHING 2026-10-22 — first batch filed: U1 + U2–U5, U9 (blocked by U1) on `pilot-console-ui`; P1, P9, P10 (blocked by P9), P11 on `pilot`; C3, C7, C8 on `pilot-console`. Held until upstream merges (cross-repo deps are not machine-readable): U6/U7 (after C1), U8 (after C3), U11/U12 (after C6), C1/C2 (after P1), C6 (after P9 + I3). Design legs D1–D5, D7 and infra I2/I3 are founder / Nelya items. Roadmap: `.agent/system/project/project_pilot_cloud_roadmap_tickets.md`; decisions: `.agent/system/project/project_pilot_cloud_positioning.md` §6, §8.1, §8.2, §8.7, §8.8, §4.

**P11 hard gate (10-22 review):** PR#5795 merged with a report of 8 PASS, but every executor run had failed in ~2 s (`exit status 1`) and the harness only errors on a nil result → false-success. Fix filed as #5798; the gate stays open until a real run with agent turns is archived.
**Created**: 2026-10-22
**Assignee**: Pilot (U/C/P legs) · founder (D1–D5, D7 in Figma; F4) · Nelya (I2, I3)

---

## Context

Wave 1 makes the console look like the 2026-10-21 Figma design and puts the proof unit (the Run Story) and the human's one job (Review needed) on screen. The pen-test harness (P11) runs in parallel on the daemon track because it is a hard gate before the first private-repo tenant.

Design facts extracted from Figma `BfAqtVPBp0i4iWHg2jzAnB` node `7-2` (2026-10-22), for the UI legs:
- Font Inter, regular weight only. Sizes: 11px chips (uppercase), 12px card labels, 13px context-panel rows, 15px list rows, 24px card values.
- Text: white; secondary text = white at 60% opacity; tertiary = white at 40%. Muted numerals `#767576` / `#999899`; bright value `#eee`.
- Accents: green `#8cd68c` (delivered count, active ticket id), blue `#72c5e4` (PILOT chip border + text). Status chip "CI": border `#333`, text white 60%. Status chip "PILOT" (done): border white.
- Cards: 1px border `#333`, radius 4px, padding 12px (stat cards) / 16px (context cards), gap 12px between stat cards.
- Chips: height 21px, padding 8px, radius 4px, 11px uppercase. The "Review" pill: height 24px, radius 100px, border `#e2e2e2`.
- Layout at 1440px: left rail 24–64px (40px avatar, 24px icons); main column x=184, width 707; context column x=986, width 270; right rail at x=1376. Page padding 24px.
- Canvas is near-black; the exact fill is not in the extracted nodes — the UI leg keeps the current theme canvas unless the designer supplies the hex (design leg D1).

## Known pitfalls (from memory)

- mem-195 (prod UI shipped the mock adapter): every UI leg's acceptance includes `make build`, `make test`, `make lint` output and a one-line note on which adapter the view uses.
- SOP Rule 3: dependencies are `Blocked by: #N` numeric refs, same repo only.
- SOP Rule 3b: backticked paths must exist on `main`; new files are named in plain text.
- mem-203: Pilot copies issue claims verbatim — no unverified facts in bodies.

## Legs — pilot-console-ui

### LEG U1 — repo: qf-studio/pilot-console-ui — title: feat(design): tokens and primitives from the 2026-10 Figma — type scale, colors, card, chip, pill, section header, list row

## Context
The console gets a new visual design (Figma file `BfAqtVPBp0i4iWHg2jzAnB`, node `7-2`, 2026-10-21). This leg lands the foundation only: tokens and reusable primitives. Views are restyled in follow-up issues that depend on this one.

Design facts (extracted from Figma; use these values):
- Font: Inter, regular weight only. Type scale: 11px uppercase (chips), 12px (card labels), 13px (context rows), 15px (list rows), 24px (card values). Line-height 1.
- Text colors: primary white; secondary white at 60% opacity; tertiary white at 40%; muted numerals `#767576` and `#999899`; bright value `#eee`.
- Accents: green `#8cd68c`; blue `#72c5e4`. Border `#333`. Pill border `#e2e2e2`.
- Card: 1px border `#333`, radius 4px, padding 12px (compact) or 16px (panel). Stat-card row: 4 equal cards, 12px gap, label top-left 12px, value bottom-right 24px.
- Chip: height 21px, padding 8px, radius 4px, 11px uppercase; variants `neutral` (border `#333`, text white 60%), `pilot` (border + text `#72c5e4`), `done` (border + text white). Pill: height 24px, radius 100px, border `#e2e2e2`, 11px uppercase.
- Section header: 15px title left, 15px secondary action right (e.g. "Show history"), 40px tall.
- List row: 15px, columns id (64px) · title (flexible, truncated) · meta right-aligned (156px) · chip (right); 26px row pitch; child rows indented 21px with a 1px tree line.

## Scope
- Add the tokens to `src/design-system/theme.css` as CSS custom properties (font, sizes, text opacities, accent colors, border, radii, spacing). Keep the existing light/dark theme switch working; the new tokens apply to the dark theme and get sensible light equivalents.
- Add primitives under `src/design-system/components` (new files, plain names): StatCard.vue (label + value slot, optional secondary value span in muted color), Chip.vue (variants neutral/pilot/done), Pill.vue, SectionHeader.vue, ListRow.vue (id/title/meta/chip slots, `depth` prop for tree indent).
- Restyle `src/design-system/components/DashboardStatCard.vue` to use StatCard.vue (or make it a thin wrapper) so existing dashboard tests still pass.
- Add one story-like test page is NOT required; unit tests per primitive are.

## Acceptance
- [ ] Tokens exist in `src/design-system/theme.css` with the values above; a test reads the computed style of a mounted StatCard and asserts border color `#333` and radius 4px.
- [ ] Each new primitive has a unit test under src/design-system/__tests__ (plain name; the directory exists) covering its variants and slots.
- [ ] Existing tests for `DashboardStatCard.vue` pass unchanged.
- [ ] `make build`, `make test`, `make lint` pass — paste the output into the PR body.

## Out of scope
Restyling any view (follow-up issues).

### LEG U2 — repo: qf-studio/pilot-console-ui — title: feat(dashboard): stat cards (Delivered N/100, Review needed, Time to PR, Projects) and header "Last shipped X ago" with a pool meter

## Context
The dashboard header and stat row follow the 2026-10 design. Per-ticket cost never appears on a platform-key tenant; a pool meter (percent of the fair-use allowance) is the only usage number. The "Blocked" card is renamed "Review needed" and opens the review list.

Blocked by: #{{U1}}

## Scope
- In `src/views/DashboardView.vue`, replace the current stat tiles with four StatCard primitives in one row, left to right:
  1. **Delivered** — value `N/100` where N is tickets delivered this billing month (green `#8cd68c` for N, muted `#767576` for `/100`). Source: the existing dashboard payload from `GET /api/v1/dashboard` (use the field that counts delivered/shipped cards this period; if no such field exists, show `—` and name the missing field in the PR body).
  2. **Review needed** — a `Review` pill on the left and the count on the right; the whole card is a link to `/board?lane=needs-you` (the existing Needs You lane route; keep whatever route the board uses today).
  3. **Time to PR** — median minutes, rendered as `~6 m` with the unit in muted color. Source: existing dashboard payload field for median time-to-PR if present; else `—` and note it.
  4. **Projects** — count of connected projects.
- Header line (top of the main column): org name on the left; on the right `Last shipped 12 min ago · Pool 62%` where "Last shipped" is the relative time of the most recent delivered card and "Pool" is `percent_used` from `GET /api/v1/billing/allowance` (if the field is absent, show only "Last shipped" and note it in the PR body). Never render tokens or USD here.
- Keep the existing "honest degrade" behaviour when the instance is not running.

## Acceptance
- [ ] The four cards render in order with the labels above; a unit test asserts labels and the `N/100` split spans.
- [ ] The Review needed card navigates to the Needs You lane; a test asserts the link target.
- [ ] No token or USD string is rendered in the header or cards on a platform-key tenant; a test asserts the absence of `$` and `tokens` in the header text.
- [ ] One line in the PR body names the adapter the view uses in dev and in the test (`src/lib/api/httpAdapter.ts` vs `src/lib/api/mockAdapter.ts`).
- [ ] `make build`, `make test`, `make lint` pass — paste the output into the PR body.

### LEG U3 — repo: qf-studio/pilot-console-ui — title: feat(dashboard): activity bar chart with 1D / 7D / 30D range switch in the new design

## Context
The dashboard shows an activity bar chart (one bar per bucket; shipped tickets highlighted). The 2026-10 design places it under the stat row in a bordered panel with a range switch on the right.

Blocked by: #{{U1}}

## Scope
- Restyle `src/design-system/components/DashboardShippedChart.vue` (or replace its use in `src/views/DashboardView.vue`) as a panel card: header row "Activity" (12px) left, range switch `1D · 7D · 30D` (12px) right; bars 9.67px wide, 8px gap, radius 2px, height scaled to the max bucket; highlighted bars in the warm accent used today in `src/design-system/components/dashboardShippedColors.ts`, others white at 30% opacity.
- Range switch changes the bucket size (1D = hourly, 7D = daily, 30D = daily) and re-requests `GET /api/v1/board/activity` with the range the endpoint supports; if the endpoint has no range parameter, bucket client-side from the returned events and say so in the PR body.
- Keep existing chart tests passing or update them for the new structure.

## Acceptance
- [ ] A unit test asserts three range buttons and that clicking one changes the bucket count.
- [ ] Bars render with the highlighted/muted distinction; a test asserts both classes appear for a fixture with mixed events.
- [ ] `make build`, `make test`, `make lint` pass — paste the output into the PR body.

### LEG U4 — repo: qf-studio/pilot-console-ui — title: feat(queue): queue grouped by project with epic trees; rows show duration and diff size, never tokens

## Context
The dashboard queue lists work grouped by project (avatar initial + project name + "N shipped" on the right), each group showing epics as parent rows with child rows indented under a tree line. Row meta shows duration and diff size. Tokens and cost never appear.

Blocked by: #{{U1}}

## Scope
- Add a "Queue" section under the activity panel in `src/views/DashboardView.vue` with a SectionHeader ("Queue" left, "Show history" right linking to the board history view that exists today, or `/board` if none).
- Group cards from `GET /api/v1/board/cards` by project; render each group header as: 24px circle with the project's first letter, project name (15px), and `N shipped` (15px, 40% opacity) right-aligned.
- Rows use the ListRow primitive: id (`GH-5521`, 60% opacity; green when the row is the active/running one), title (truncated), meta right-aligned (`12 min · +184 −32` built from execution duration and lines added/removed from the card's execution payload at `GET /api/v1/board/cards/{id}/execution`; omit a part when the field is absent), chip right (`CI` neutral / `PILOT` blue while running / `DONE` white when delivered).
- Epic children render under the parent with `depth=1` and the tree line.
- Group order: projects with running work first, then by most recent activity. Show at most 3 groups and 3 rows per group, with a `+N more` link to the board.
- Never render `tokens`, `K tokens` or `$` in rows; the existing `DashboardShippedByProject.vue` tile is replaced by this section.

## Acceptance
- [ ] Unit tests cover: grouping by project, epic child indentation, meta string building with and without diff fields, chip selection per status, the 3×3 cap with `+N more`.
- [ ] A test asserts that no row text contains `token` or `$`.
- [ ] `make build`, `make test`, `make lint` pass — paste the output into the PR body.

### LEG U5 — repo: qf-studio/pilot-console-ui — title: feat(context): Context panel with Docs / Memory / Graph growth numbers and a labeled health value

## Context
The right column shows what Pilot knows about the tenant's repos: Navigator docs, memories and the knowledge graph. The 2026-10 design shows three panel cards. The buyer cares about growth, not read counts, and every number needs a label.

Blocked by: #{{U1}}

## Scope
- Add a right column (270px at ≥1280px; stacked under the main column below that) to `src/views/DashboardView.vue` with a header "Context" and three panel cards (16px padding, 13px rows):
  - **Docs** — header value: total docs size or count; rows: `Created this week`, `Updated this week`, `Read by Pilot this week`, each `count` left of a muted secondary number where available.
  - **Memory** — header value: total memories; same three rows.
  - **Graph** — header value: a health word (`Healthy` green / `Drift` / `Stale`) with a tooltip that explains the rule; rows: `Nodes`, `Edges`, `Last updated` (relative time).
- Data source: the existing docs/graph endpoints the Docs page uses (see `src/views/DocsView.vue` and `src/lib/api/types.ts`). Where a number is not available from any existing endpoint, render `—` and list the missing fields in the PR body under "Needs API" — do not invent values and do not hardcode.
- Replace the unlabeled percentage in the design with the health word; no bare `98%`.

## Acceptance
- [ ] The three cards render with the labels above; a unit test asserts the labels and the `—` fallback.
- [ ] The PR body lists every field that fell back to `—` and which endpoint would need to supply it.
- [ ] `make build`, `make test`, `make lint` pass — paste the output into the PR body.

### LEG U9 — repo: qf-studio/pilot-console-ui — title: feat(research): Research page — sub-agent tree with DONE badges, report body, Context-per-run panel; board input submits here

## Context
The chat view becomes the Research page (Figma node `13-994`). A research turn shows the sub-agents it ran as a tree with DONE badges and meta, then the report. The right column shows what this run read and created. The dashboard's "Ask your pilot…" input submits to this page. Tokens never appear on rows.

Blocked by: #{{U1}}

## Scope
- Restyle `src/views/ChatView.vue` (route stays as today) to the design: page title "Research" (15px) with the question under it (15px, 60%); a "Navigator research" tree header with the sub-agent count right-aligned; one ListRow per sub-agent (id, DONE chip, title, meta `12 m` duration only); then the report rendered as markdown.
- Input at the bottom: placeholder `Ask your pilot…`, two mode pills `RESEARCH` and `DOCS` (existing chat modes; keep their current semantics), send on Enter.
- Dashboard: add the same input (placeholder + pills) at the bottom of the main column in `src/views/DashboardView.vue`; submitting navigates to the Research page with the question and mode as query params, and the Research page starts the turn from them.
- Right column "Context" for the current run: `Read N docs · M memories`, `Created K memories`, each from the conversation events at `GET /api/v1/chat/conversations/{id}/events` if those events carry such counts; otherwise `—` and list the missing event fields in the PR body. Remove any judge name or version from the panel.
- Do not add the `Create tickets` action yet (separate issue).

## Acceptance
- [ ] Unit tests: sub-agent rows render from a fixture event stream with DONE chips and duration-only meta; the report renders markdown; the dashboard input navigates with the question in the query.
- [ ] A test asserts no `token` or `$` string in the sub-agent rows.
- [ ] `make build`, `make test`, `make lint` pass — paste the output into the PR body; one line names the adapter used.

## Legs — pilot (daemon)

### LEG P1 — repo: qf-studio/pilot — title: feat(gateway): run-story fields on the execution read — diff stats, tests, evidence-gate result, issue→PR and PR→merge timings

## Context
Pilot Cloud shows a "Run Story" per ticket: what was asked, what changed, what was verified, how long it took, the outcome. The console reads executions through the gateway JSON API. This leg makes every field the card needs available in one read, computed from data the daemon already stores; nothing is invented.

## Scope
- Add a `run_story` object to the gateway's execution read responses (the handlers in `internal/gateway` that serve `/api/v1/executions/{id}` and the task-scoped variant) with these fields, each nullable:
  - `asked`: task title, issue URL.
  - `changed`: PR URL, `files_changed`, `lines_added`, `lines_removed` (from the executions row), and a one-line summary = the first line of the PR body when the daemon has it.
  - `verified`: quality-gate results for the run (names + pass/fail) from the stored execution events, acceptance-evidence outcome (`verified` / `not_verified` / `skipped`) when the acceptance-evidence feature produced one, CI status when the autopilot state for the PR has it.
  - `timings`: `queued_at`, `started_at`, `pr_opened_at`, `merged_at`, `duration_ms`. `pr_opened_at` and `merged_at` come from the autopilot PR state where recorded.
  - `outcome`: one of `running`, `review_needed`, `merged`, `failed`; `failure_class` (`ci` / `env` / `scope` / `unknown`) when failed, derived from the execution's error classification if one exists.
  - `model_name`.
- Document in a short doc comment on the response type where each field comes from; where no stored source exists today, the field is null and the PR body says so under "Not available yet".
- No cost or token fields in `run_story` (they stay where they are on the execution row).

## Acceptance
- [ ] Table-driven tests in `internal/gateway` cover: a merged execution with all sources present, a running execution (nulls), a failed execution with a failure class.
- [ ] The PR body lists every `run_story` field with its source table/column or "Not available yet".
- [ ] `make test` and `make lint` pass — paste the output into the PR body.

### LEG P9 — repo: qf-studio/pilot — title: feat(briefs): one brief object with console and email payloads; receipts digest folds in; cost lines only on own-key

## Context
The daily brief is generated in `internal/briefs` and delivered to Slack/Telegram; the receipts digest is a separate Telegram-only message. Pilot Cloud needs one brief object that the console can store and show, and an email rendering. On a platform-key tenant, per-run cost never appears.

## Scope
- In `internal/briefs`, define a single structured brief (extend `types.go`) with sections in this order: `shipped` (one entry per delivered run: issue ref, title, PR URL, duration, `+a −b`), `review_needed` (items older than 24h first; each with a one-line reason), `pool` (percent of allowance used, when the daemon knows it), `failed` (issue ref, failure class, retryable flag).
- Fold the receipts digest into the `shipped` section: the per-run cost line is included only when the execution's `key_source` is the tenant's own key; on `platform` it is omitted.
- Add a JSON payload for the console (serializable struct, versioned `schema: 1`) and an email rendering in `internal/briefs/formatter_email.go` with the same four sections; keep Slack/Telegram formatters working.
- Expose the latest brief through the gateway (`internal/gateway`, new route in plain text: GET /api/v1/briefs/latest and GET /api/v1/briefs?limit=N) with the same bearer auth as sibling routes.
- Do not change the schedulers' times in this leg.

## Acceptance
- [ ] Table-driven tests: section ordering; 24h-first ordering in review_needed; cost line present for own-key and absent for platform-key; JSON payload round-trips; email formatter output contains the four section headings.
- [ ] Gateway tests for the two routes (auth, empty, limit).
- [ ] `make test` and `make lint` pass — paste the output into the PR body.

### LEG P10 — repo: qf-studio/pilot — title: feat(briefs): weekly brief on Monday with proof numbers — tickets shipped, median time to PR, merged count

## Context
The weekly brief exists as a manual trigger. Pilot Cloud sends it every Monday with three proof numbers for the previous 7 days.

Blocked by: #{{P9}}

## Scope
- Schedule the weekly brief for Monday at the daily-brief hour in the tenant's configured timezone (reuse the daily scheduler's config shape; add `weekly_day` with default `monday`).
- Content: `tickets_shipped`, `median_time_to_pr_minutes`, `merged_count` for the last 7 days, computed from the executions ledger and the autopilot PR state; plus the top 3 shipped runs by diff size.
- Use the brief object from the previous leg; the console and email payloads include a `kind: weekly` marker.

## Acceptance
- [ ] Tests: the scheduler fires on Monday only; the three numbers are computed correctly from a fixture ledger (including an empty week → zeros, not an error).
- [ ] `make test` and `make lint` pass — paste the output into the PR body.

### LEG P11 — repo: qf-studio/pilot — title: test(security): hostile-ticket pen-test harness — fixture repo, injected issue bodies, assertions on env, disk, SSM, egress and cross-tenant reach

## Context
Before any customer with a private repo runs on Pilot Cloud, a prompt-injected ticket must be shown not to reach beyond the tenant's own blast radius. This leg builds a repeatable harness; running it on the fleet canary is a separate operations step.

## Scope
- Add a harness under a new directory (plain name: tests/pentest) with:
  - A fixture repository generator (a small Go module with a README and one test) that the harness commits to a temp dir.
  - A set of hostile issue bodies (plain-text files) that try, one per file: read environment variables and write them into the PR body; read files outside the worktree (home directory, `/etc`, the Pilot data directory); call the instance metadata endpoint and SSM; make outbound HTTP to a host not on the expected allowlist; read another path that would belong to a different tenant.
  - A runner that executes each body through the real executor path with the Claude Code backend in the same way `pilot start` does (reuse the existing executor entry points; no mock executor), captures the resulting PR body / diff / process egress log, and asserts: no environment value appears in any output; no file content from outside the worktree appears; no request reached the disallowed host; the destructive-command hook blocked the attempts it covers.
  - A report (markdown) written to the harness output directory: one row per hostile body with pass/fail and the evidence line.
- Add `make pentest` that runs the harness against a configured backend; skipped in CI by default (requires a real key and network).
- Document how to run it on the fleet canary in a short section of `docs/` (the Nextra docs under docs/content; add a page in plain text: docs/content/guides/pen-test.mdx).

## Acceptance
- [ ] The harness runs locally end to end with `make pentest` and writes the report; paste the report table into the PR body (redact nothing — if a secret appears in the output, the harness has found a real defect, and the PR must say so).
- [ ] Unit tests cover the assertion functions with synthetic outputs (positive and negative cases).
- [ ] `make test` and `make lint` pass — paste the output into the PR body.

## Legs — pilot-console (API)

### LEG C3 — repo: qf-studio/pilot-console — title: feat(review): unified Review needed list — approvals and decisions with a why-line; every action records the actor

## Context
The console shows a Needs You lane fed by approval mirroring. Pilot Cloud's "Review needed" list unifies everything that waits on a human: PRs that need approval, decisions Pilot cannot make, and (in a later leg) ticket drafts. Each item carries one line that says why it needs a human, and every action records who did it.

## Scope
- Add `GET /api/v1/review` returning one list, oldest first, grouped by project, of items `{ id, type, project, title, why, created_at, card_id, actions }` where `type` is `pr_approval` or `decision` for now (a `draft` type is reserved for a later leg), and `why` is a one-line reason derived from the source (e.g. "prod mode: merge needs approval", "destructive action: migration drops a column").
- Record `actor_id` (the authenticated user) on every decision taken through `POST /api/v1/board/cards/{id}/decision`, and return `decided_by` in subsequent reads.
- Add a `send_back` action to the decision endpoint: it posts the comment to the card (reusing the comment path) and marks the item as sent back without approving or rejecting.
- Org-scoped like sibling routes; covered by the existing fleet-org-scoping check (`make check-fleet-org-scoping`).

## Acceptance
- [ ] Tests: list ordering and grouping; `why` lines for both types; actor recorded and returned; `send_back` neither approves nor rejects and posts the comment.
- [ ] `make build`, `make test`, `make lint`, `make check-fleet-org-scoping` pass — paste the output into the PR body.

### LEG C7 — repo: qf-studio/pilot-console — title: feat(metering): pool meter — percent of the fair-use allowance; USD hidden when the tenant runs on the platform key

## Context
Pilot Cloud never shows per-ticket cost to a platform-key tenant. The one usage number is the pool meter: percent of the monthly fair-use allowance used. The allowance endpoint exists.

## Scope
- Extend `GET /api/v1/billing/allowance` with `percent_used` (integer 0–100, capped at 100) and `key_source` (`platform` or `own`).
- When `key_source` is `platform`, omit every USD field from this response and from `GET /api/v1/usage` and `GET /api/v1/usage/ledger` (keep counts, durations, ticket numbers). When `own`, keep USD fields as today.
- Add the same `key_source` gate to the dashboard payload (`GET /api/v1/dashboard`) if it carries cost fields.

## Acceptance
- [ ] Tests: percent computation at 0, mid, over-cap; USD fields absent for `platform` and present for `own` on all three endpoints.
- [ ] `make build`, `make test`, `make lint` pass — paste the output into the PR body.

### LEG C8 — repo: qf-studio/pilot-console — title: feat(billing): $300 fair-use ceiling; prepaid ticket packs (25 for $99, 100 for $349, 90-day expiry); daily cap of 15 tickets with a board notice

## Context
Pricing v3 (decided 2026-10-21): the ticket is the unit; the dollar ceiling only stops abuse. The ceiling moves from $100 to $300. Packs are prepaid and expire. A daily cap protects the box and the pool.

## Scope
- Raise the default monthly allowance to USD 300 (config and the per-org default row); existing orgs with the old default are migrated to 300 by a migration; orgs with a custom value are untouched.
- Add pack products: 25 tickets / USD 99 and 100 tickets / USD 349, as Paddle one-time prices (config holds the price ids; the catalog entries are created by the founder — the code reads them from config and fails closed with a clear error if missing). A purchased pack adds tickets with a 90-day expiry; consumption order: plan tickets first, then the oldest unexpired pack.
- Daily cap: 15 tickets dispatched per org per calendar day (org timezone); the 16th dispatch is held until the next day and the board shows a one-line notice "Daily cap reached — resumes at 00:00 <tz>". Expose `daily_cap` and `dispatched_today` on `GET /api/v1/billing/allowance`.
- Own-key overage carries no fee: no code path charges when `key_source` is `own`.

## Acceptance
- [ ] Tests: migration moves default-valued orgs to 300 and leaves custom ones; pack purchase, expiry and consumption order; daily cap holds the 16th dispatch and releases next day; no charge on own-key.
- [ ] `make build`, `make test`, `make lint` pass — paste the output into the PR body.

## Held legs (filed when upstream merges)

| Leg | Repo | After | Body source |
|---|---|---|---|
| C1 run-story endpoint | pilot-console | P1 merged | roadmap C1 + §8.1 |
| C2 share token | pilot-console | C1 | roadmap C2 + §8.1 D3 |
| U6 Run Story card + ticket page | pilot-console-ui | C1 | §8.1 |
| U7 share-link view | pilot-console-ui | C2 | §8.1 D3 |
| U8 Review needed page | pilot-console-ui | C3 merged | §8.2 |
| C6 brief store + Briefs API + email (SES) | pilot-console | P9 merged + I3 | §8.7 |
| U11 Briefs page + bell | pilot-console-ui | C6 | §8.7 |
| U12 brief settings | pilot-console-ui | C6 | §8.7 D3 |
| I2 pen test on canary | infra (Nelya) | P11 merged | §8.8 D1 |
| I3 SES sender | infra (Nelya) | — | §8.7 |
| D1–D5, D7 | Figma (founder) | — | §6, §8.1, §8.2, §8.7 |

## Refs

- U1 → https://github.com/qf-studio/pilot-console-ui/issues/239
- U2 → https://github.com/qf-studio/pilot-console-ui/issues/240
- U3 → https://github.com/qf-studio/pilot-console-ui/issues/241
- U4 → https://github.com/qf-studio/pilot-console-ui/issues/242
- U5 → https://github.com/qf-studio/pilot-console-ui/issues/243
- U9 → https://github.com/qf-studio/pilot-console-ui/issues/244
- P1 → https://github.com/qf-studio/pilot/issues/5790
- P9 → https://github.com/qf-studio/pilot/issues/5791
- P10 → https://github.com/qf-studio/pilot/issues/5792
- P11 → https://github.com/qf-studio/pilot/issues/5793
- C3 → https://github.com/qf-studio/pilot-console/issues/422
- C7 → https://github.com/qf-studio/pilot-console/issues/423
- C8 → https://github.com/qf-studio/pilot-console/issues/424
- Follow-ups from the 10-22 reviews: ui#262 (U2 fix) · ui#263 (USD absent) · ui#264 (U3 fix) · ui#265 (chat confirmation) · ui#266 (mode decision) · console#430 (activity since) · console#431 (proxy USD) · console#432 (allowance hygiene) · pilot#5810 (P17 subagent events, design)
