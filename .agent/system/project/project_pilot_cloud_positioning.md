---
name: project_pilot_cloud_positioning
description: Pilot Cloud positioning decisions 2026-10-21 — identity sentence, research→ticket thesis, proof ranking, segment order, offer, workflow improvements. Supersedes the "orchestration layer" line for Cloud copy.
type: project
---

# Pilot Cloud — positioning decisions (2026-10-21)

Founder session, 2026-10-21. Each section is a decision. Open items are marked **OPEN**.
This doc is the canonical source for Cloud copy and pricing pages. The older
`memories/decisions/strategy_pilot_positioning.md` ("orchestration layer", TB2.0 claim)
now applies to the OSS/developer story only.

## 1. Identity

> Pilot Cloud is a hosted autonomous engineer that turns labeled tickets into reviewed
> pull requests on a dedicated box, for small teams with more tickets than engineers.

- Outcome positioning, not layer positioning. The buyer pays for shipped tickets.
- "Dedicated box" resolves the self-hosted-vs-cloud conflict in `docs/content/index.mdx:73`
  and `why-pilot.mdx:45`: each tenant runs on its own EC2 instance (TASK-495/499).
  Cloud copy: "Your code runs on a box only you use."
- "Orchestration layer that makes any coding agent better" leaves Cloud copy; keep for OSS.

## 2. Research → tickets

Thesis: **Pilot research writes a spec for the executor, not only an answer for a human.**

What Claude Code cannot copy: the feedback loop. Only the system that executes tickets
knows which ticket shapes ship (receipts, false-success classes, `.agent/` graph).
Review moves upstream: a human approves a spec (prose), which is cheaper than a diff.

| | Claude Code | Pilot Cloud |
|---|---|---|
| Output | Prose for a human | Issue with H2 sections, file paths, acceptance criteria, `#N` deps |
| Memory | Dies with the session | `.agent/` graph, shared by every run on the repo |
| Feedback | None | Pilot sees which ticket shapes ship and which fail |
| Reviewer reads | A diff, after | A spec, before |
| Unit | A conversation | A ticket — the unit we bill and prove |

Decisions:
- D1 Bootstrap at signup is free, once: Pilot scans the repo, proposes the first ~10 tickets
  with `file:line` evidence. Later research/chat draws from the fair-use token pool and is
  **not** counted as tickets. Pool empty → own key, same as tickets.
- D2 Every Pilot-written ticket goes to **Needs You** before Queued. The human approves the spec.
- D3 why-pilot line "Not a researcher" is removed. Replacement: *"Ask about your code.
  Turn the answer into a ticket."*
- **OPEN — bootstrap unit economics.** The bootstrap must be a deep research, not a
  skim, or it does not sell. Large repos can cost a lot on Opus. Before the free offer
  goes live: measure bootstrap cost on repos of several sizes, set a per-repo cost cap,
  and define the degrade path (scope by directory / sample) when the cap is hit.
  Related: TASK-549 (Navigator context for legacy repos), TASK-518 (side-chat Navigator).

## 3. Proof

Nobody believes a claim; they believe a number they can check. Ranked:

1. **Pilot built Pilot.** 1,653 of 2,212 merged PRs on `qf-studio/pilot` came from
   `pilot/*` branches (2026-01-26 → 2026-10-20). Live counter on the landing page.
2. **Run Story** on every Done card: what was asked, diff link, tests, time, outcome.
   No dollars on platform-key tickets (a $ figure discloses margin). Show a fair-use
   meter (% of allowance) instead. Dollars only on own-key tickets.
3. **Bootstrap on their repo** — belief comes from their own PRs.
4. **Failure receipts** — publish the false-success classes we catch (TASK-460).
5. **No benchmark claim.** TB2.0 stays scrubbed.

Decisions: D1 lead with (1). D2 Run Story ships before public launch. D3 failure posts
are part of the content plan. The "read-only cost display" item in `saas-architecture.md`
is BYO-era and is superseded by the no-dollars rule above.

## 4. Market and offer

Segments, in order:
1. **Dev agencies**, 3–15 engineers, many client repos. They bill per ticket, feel the
   cost per ticket, and one win repeats across clients.
