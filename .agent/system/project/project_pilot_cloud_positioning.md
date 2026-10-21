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
- "No seats" needs an **invite endpoint** (an org is one person today) — first gap to close.
- Packs and daily cap follow from the above (pricing v3, TASK-546).

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

## Copy changes implied

- `docs/content/index.mdx:73` "secrets never leave your environment" → dedicated-box wording.
- `docs/content/concepts/why-pilot.mdx:189-191` "Not a researcher" → "Ask about your code.
  Turn the answer into a ticket."
- Pricing page unit = tickets; one product name (**Pilot Cloud**, not "Pilot Console" in copy).