2. **Product teams**, 2–10 engineers, one repo.
3. **PM-only teams** (Pilot is the engineer) — later. Requires autopilot merge-on-green +
   evidence gates (TASK-460) + a preview URL on the Run Story so the PM reviews the result,
   not the code. Spec approval (D2 above) still by the PM.
- Not: indie devs (do not pay $499).

Offer:

> $499 a month. 100 shipped tickets. No seats. Your own box.

- Unit sold is a **ticket**, not tokens, not seats. The $300 fair-use ceiling is the only
  token word on the page.
- A ticket counts when its PR opens (TASK-546 definition). Keep.
- **Fair-use ceiling: $300 / tenant / month (decided 2026-10-21, was $100 since 10-01).**
  Ledger evidence (box DB `executions`, 2026-09-21 → 10-21, 324 runs, 6 repos): $311 total,
  mean $0.96 / run, p50 $0.52, p90 $2.32, max $16.10; Sonnet 5.5 mean $0.89; 100 runs ≈ $96.
  At $100 a tenant that uses all 100 tickets hits the dollar cap at the same time — one retry
  or one p90 ticket breaks the "100 tickets" promise. At $300 the cap is 3× the mean: the
  ticket counter is the real limit, the dollar cap only stops abuse. Worst-case margin
  $499 − $300 − ~$50 box ≈ $149. Caveats: our repos are Go with Navigator context — expect
  1.5–2× on a legacy customer repo; research turns and bootstrap are not in this data
  (TASK-581). Recheck after the first 5 tenants.
- "No seats" needs an **invite endpoint** (an org is one person today) — first gap to close.
- **Pricing v3 closed 2026-10-21** (TASK-546 D-items): packs 25 tickets $99 / 100 tickets
  $349, prepaid, expire in 90 days · daily cap 15 tickets per org, one-line notice on the
  board when hit · own-key overage carries no fee (we earn on the plan, not the tokens) ·
  no free tier — the free bootstrap is the trial, card entered before the first ticket ·
  legal pages (TASK-515, parked) are unparked: they gate Paddle go-live (TASK-497 L7) and
  therefore every sale.

## 5. Workflow

Today: sign up → connect repo → Provision → label / drag to Queued → PR → CI → Needs You
→ approve → merge → Done.

Improvements, in order:
1. **Run Story** on every Done card (receipts data exists, TASK-489). Smallest change.
2. **Bootstrap at signup** (needs TASK-549 + the cost cap above).
3. **Spec lane** — Pilot-written ticket → Needs You → Queued (needs TASK-518 leg 4).

Invite endpoint runs beside these (offer gap, not a workflow step).

## 6. Design notes — console UI (Figma `BfAqtVPBp0i4iWHg2jzAnB`, reviewed 2026-10-21)

Dashboard (node `7-2`) and Research page (node `13-994`), reviewed against sections 1–5.
Style, simplicity and grid: keep as designed.

Dashboard:
1. **No cost on rows.** Replace per-ticket `2.3K · 12 min` with `12 min · +184 −32` (duration +
   diff size). Drop `40,3B tokens` from the header. One pool meter at the top (`Pool 62%`).
   Tokens/dollars only on own-key tenants. (Section 3, no-dollars rule.)
2. **Blocked → "Review needed".** The card keeps the count and gets a button that opens the
   review list page. The spec lane (Pilot-written tickets, section 2 D2) lives on that page.
3. **Ask your pilot.** The input stays on the board. Submit opens the Research page with the
   answer. One input, one destination.
4. **Context panel.** Replace Reads/Created/Updated (placeholder `48/5/48`) with growth:
   `Memories 5.0K · +120 this week`. Label the `98%`.
5. **Header `142 hours` → `Last shipped 12 min ago`.** A liveness signal: the engineer is on
   duty, checkable in one click. Alternative kept in reserve: `31 merged · 30D`.

Research page:
1. **Ticket exit.** Add `Create tickets` under the report. Proposed tickets render as rows in
   the sub-agent style, each with `Approve` → Review needed. (Section 2 D3: "Ask about your
   code. Turn the answer into a ticket.")
2. **No cost on rows.** `0 t · 0 h` and `2.3K · 12 m` → duration only, plus the pool meter.
3. **Context panel per run.** Replace `Direction JEV 1.136 Successful/Failed` (judge jargon)
   with what the research used and made: `Read 12 docs · 4 memories · Created 2 memories`.
   This shows the feedback loop per run (section 2, row 3).
4. **Keep the sub-agent tree with DONE badges.** Research is work with receipts.

## 7. Onboarding — two paths after signup (decided 2026-10-21)

Both paths end in the same object: a set of proposed tickets plus a `.agent/` context, which
the human approves (Review needed → Queued). Only the input differs.

**New project — interview, not scan.**
- Pilot asks at most 5 questions on the Research page: what it is, the stack, the first user
  flow, the deploy target, the constraints. Each question offers a default.
- Output: one scaffold ticket, then 5–10 first tickets with `#N` deps, per
  `.agent/sops/onboarding/new-project-issue-authoring.md`. The answer ends with `Create tickets`.
- **Deploy templates.** The deploy-target question is a pick from templates, each a starter
  ticket set (infra-as-code + CI deploy workflow + env pipeline + a Needs You step where the
  customer supplies cloud credentials): **VPS** (Docker Compose + GitHub Actions over SSH) and
  **AWS** first; **Azure** and **Google Cloud** later. Reuses Pilot's env pipelines and the
  post-merge deployer.

**Legacy project — scan first, then docs.**
- Step 1: scan what is already connected — repo, README, `docs/`, open issues, the last ~50
  merged PRs (PR history is the best doc a legacy repo has). TASK-549 covers this. The
  TASK-581 cost cap applies.
- Step 2: ask for up to 3 external sources. V1 accepts a URL or an upload; Pilot stores them
  under `.agent/system/` so Navigator indexes them. Notion / Confluence connectors are not v1.
- **OPEN — external docs ingestion** is a system of its own (URL fetch, upload, connectors).
  Decide after the first 3 legacy tenants show what they actually have.

## 8. Feature specs — launch cut for agencies

Launch cut (section 4 segment 1): (1) Run Story · (2) Review needed lane · (3) Research page
`Create tickets` · (4) Bootstrap (section 7) · (5) Invite endpoint. Everything else
(provision, kanban, `pilot` label, autopilot merge) exists.

### 8.1 Run Story (decided 2026-10-21)

The card for one ticket. The proof unit.

Fields:
- Asked — ticket title, issue link.
- Changed — PR link, files, `+184 −32`, one-line summary.
- Verified — tests passed / failed, CI status, evidence-gate result (TASK-460).
- Time — issue → PR, PR → merge.
- Outcome — one of four states; model used (Sonnet / Opus).

States: **Running** (current phase, live) · **Review needed** (PR open, waits on the human) ·
**Merged** · **Failed** (reason class: CI / env / scope; `Retry` action via the TASK-485 path).

Appears: the Done card on the board (expand on click) · the ticket page · the daily receipts
digest (TASK-489 data) · a share link, opt-in per story, secrets redacted (the sales artifact).

Never shows: tokens or dollars on the platform key (section 3) · judge names or versions.

Decisions: D1 fields as above · D2 four states, `Retry` on Failed · D3 share link, opt-in per
story · D4 model name shown, cost not.

### 8.2 Review needed lane (decided 2026-10-21)

The human's one job. Dashboard card "Review needed" shows the count and opens this list.

Item types — each shows one line that says why it needs a human:
- A PR Pilot opened, when the project runs in `prod` mode (merge needs approval).
- A ticket Pilot wrote (bootstrap, research). The human approves the spec (section 2 D2).
- A decision Pilot cannot make: credentials, ambiguous scope, a destructive action
  (`irreversible-actions.md`, DecisionRecorder seam).

Actions per item:
- `Approve` → spec goes to Queued · PR merges · decision is recorded.
- `Reject` with a reason → the reason is stored as a learning in `.agent/`.
- `Send back` with a comment → Pilot revises the ticket or the PR (a revision, not a draft flip).

Rules: one list, oldest first, grouped by project · the dashboard count is this list · nothing
waits in silence — the daily brief lists items older than 24 h.

Decisions: D1 three item types · D2 three actions, reject reason → learning · D3 oldest first,
grouped by project, 24 h in the brief · D4 v1 is owner-only; roles come with the invite endpoint.

### 8.3 Research page → `Create tickets` (decided 2026-10-21)

Flow:
1. The user asks, from the board input or the Research page. Modes: `Research` (sub-agents,
   read-only) and `Docs` (answers from `.agent/`).
2. Pilot answers: the sub-agent tree with DONE badges, then the report.
3. `Create tickets` under the report → Pilot drafts N tickets from the report.
4. Each draft goes to Review needed as a spec item (8.2). `Approve` creates the GitHub issue
   with the `pilot` label → Queued. The user can edit a draft before approval.
5. A rejected or sent-back draft becomes a learning.

Draft format — the issue-authoring SOP (`.agent/sops/onboarding/new-project-issue-authoring.md`):
H2 sections, an `## Acceptance` list, `file:line` evidence, `#N` deps. Every required change is
under Acceptance. No claim without evidence — Pilot copies issue claims verbatim (learning
mem-203), so a wrong claim ships.

Shippable check per draft: one PR · a testable Acceptance list · evidence-linked claims only.
A draft that fails is split into an epic with sub-issues (epic decomposition exists).

Rules: no draft becomes an issue without approval (section 2 D2) · research draws from the
fair-use pool, not from the 100 tickets; a ticket counts when its PR opens · a daily cap on
research turns per org protects the pool.

Decisions: D1 SOP draft format · D2 shippable check, epic split on failure · D3 edit before
approve · D4 50 research turns per day per org, tunable.

### 8.4 Invite endpoint — "No seats" (decided 2026-10-21)

"No seats" is a pricing-page promise. **Correction 2026-10-21 (inventory):** org invites, the
accept page and the Members page are already shipped (TASK-564/565/566, ui#231); TASK-546's
unchecked boxes are stale. The remaining gaps are the project-scoped **Viewer** role and
**actor tracking** on lane actions (D1, D4 below). D2/D3 are verification items against the
shipped code, not new work.

Roles:
- **Owner** — billing, provision, delete the org, invite.
- **Member** — everything in Review needed, the queue, research. Can invite Members and Viewers.
- **Viewer** — read-only, scoped to named projects. For an agency this is the client: they see
  their board and Run Stories, nothing else. A selling point, not a cost.

Invite flow: an Owner or Member enters an email and a role (a Viewer invite also names the
projects) → Pilot sends a link → the link expires in 7 days → the invitee signs in with GitHub
and joins the org.

Rules: unlimited members, the price does not change · 20 invites per org per day (abuse guard)
· every Review needed action records the actor (required once two people act).

Decisions: D1 three roles, Viewer project-scoped · D2 email link, 7-day expiry, GitHub sign-in
· D3 unlimited members, 20 invites/day · D4 every lane action records the actor.

### 8.5 Live log tail + redaction scrubber (decided 2026-10-21)

Proof in real time, on a Running Run Story (8.1).

Exists: the per-execution stage timeline (`GET /api/v1/executions/{id}/events`, GH-4749) —
`detail` is served verbatim, no scrubber · secret-shape regexes in one package,
`internal/executor/secretpatterns` (used by the acceptance-evidence redaction, GH-5437) ·
a `/ws/dashboard` proxy is planned in S4 (`saas-roadmap.md`), not built.

What the user sees: the stage timeline, live · one line per tool call in the Research-page
sub-agent style — `read internal/foo.go` · `edit internal/foo.go +12 −3` ·
`run go test ./... ✓` · **no raw transcript** (secrets and prompt internals).

Scrubber: one function at the gateway edge, applied to event `detail` and to the stream —
`secretpatterns` regexes + values of env vars whose name matches
`(?i)token|key|secret|password|credential`. Same package as the evidence redaction, so the
two never drift.

Decisions: D1 stages + tool-call lines, no raw transcript in v1 · D2 scrub at the gateway edge
(daemon leg in the pilot repo) · D3 transport = `/ws/dashboard` proxy · D4 stream ephemeral,
tool-call lines persist 7 days, stage timeline persists as today.

### 8.6 Marketing site — `pilotcloud.dev` (decided 2026-10-21)

Exists: repo `pilotcloud-site` (Next.js 15 static export, Bun), 9 pages — landing, features,
how-it-works, integrations, compare, self-hosted, terms, privacy, refunds. Hosting ready
(Nelya I1: bucket `pilot-fleet-s3-site`, CloudFront `E39M9CANDXR187`). Deploy workflow = a
PR Nelya still has to push. Legal pages parked on founder facts. Full state: TASK-515.

Changes from this doc:
1. **Hero** = the identity sentence (section 1). The "orchestration layer" line leaves Cloud copy.
2. **Proof counter** — "Pilot built Pilot: 1,653 of 2,212 merged PRs" (section 3). Fetched at
   build time by a script in `scripts/`, shown with a date, rebuilt weekly.
3. **Pricing block** = section 4: `$499 a month · 100 shipped tickets · No seats · Your own
   box`; packs below; "fair use" is the only token word. Price string pinned to the Paddle
   catalog (`pri_01m4g870rh98m207cjwhjn8taq`).
4. **Self-hosted page** keeps "your secrets never leave" for OSS; the Cloud column says
   "a box only you use".
5. **Product name** on the site: **Pilot Cloud**. "Console" is the app URL only.

Order to ship: (1) founder supplies legal entity, address, contact email → legal pages
unpark · (2) Nelya's workflow PR → review → first deploy · (3) Paddle resubmit (TASK-497 L7)
· (4) copy update 1–5 rides the first or second deploy.

Decisions: D1 hero A · D2 build-time counter · D3 pricing block · D4 OSS keeps the
self-hosted claim · D5 name = Pilot Cloud.

### 8.7 Briefs in the console (decided 2026-10-21)

Exists: daemon daily brief (Slack, `orchestrator.daily_brief`), weekly brief (manual),
receipts digest (Telegram only, 18:00, GH-5257), console bell popover (UI-5). A Cloud tenant
with neither Slack nor Telegram gets nothing.

One brief object, three channels: **console** (a Briefs page, newest first; the bell shows
the unread one) · **email** (default — every tenant has one; instance-down alerts use the
same channel) · **Slack / Telegram** via the Connections page, as today.

Daily content, in order: (1) Shipped today — one Run Story line each, no cost on the
platform key · (2) Review needed — items older than 24 h first · (3) pool meter, percent ·
(4) Failed — reason class and `Retry`. The receipts digest folds into this; cost lines appear
only for own-key tenants.

Weekly, Monday: tickets shipped, median time to PR, merged count; opt-in share link (the
proof of the week).

Decisions: D1 one brief object, three channels, email default · D2 receipts digest folds in,
cost lines only on own-key · D3 daily content as listed, tenant time + timezone, default
18:00 · D4 weekly Monday with proof numbers and an opt-in share link.

### 8.8 Security close-out (decided 2026-10-21)

Exists: per-tenant VM/SG/IAM, KMS-encrypted EBS, SecureString secrets, gateway bearer ·
executor env scrub + destructive-command hook on by default (TASK-491) · write-boundary hooks
(TASK-551) · evidence redaction (GH-5437) · GitHub App installation tokens instead of
long-lived PATs (TASK-461). Blast-radius statement: `saas-architecture.md:138`.

Planned (S5), all three:
1. **Hostile-ticket pen test** — a prompt-injected issue tries the env, the disk, SSM, the
   network outside the allowlist, and another tenant. A repeatable harness: fixture repo,
   issue bodies, assertions. Runs on the canary tenant before every AMI roll. **Hard gate
   before the first tenant with a private repo.**
2. **Egress allowlist proxy** on the tenant box — Anthropic, GitHub, tracker APIs, and the
   package registries builds need (npm, Go proxy, PyPI). Registries stay an exfil path:
   log all egress, disclose the residual.
3. **Postgres RLS** in console-db — `FORCE ROW LEVEL SECURITY` + `app.current_tenant_id`.
   Defense in depth, low effort.

Customer-facing: a **Security page** on the site — the blast-radius statement verbatim,
"a box only you use", the last pen-test summary with a date. Agencies with client repos
ask this first.

Decisions: D1 repeatable harness, canary before every AMI roll, hard gate before the first
private-repo tenant · D2 allowlist with registries allowed, egress logged, residual disclosed
· D3 RLS wired · D4 Security page with statement + pen-test summary.

## 9. Post-launch scopes (one paragraph each, 2026-10-21)

1. **Viewer role + actor tracking** (8.4 gap). Add `viewer` to the org roles with a
   `project_ids` scope; viewers read the board, Run Stories and briefs for those projects
   only, no actions. Every Review needed action (8.2) stores `actor_id` and shows "Approved
   by …" on the item. Done when an agency invites a client as Viewer on one project and the
   client sees nothing of the other projects.
2. **Deploy templates** (section 7). A template = a starter ticket set (infra-as-code + CI
   deploy workflow + env pipeline + a Needs You step for cloud credentials), picked in the
   new-project interview. Order: VPS (Docker Compose + GitHub Actions over SSH), AWS, then
   Azure, Google Cloud. Done when a new project reaches a deployed `main` from the template
   tickets alone, with no hand edits.
3. **External docs ingestion** (section 7, OPEN). V1: a URL or an upload lands under
   `.agent/system/` so Navigator indexes it; the bootstrap and research turns read it.
   Connectors (Notion, Confluence) only after the first 3 legacy tenants show what they
   actually have. Done when a research answer cites an uploaded doc by path.
4. **PM-only mode** (segment 3). Per project: autopilot merge-on-green + the evidence gates
   (TASK-460) + a preview URL on the Run Story. The PM approves specs (8.2) and reviews the
   result, not the code. Gated on the evidence gates. Done when a project runs one week
   with no engineer in the lane and no false success in the ledger.
5. **Docs manage/edit** (TASK-466 idea). The console Docs page gets edit + create for
   `.agent/` files through the existing daemon gate, with a PR per change (no direct
   writes to `main`). Done when a tenant edits a system doc from the console and the change
   lands as a reviewed PR.
6. **Mobile v1** (TASK-478 UI-12, stalled since 08-15). Re-land the preserved branch
   (`restore/GH-71-mobile`) on the new design (section 6): 4-tab bar, home glance tiles,
   Review needed sheet, chat full-bleed. Done when the Playwright 390×844 check passes on
   the new design.

## 10. Roadmap — waves (2026-10-21)

Order by dependency and by what unblocks a sale. Tracks run in parallel per repo
(site · console-ui · console-api · daemon · infra); Navigator writes a task doc per leg,
Pilot executes. No dates: Pilot throughput sets the pace (~10 issues/day across repos).

| Wave | Goal | Legs (spec) | Repos | Gate / dependency |
|---|---|---|---|---|
| **0 — Unblock the sale** | A public site, legal pages, Paddle live | legal facts → legal pages · Nelya deploy PR → first deploy · Paddle resubmit · site copy 1–5 (8.6) | pilotcloud-site, ops | founder facts; Nelya PR |
| **1 — Design update + proof surface** | The new console (section 6) with the proof unit | Figma re-skin: dashboard + Research page (no-cost rows, pool meter, Review needed card, Last shipped, Context growth) · Run Story card + ticket page (8.1) · Briefs page + email channel (8.7) · pen-test harness (8.8 D1) in parallel on the daemon/infra track | console-ui, console-api, pilot, infra | pen test is a **hard gate** before the first private-repo tenant — agencies have private repos, so it is launch-blocking |
| **2 — Research → tickets** | The thesis (section 2) on the wire | `Create tickets` + drafts in the lane (8.3) · spec items + actor tracking + reject→learning (8.2) · daily research cap check | pilot, console-api, console-ui | TASK-518 leg 4 |
| **3 — Onboarding** | Both signup paths (section 7) | bootstrap with cost cap · new-project interview · legacy scan + external docs v1 (upload/URL) | pilot, console-ui | TASK-581 result (cost cap) |
| **4 — Trust close-out** | Real-time proof + security | live log tail + scrubber (8.5) · egress allowlist + RLS (8.8 D2/D3) · Security page (8.8 D4) | pilot, console-api, console-ui, infra, site | — |
| **5 — Post-launch** | Section 9 | Viewer role · deploy templates · docs ingestion v2 · PM-only mode · docs edit · mobile | all | first 5 tenants' data |

Founder inputs that gate waves: legal entity / address / contact email (W0) · Nelya's
deploy workflow PR (W0) · run TASK-581 and pick the cap (W3).

## Copy changes implied

- `docs/content/index.mdx:73` "secrets never leave your environment" → dedicated-box wording.
- `docs/content/concepts/why-pilot.mdx:189-191` "Not a researcher" → "Ask about your code.
  Turn the answer into a ticket."
- Pricing page unit = tickets; one product name (**Pilot Cloud**, not "Pilot Console" in copy).
