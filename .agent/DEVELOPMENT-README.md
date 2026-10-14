# Pilot Development Navigator

**Navigator plans. Pilot executes.**

## WORKFLOW: Navigator + Pilot Pipeline

**This session uses Navigator for planning, Pilot for execution.**

### The Pipeline

```
┌─────────────────┐                          ┌─────────────────┐
│   /nav-task     │  ───── plan ──────────►  │  GitHub Issue   │
│   (Navigator)   │       --label pilot      │  (with pilot)   │
└─────────────────┘                          └────────┬────────┘
        ▲                                             │
        │                                             ▼
        │ iterate                            ┌─────────────────┐
        │ if needed                          │   Pilot Bot     │
        │                                    │   (executes)    │
┌───────┴─────────┐                          └────────┬────────┘
│   Review PR     │  ◄──── creates PR ───────────────┘
│   Merge/Request │
└─────────────────┘
```

### Workflow Steps

| Step | Command | Action |
|------|---------|--------|
| 1. Plan | `/nav-task "feature description"` | Design solution, create implementation plan |
| 2. Execute | `"dispatch TASK-XX to Pilot"` (auto-invokes `nav-pilot`, v6.16.0+) — or raw `gh issue create --label pilot` | Hand off to Pilot for execution |
| 3. Review | `gh pr view <n>` | Check Pilot's PR |
| 4. Ship | `gh pr merge <n>` | Merge when approved |

### Quick Commands

```bash
# Plan a feature (Navigator does the thinking)
/nav-task "Add rate limiting to API endpoints"

# Hand off to Pilot — preferred: nav-pilot skill (Navigator v6.16.0+)
#   "dispatch TASK-XX to Pilot"          # auto-resolves doc → gh issue from H1 + --body-file
# Raw equivalent (when bypassing the skill):
gh issue create --title "Add rate limiting" --label pilot --body "..."

# Check Pilot's queue
gh issue list --label pilot --state open

# Review PR
gh pr view <number>

# Merge when ready
gh pr merge <number>
```

### Rules

| Do | Don't |
|----|-------|
| Use `/nav-task` for planning | Write code directly |
| Create issues with `pilot` label | Make commits manually |
| Review every PR before merging | Create PRs manually |
| Request changes on PR if needed | Approve without review |
| Let merged work ride the 16:00 CET release train | Cut ad-hoc releases (incidents only — see Release Cycles) |

### Release Cycles (workflow decision, 2026-07-09 — mem-104)

Work is organized in **cycles** (Linear-style), layered ON TOP of the
Navigator + Pilot pipeline above — planning/dispatch/review/merge are
unchanged; cycles govern **scope and release cadence** only:

1. **Ideate & research** — as before (`/nav-task`, navigator-research agents).
2. **Plan the cycle** — pick the updates that ship this cycle; the cycle
   **ends before the release train**, so scope what can merge by then.
3. **Execute & collect** — dispatch to Pilot; merged PRs **accumulate on
   `main` unreleased**. Merged-but-unreleased is the NORMAL state, not an
   incident (do not "fix" it — see mem-093 for what an actual release wedge
   looks like).
4. **Release** — the scheduled train tags at **16:00 Europe/Berlin**. The
   pilot repo is **daily** (`schedule: "0 16 * * *"`); the other project
   repos are Mon–Fri (`0 16 * * 1-5`). Config in `~/.pilot/config.yaml`.

**The one exception**: incidents. A production-impacting fix does NOT wait
for the train — release ASAP (out-of-band tag is safe; the releaser reads
its baseline live from git tags, mem-093).

**Cutover COMPLETE (2026-07-10)**: pilot repo flipped `on_merge → on_schedule`
after two prerequisites landed — #4150 (append ` (#N)` to squash titles so
`resolveTrainMemberPRs` can resolve members; without it `on_schedule` skips
every tick with "no resolvable member PRs") and #4174 (no-tags-repo first
release). Verified live: scheduler runs `0 16 * * *`, next_run correct, no
release cut on restart. Watch item: the train still skips a repo whose
squash commits predate #4150, or a repo with zero tags.

---

## CRITICAL: Core Architecture Constraints

### 1. Navigator Integration (runner.go)

**NEVER remove Navigator integration from `internal/executor/runner.go`**

The `BuildPrompt()` function MUST invoke `/nav-loop` mode when `.agent/` exists. This is Pilot's core value proposition:

```go
// LocalMode takes priority — checked FIRST (GH-2103, bench val10)
if task.LocalMode {
    return r.buildLocalModePrompt(task)  // problem-solving prompt, no PR constraints
}

// Navigator-aware prompt structure for medium/complex tasks
if useNavigator {
    sb.WriteString("Use /nav-loop mode for this task.\n\n")  // <- NEVER REMOVE
    // ... PILOT EXECUTION MODE override for CLAUDE.md rules
}
```

**LocalMode priority (GH-2103)**: `task.LocalMode` MUST be checked before Navigator detection. Sandbox environments (bench, CI) may have `.agent/` directories that hijack the prompt to Navigator path. LocalMode = problem-solving prompt without PR workflow constraints.

**Incident 2026-01-26**: Navigator prefix was accidentally removed during "simplification" refactor. Pilot without Navigator = just another Claude Code wrapper with zero value.

### 2. Navigator Auto-Init (v0.33.16+)

Navigator is now auto-initialized for projects without `.agent/`. In `runner.go Execute()`:

```go
// Auto-init Navigator if configured and missing
if r.config.Navigator.AutoInit && !initialized {
    r.maybeInitNavigator(task.ProjectPath)  // Creates .agent/ from templates
}
```

Disable via config: `executor.navigator.auto_init: false`

---

## Quick Navigation

| Document | When to Read |
|----------|--------------|
| CLAUDE.md | Every session (auto-loaded) |
| This file | Every session (navigator index) |
| `.agent/system/FEATURE-MATRIX.md` | What's implemented vs not |
| `.agent/system/ARCHITECTURE.md` | System design, data flow |
| `.agent/system/PR-CHECKLIST.md` | Before merging PRs in `--env=prod` mode |
| `.agent/system/jev-gates-roadmap.md` | Before adding a Jev/TypeSafe classifier to any gate: triage rule, UPGRADE vs SKIP verdict per gate, sequencing, shadow rollout protocol |
| `.agent/product/PRICING-MODEL.md` | **What we charge for and why** — $499 flat, 100 tickets included (Sonnet 5.5), own key past the cap; v3 (packs) researched 10-13, TASK-546. Canonical; read before any pricing conversation |
| `.agent/product/LEGAL-TERMS.md` | **Source of truth for `/terms`, `/refunds`, `/privacy` and the licence summary on pilotcloud.dev** — DRAFT 10-14, `[FOUNDER]` fields + lawyer review open; numbers live on the pricing page, never here |
| `.agent/product/UNIT-ECONOMICS.md` | Cost, margin, break-even and customer TCO per tenant — measured, not modelled |
| `.agent/tasks/TASK-XX.md` | Active task details |
| `.agent/sops/*.md` | Before modifying integrations |
| `.agent/system/references/reference_slack_notifications_routing.md` | Before touching Slack/alert/approval destinations on the box (which channel gets what, the 3 keys, restart rule) |
| `.agent/.context-markers/` | Resume after break |

### Research Reports (research/)

- `research/ai-coding-agent-products-price-extra/report.md` — Cost-plus 1-4% per ticket loses money; keep Pilot's flat plan (47 sources, 2026-10-13)

## Current State

**Current Version:** box runs **v2.283.0** (out-of-band tag 10-13 17:19Z; self-upgraded 17:24Z). **Hosted tenants now self-upgrade too** (headless pipeline PR#5654 + sha256 PR#5655 + console PR#400; tenant `i-0289111000cebcee9` took v2.283.0 at 17:22Z with no SSM). v2.284.0 pending: PR#5667 alert + PR#5668 lint + the in-flight #5665/#5666.

**PRIORITY (founder directive 2026-07-26 — supersedes 07-17):** **SaaS/platform UNPARKED — TASK-405 is active work again.** The 07-17 ordering (pointer delivery → pilot reliability → SaaS parked) held while the dispatch-reliability chain was open; that chain closed with v2.246.0 on 07-25. Pointer and pilot reliability remain live tracks but no longer gate S-milestone dispatch. Memory: `founder-priority-pointer-first-saas-parked` (superseded).

**Recent (Oct 5 – Oct 13 2026; detail lives in `system/saas-roadmap.md`, `system/side-chat-navigator.md`, `tasks/archive/`, memories and git log — do not re-grow this block, replace it):**
- **10-14: PRICING V3 + LEGACY BOOTSTRAP DISPATCHED, PRICE UNCHANGED ([TASK-546](tasks/TASK-546-pricing-v3-honest-allowance-overage-packs.md), [TASK-549](tasks/TASK-549-legacy-repo-navigator-bootstrap.md)).** 10-13 research (nav-research on 4 repos + nav-deep-research, 47 sources, 11 graph memories): founder's cost+1-4%/ticket rejected (nets -$57..-$2 vs +$321 flat; Paddle 5%+$0.50 > markup); "100 tickets" is enforced as a $100 cap; chat turns are unmetered and uncapped per org; an org is one person (no invites); legacy repos run every ticket cold (placeholder scaffold, no copy-back). 10-14: ten issues filed across pilot/console/ui for metering, caps, invites, bootstrap; packs/copy/$300 deferred to a price decision. TASK-547 (#5671 → PR#5674) reviewed APPROVE and archived after an overnight `pilot-needs-human` park caused by the dispatch commit archiving the TASK-542 doc it cited. **`product/LEGAL-TERMS.md` written** as the source of truth for the site's `/terms` `/refunds` `/privacy` and licence summary (TASK-515 S2); four `[FOUNDER]` fields + lawyer review open; the 90-day small-org sunset is a proposal, not in `LICENSE`.
- **10-13: FIRST REAL TENANT SMOKE → 10 TICKETS SHIPPED + REVIEWED IN ONE DAY → TENANTS SELF-UPGRADE.** Smoke of the side-chat Navigator on tenant `i-0289111000cebcee9` shipped pilot-ship-test-go#7 → PR#8 in 11 min and exposed 6 product gaps; all fixed same day: chat Refs rewrite ([TASK-531](tasks/archive/TASK-531-chat-filed-issues-untracked-refs.md)), headless self-upgrade + sha256 + console bootstrap ([TASK-532](tasks/archive/TASK-532-headless-self-upgrade-hosted-tenants.md)/[533](tasks/archive/TASK-533-upgrade-checksum-verification.md)/[537](tasks/archive/TASK-537-console-bootstrap-writable-binary-auto-upgrade.md)), board In Progress from `pilot-in-progress` ([TASK-534](tasks/archive/TASK-534-console-in-progress-from-pilot-label.md)), activity journal ([535](tasks/archive/TASK-535-console-activity-journal-ingest-and-pr-merged.md)), ingest nudge ([536](tasks/archive/TASK-536-console-ingest-nudge-after-file-and-dispatch.md)), UI refresh ([538](tasks/archive/TASK-538-ui-board-refresh-mount-focus-chat-file.md)), `pr_merged` rendering ([543](tasks/archive/TASK-543-ui-render-pr-merged-activity-and-ingest-source.md)). Releases v2.282.0 + v2.283.0 out-of-band; the tenant self-upgraded headless 27 s after publication. Memories: `tenants-do-not-self-upgrade-hosted-invariant` (resolved), `chat-filed-issues-cite-untracked-agent-scaffold`.
- **10-13 14:00Z INCIDENT: THE 16:00 TRAIN NEVER TAGGED — pilot controller wedged 57 min.** `reconcileReleaseBackfill` ran inside the Run tick with no deadline and walked all 903 tags oldest-first per row. Diagnosed with a SIGQUIT goroutine dump (daemon stderr is a file), mitigated by restart + `release_backfill_abandoned=1` on the orphan row, fixed by [TASK-539](tasks/archive/TASK-539-epic-parent-pass-off-tick-with-deadline.md) (reconcilers off the tick, deadline, row cap) + [TASK-540](tasks/archive/TASK-540-release-backfill-newest-first-binary-search.md) (newest-first probe + binary search; continuation #5661 after a conflict) + [TASK-541](tasks/archive/TASK-541-epic-pass-liveness-alert.md) (staleness alert). Memory: `release-backfill-sweep-runs-inside-controller-tick-and-wedges-the-train`.
- **10-13: HOMEBREW TAP REPAIRED (pilot#5615 closed).** The tap token had been scoped to the grot tap since 10-05; access fixed on the token, the v2.283.0 formula pushed by hand (a goreleaser rerun on a published tag 422s — memory `goreleaser-rerun-on-published-tag-fails-422-push-formula-by-hand`); TASK-545 makes the tap push a separate non-fatal job.
- **10-09→10-12: SIDE CHAT IS A NAVIGATOR — ALL 5 LEGS MERGED + REVIEWED + PROD-PROVEN 10-13** ([TASK-518](tasks/archive/TASK-518-side-chat-navigator-research-and-issue-filing.md), note `system/side-chat-navigator.md`). Side effect fixed: autopilot redrives any CI-side held PR on a new head, survives restarts, legacy holds backfilled (TASK-528/529/530, archived).
- **10-09: PADDLE L7 STEPS 1+2 ON LIVE + GATE FOLLOW-UP SHIPPED.** paddle-live MCP connected (OAuth; scopes Prices Write + Client-side tokens Write only, set under `vendors.paddle.com/mcps`): live audit clean → **$499 twin `pri_01m4g870rh98m207cjwhjn8taq` created additively** · live client token `ctkn_01m4g87ga97b6stpk4hxp5zg41` → Doppler `prd` `PADDLE_CLIENT_TOKEN`. Founder dashboard items remain (API key · webhook destination · domain approval · payment link); Nelya template ask still unanswered since 09-30. pilot#5625 → **PR#5626 merged by autopilot, reviewed APPROVE-w-defect** (3 pins run by reviewer, all kill; defect: `extractFailingTests` is Go-only so every vitest/pytest/cargo pin renders "no test failed" → [#5627](https://github.com/qf-studio/pilot/issues/5627) → **PR#5628 merged 12:42Z, reviewed APPROVE-w-notes**: per-toolchain parser + non-zero-exit fallback, both pins kill; note: a compile-breaking Go mutation now counts as a kill labelled `<exit 1, unparsed>`). Live API key `pilot-console-prod` created (24 scopes, rotatable, 90 d) → Doppler `prd` `PADDLE_API_KEY`, verified 200. Live webhook destination `ntfset_01m4gbtxeevnar9mma451sbh1w` created by API, secret piped into Doppler `prd` — **all three Paddle secrets now in Doppler `prd`**; Payment link set + `console.pilotcloud.dev` submitted for approval (In review; needs ToS/privacy/refund links on the site). **Paddle side of L7 complete.** Nelya nudged 13:03Z with the price id. Left: SSM write (needs Nelya grant), template sync + flag flip, readiness audit. **Founder decision 10-09: landing page + legal pages for `pilotcloud.dev` is a SEPARATE session** (apex has no DNS; console has no public legal routes; Paddle approval needs ToS/privacy/refund) — brief in `.context-markers/2026-10-09_handoff-landing-page-session.md`.
- **10-12: PILOTCLOUD.DEV LANDING BUILT LOCALLY ([TASK-515](tasks/TASK-515-pilotcloud-landing-and-legal-pages.md)).** New private repo `pilotcloud-site` registered on the box; scaffold shipped by Pilot (site#1 → PR#3, merged 10-09). Landing then built by Navigator with the founder in a live Chrome loop on `feat/landing-story` (paper-sketch layout: real tickets → GO → board → steps/gates → merged PR → triggers/integrations/gates → pricing; depth style pass 1). No PR yet; site#2 held. Legal pages parked on founder facts; deploy parked on Nelya I1; Paddle approval gated on both. Marker `2026-10-12_landing-story-local-build.md`.
- **10-09: CONSOLE SIDE CHAT FIXED SAME DAY, FOUNDER-CONFIRMED ~13:55Z — "Chat isn't enabled for this org" on every tenant ([TASK-514](tasks/archive/TASK-514-side-chat-not-enabled.md)).** Root cause: the tenant config renderer (console `internal/fleet/configrender.go`) never wrote `adapters.chat.enabled: true`; daemon default off → routes absent → 404 → console 409 `chat_not_enabled`. Chat had only ever been proven on a hand-written config (TASK-464/469). Four legs dispatched 12:50Z, all merged + reviewed by 13:45Z (every mutation pin run by the reviewer, Pilot had listed them "Not verified"): console#383→PR#385 (`ChatEnabled` param + repo-sync sweep rollout, one bump + restart per existing instance), console#384→PR#386 (log daemon status/cause on 502, `url.PathEscape` conv id), ui#221→PR#222 (cursor reset when `cursorSeq > latestSeq`, inline send error), pilot#5629→PR#5630 (example-yaml load test; issue premise was wrong — stanza already existed, truncated grep). Console deployed 13:13Z (prod-0.1.23), UI 13:11Z; 60 s sweep restarted tenant daemons ~13:14Z. **Process miss:** issues filed with raw `gh issue create` again → founder reaffirmed nav-task slices / nav-pilot dispatches; memory `file-pilot-issues-via-nav-pilot-skill-only` updated (recurrence 2).
- **10-08: TWO REVIEW WAVES CLOSED SAME DAY — 10 PRs merged + reviewed across console-ui and console.** Gap wave from TASK-513 (ui#205/206/207, console#373/374) merged by 11:17Z; reviews APPROVE-w-notes (PR#209 freeze root cause unproven; PR#375 N+1 GitHub calls unbounded). PR#376 conflict (two EOF test appends) merged in a temp worktree → autopilot re-adopted (GH-4610 path). GH-205 was held 5 ticks by a cross-repo docs path in the body — body edit cleared it. Review notes → two navigator-research briefs → follow-up wave ui#211/212/213 + console#377/378 filed 12:21Z, all merged by 12:47Z, all reviewed with mutation pins proven by the reviewer (Pilot lists pins 'Not verified' — mem-220). Third wave filed 16:21Z, ALL MERGED by 16:37Z, reviewed 16:55Z: ui#217→PR#219 (generation counter in chat store; 2 mutations run by reviewer, both kill) · ui#218→PR#220 (`.pilot/workflow.yaml` v1 front-matter; `Loaded .pilot/workflow.yaml` log line still to confirm on the next ui dispatch) · console#381→PR#382 (30 s Validate deadline → UpstreamError/503, ReadHeaderTimeout 10 s; pin run by reviewer, kills). Pins not pasted because the Acceptance bullets had no `->` arrow (authoring, not a gate defect — mem-220 corrected); the two real gate gaps (freeform pins never run by the executor · mutation runner is `go test`-only) filed as [pilot#5625](https://github.com/qf-studio/pilot/issues/5625). Loop recorded as mem-221.
- **10-07→10-08: TASK-513 REAL EXHAUSTION TEST DONE ON PROD (archived) — and it found three fleet-breaking regressions.** Provision had been dead since console PR#321 (09-24): `dispatchLong` ran on the per-tick ctx → every provision canceled, `fail()` could not settle → 1/min loop (console#367→PR#368, prod-0.1.16); same for config push → boxes never received repos (console#369→PR#370, prod-0.1.17); golden AMI had no `make` → every Makefile gate exit 127 (Nelya: ami-06825978577ce40d4; pilot#5622→PR#5623 fallback + gate detail in the failure comment). Then both allowance branches proved on two test orgs: own-key switch (Testica), and no-key suspend → EC2 stop → own-key save → resume in 36 s → PR#324 on the own key with pool-02 flat (Test 2). 8 gap issues filed (ui#205–207, console#371–374, sdk#146). Learned: no operator-safe single-box AMI roll exists (console#371); never terminate a test org (retires its pool key); the console SPA freezes long-lived tabs (ui#206).
- **10-06→10-07: TASK-502 LEG 3 ENFORCEMENT PLANNED→SHIPPED→LIVE IN ~26 H (TASK-512, archived).** 3 nav-research agents → console#361/#362 (3a/3b) → PR#363/#364 merged 10-06, console#365→PR#366 + ui#203→PR#204 merged 10-07, all reviewed APPROVE-w-notes, ui PR#204 real-stack verified pre-merge. Nelya set `PILOT_CONSOLE_ALLOWANCE_ENFORCE_ENABLED=true` + `PILOT_CONSOLE_USAGE_POLL_INTERVAL=15m` (infra dc10719); reconciler rev 27 on prod-0.1.15 since 10-07 ~10:20Z; UI live 12a7b46. Learned: console deploy is automatic on main now (mem-202 update); never cancel a deploy run (mem-217); local compose override points at prod SSM (mem-216); evidence runner refuses `|` in `-run` (SOP 5c); cross-repo paths in backticks trip the base-presence hold (SOP 3b). **TASK-513 opened 10-07: real exhaustion on a prod test org** (founder registers org + GitHub token, Navigator provisions + labels issues, Nelya one `set-allowance` command, founder pastes own key; never terminate the org — it retires pool-01). TASK-511 archived.

**Caveat CLEARED 2026-08-26 (was wrong since at least v2.149.4):** the long-standing claim that `gateway.Config.LinearWebhookPublicKey` has no YAML decode is **false** — nav-research verified it is fully wired: `internal/adapters/linear/types.go:20` (`yaml:"webhook_public_key"`) → `internal/pilot/linear_key.go` (PEM/PKIX/Ed25519 parse) → `internal/pilot/pilot.go:492` → `internal/gateway/server.go:126`, with the disabled-path logged at `pilot.go:495`. Ed25519 verification works when the key is configured. The real incident of this shape was **`gateway.Config.Auth` (GH-4784)** — validated + defaulted but both production constructors called the auth-less `NewServer` (memory `unwired-config-field-validated-but-dead`). This entry sat stale for months and was repeated as fact; do not reinstate it without re-grepping.

**Earlier (v2.179.0–v2.187.1, June 9–16 2026):** `pilot project add` gh wizard (TASK-282) · board-GraphQL partial-data tolerance (`ExecuteGraphQLTolerant`) · TASK-322 security audit CLOSED · decomposition-integrity waves 1+2 · hot-upgrade self-verify on boot · executor SHA-harvest fix · `safeGo` panic-recovery sweep · board-orphan defense-in-depth · ancestor-tag release dedup. Detail in `git log` + `.agent/tasks/archive/`.

### Autopilot Environments (v1.59.0+)

The `--env` flag selects a deployment pipeline:

| Flag | CI Wait | Approval | Post-Merge | Use Case |
|------|---------|----------|------------|----------|
| `dev` | Skip | No | none | Fast iteration, trust the bot |
| `stage` | Yes | No | none | CI must pass, then auto-merge |
| `prod` | Yes | Yes | tag | CI + human approval required |

```bash
pilot start --env=stage --telegram --github  # Balanced (recommended)
```

---

## 🚀 Pilot Cloud SaaS Program (TASK-405) — ACTIVE

Building the hosted Pilot SaaS using this daemon to build it (Pilot ships its own SaaS via `pilot`-labeled issues).

- **Plan of record + live status**: [`system/saas-roadmap.md`](system/saas-roadmap.md) (v9.9) — S0 ✅ · S1 ✅ · S2 ✅ (exit met 07-27) · H1–H12 ✅ · R-track ✅ · S6-lite ✅ · **S3 BUILT** (exit gated on founder staging inputs → operator deploy per infra PR#25) · **S4 board: waves 1+2 merged** (C1/C2/C7/C3/C4 + kanban UI) · **wave 3 + UI wave COMPLETE 08-05** (C5 · C6 · C8+fixes · C9 · ui#44/45 · TASK-448 metrics+PR#4739/4741 fixes) · **wave 4 in flight 08-06** (C15 PR#108 ✅ · pilot#4748 C14-pilot + #4749 events endpoint queued · C14-console + timeline legs gated on those merging · close verb dropped as already-built)
- **Program doc**: [`tasks/TASK-405-pilot-saas-platform.md`](tasks/TASK-405-pilot-saas-platform.md)
- **Design**: [`system/saas-architecture.md`](system/saas-architecture.md) · [`saas-kanban-sync-design.md`](system/saas-kanban-sync-design.md) · [`saas-fleet-design.md`](system/saas-fleet-design.md) · [`saas-asset-research.md`](system/saas-asset-research.md)
- **New repos** (created 2026-07-14, in `~/.pilot/config.yaml`): `qf-studio/pilot-console` (Go control plane) · `pilot-console-ui` (Vue3/Vite/Bun SPA) · ~~`pilot-cloud-infra` (Go CDK)~~ **archived 2026-09-23** (estate deleted; fleet infra = Nelya's `aws-infrastructure-pilot`) — each has its own `CLAUDE.md`
- **Latest handoff marker**: `.agent/.context-markers/2026-10-01_console-execution-continue-task502-legs-1-3-4-5.md`
- **Systemic**: TASK-407 atomic dispatch-admission claim — **proven + archived 2026-07-30** ([`tasks/archive/`](tasks/archive/TASK-407-dispatch-admission-claim.md); #4265 closed, `duplicate-pr` green since 07-24). TASK-406 shipped → archived.
- **Ops SOP**: [`sops/operations/safe-daemon-restart.md`](sops/operations/safe-daemon-restart.md) — restart is the operator's action; never relaunch the `--dashboard` daemon from an assistant shell (no single-instance lock yet)
- **Quality SOP**: [`sops/quality/real-stack-verify-gates-ui-merges.md`](sops/quality/real-stack-verify-gates-ui-merges.md) — ADOPTED 2026-07-30: UI-surface merges aren't DONE until operator-verified on the live local stack (daemon gates are fixture-only; 5 drift defects in one night prove it)
- **Incident**: [`system/incident-duplicate-cifix-2026-07-14.md`](system/incident-duplicate-cifix-2026-07-14.md) — the Hardening-track root cause

## Active Work

**Source of truth: GitHub Issues with `pilot` label**

```bash
gh issue list --label pilot --state open
gh issue list --label pilot-in-progress --state open
gh pr list --state open
```

### Backlog

Shipped items live in `git log` + `tasks/archive/` — this table holds **open work only**.
Do not append completed rows here.

| Priority | Topic | Why |
|----------|-------|-----|
| **P1** | **v2.284.0 shipped — autopilot hardening closed; smoke v2 on the tenant** | ✅ **Tagged 10-14 10:13Z at 50f29c745; Release run green on the normal path — `goreleaser` ✅ + new non-fatal `homebrew-tap` ✅ (formula commit 10:16Z) = the #5615 proof.** Box self-upgraded to 2.284.0. Contents: TASK-542 (PR#5669, APPROVE-w-defect) → TASK-547 (PR#5674, APPROVE; no-tag rows back off via a separate soft counter, abandon streak untouched) · TASK-544/548 (PR#5668/#5673, `make lint` 0 issues with golangci-lint 2.14) · TASK-545 (PR#5670, APPROVE-w-notes) · TASK-541 alert (PR#5667). All archived. **Left:** smoke v2 on tenant `i-0289111000cebcee9` once it shows 2.284.0 (chat → card without `.agent/` refs → board In Progress within seconds → Activity rows → Done). |
| **P1** | **Pricing v3 — honest allowance + prepaid overage packs** ([TASK-546](tasks/TASK-546-pricing-v3-honest-allowance-overage-packs.md)) | 🚀 **10-14: waves 1–3 DISPATCHED, price unchanged** — pilot #5676/#5677/#5678 (key source + reported cost + usage rows · chat-turn rows · daily chat cap), console #401/#402/#403/#404 (ledger · tickets-or-USD · daily caps · invites), ui#231 (Members page). Research 10-13: cost +1-4%/ticket nets -$57..-$2 vs +$321 flat; "100 tickets" enforced as $100 (fires ~ticket 32 on Sonnet 5). Deferred until the founder changes the price: packs 25/$99 · 100/$349, $300 ceiling value, copy/catalog. Decisions D1–D11 in the doc. |
| **P1** | **Legacy repo bootstrap — real Navigator context on first attach, persisted, priced** ([TASK-549](tasks/TASK-549-legacy-repo-navigator-bootstrap.md)) | 🚀 10-14: #5679 (bootstrap session, trigger default manual) + #5680 (copy-back) dispatched. Verified: scaffold's injected context sections are placeholders nothing fills; no copy-back from worktrees; chat turns are cold research sessions. Next: cold-start bench (Navigator job), then D1–D3 (auto trigger, console snapshot, 10-ticket price). |
| **P1** | **Pilot SaaS platform** ([TASK-405](tasks/TASK-405-pilot-saas-platform.md)) | S0–S2 ✅ · S3 exit met local-first 08-18 · S4 build complete · **S4 exit path UNBLOCKED 09-21: console-api + reconciler LIVE on Nelya's `pilot-fleet` (ECS, `prod-0.1.0`, factory off)** — the minimal-EC2 route ([TASK-490](tasks/TASK-490-s4-minimal-invpc-console.md)) is superseded by the ECS transfer. **Domain decided `pilotcloud.dev`.** **09-25: first fleet tenant provisioned + shipped twice on the hosted path; board live after enabling the sync workers in prod (infra#14) — S4 exit evidence on the fleet.** Next: **Paddle L7** (sandbox MCP key → $299 price object → live checkout) → console model pin. Email track (TASK-501) shipped, smoked and archived 09-29. |
| **P1** | **Fleet TO-BE alignment (Nelya)** ([TASK-495](tasks/TASK-495-fleet-to-be-alignment-nelya.md)) | ✅ **EXIT EVIDENCE MET 09-25**: reconciler-provisioned tenant `i-0289111000cebcee9` shipped two issues end-to-end; tenant id posted to Nelya for her account-side checklist (Slack draft). Old-estate backup chain verified closed 09-25. Open on her side: none blocking. Ours: infra#16 (replicas=1) via her pipeline = our dispatch. |
| **P1** | **Golden AMI refresh → first fleet tenant** ([TASK-499](tasks/TASK-499-golden-ami-refresh-first-fleet-tenant.md)) | ✅ **L3 DONE 09-25: first fleet tenant provisioned + issue→PR→merge in 4m35s on the hosted path** (defects filed: console#323 repo-switch inert · console#324 worktree parity · pilot#5459 pr_url · pilot#5460 hook cleanup). Prior: L1 ✅ (bake fetches release by version, sha256, version pin, both SSM params) · L2 ✅ `ami-01ecd7cefa1e6f316` pilot 2.276.1 · **L3 BLOCKED**: reconciler redeploy rolled back on Nelya's AZ-rebalancing template (binpack singleton); after her fix: re-run → `tenant_factory=true` (ask founder) → dogfood tenant → Docs real tree. Old AMI kept as rollback. |
| **P1** | **Paddle Billing integration** ([TASK-497](tasks/TASK-497-paddle-billing-integration.md)) | Code complete, L6 smoke passed 09-14. **L7 started 09-29: sandbox key in Doppler, sandbox price $499 `pri_01m3rf7qws3gzscj9fttg4aywe` (decided 09-30).** **Nelya template ask POSTED 09-30 09:57Z** (thread `1790762207.809729`; flag-off gated, values later). **10-09: live $499 twin `pri_01m4g870rh98m207cjwhjn8taq` + live client token created via paddle-live MCP; token in Doppler `prd`.** Next, founder (dashboard): live API key · notification destination (`console.pilotcloud.dev/api/v1/billing/webhook`, `subscription.*` + `transaction.completed`) · submit checkout domain · payment link. Nelya template ask unanswered since 09-30 — nudge. Then point prod at live, readiness audit. |
| — | ~~Jev gate 1 — acceptance classifier~~ ([TASK-505](tasks/archive/TASK-505-jev-acceptance-classifier-shared-client.md)) | ✅ Archived 10-01: live in shadow since 09-30 21:09Z; flip decision ~10-07 from the per-item debug lines. |
| P2 | **Autopilot per-stage deadline + tick-liveness alert** ([#5541](https://github.com/qf-studio/pilot/issues/5541) → PR#5545) | ✅ Shipped 09-30 22:35Z, reviewed 10-01 APPROVE-w-notes. Culprit was `buildScopeMembers` serial GitHub calls (60s budget now). Follow-up [#5547](https://github.com/qf-studio/pilot/issues/5547): deadline errors must not open the per-PR circuit. |
| P3 | **gh-guard audit journals unit-test denials** ([#5542](https://github.com/qf-studio/pilot/issues/5542) → PR#5544) | ✅ Shipped 09-30, reviewed 10-01 APPROVE-w-notes: origin = the model running `go test` in the guarded session (not the quality gates); denial never relaxed; residual WARN count + untested shim-side detection noted. |
| — | ~~Jev gate 2 — base-presence path token~~ ([TASK-506](tasks/archive/TASK-506-jev-base-presence-path-token.md)) | ✅ Archived 10-01: live in shadow since 10-01 09:16Z (v2.276.12). Gate 3 (CI failure class) is the next roadmap item, unfiled. |
| **P2** | **Jev gate 3 — CI failure class** ([TASK-507](tasks/TASK-507-jev-ci-failure-class.md) → [#5555](https://github.com/qf-studio/pilot/issues/5555)) | Dispatched 10-01: choice per failed check on a redacted log tail, shadow first, live override only `code` → `infra`/`infra_billing`. Also queued: [#5553](https://github.com/qf-studio/pilot/issues/5553) test-pin bundle from the 10-01 reviews, [#5554](https://github.com/qf-studio/pilot/issues/5554) 404-eviction test flake, [#5556](https://github.com/qf-studio/pilot/issues/5556) per-item shadow lines at INFO (box never logs DEBUG), [#5557](https://github.com/qf-studio/pilot/issues/5557) credential-shaped span pre-filter + bounded key=value redaction (gate-2 first live miss, nav-research 10-01). Five PRs to review on return; #5555 needs the live smoke. **10-01 pm: #5555→PR#5561, #5556→PR#5562, #5557→PR#5563 merged; all three reviewed 10-01 pm, APPROVE-w-notes (gate 3: 10 mutations caught, live smoke run by the reviewer on the box: code/infra/infra_billing at 1.0). Follow-up [#5565](https://github.com/qf-studio/pilot/issues/5565): gate-3 per-check shadow line still at DEBUG (no flip data until merged).** Also from the reviews: [#5566](https://github.com/qf-studio/pilot/issues/5566) redaction leaks slash-containing secrets to Jev (bug) · [#5567](https://github.com/qf-studio/pilot/issues/5567) test pins · [#5568](https://github.com/qf-studio/pilot/issues/5568) evidence tail truncation + silent Not-verified live smoke. |
| **P1** | **Post-merge CI fix issues borrow the merged PR branch → false delivery / infinite poll** ([TASK-508](tasks/TASK-508-post-merge-fix-borrowed-branch.md) → [#5564](https://github.com/qf-studio/pilot/issues/5564)) | RCA 10-01: 6 post-merge fix issues in 60 days, 1 real fix. Footer carries the merged branch → dispatcher short-circuit marks the task completed with the ORIGINAL PR URL, Claude never runs; issue left open forever (#5551) or closed `pilot-done` as false success (#5560, #5385). Dispatched: A footer omits branch/pr/sha for post-merge · B short-circuit supersedes + closes when the borrowed origin PR is the merged one · C completed rows stop arming repick-backoff. Follow-ups unfiled: flake re-run before filing, ownership check in external-merge close, dedup vs human-filed. **Operator: close #5551 by hand.** |
| **P1** | **Linear Invoices → GitLab cutover** ([TASK-510](tasks/TASK-510-linear-invoices-gitlab-cutover.md); forge half supersedes [TASK-509](tasks/TASK-509-linear-invoices-onboarding.md)) | ✅ **LIVE 10-02 08:46Z on v2.277.1** (cut by hand; the train is daily 16:00 Berlin, the 10-01 "not cutting" note was a misread). [#5583](https://github.com/qf-studio/pilot/issues/5583) per-project `gitlab:` forge + [#5584](https://github.com/qf-studio/pilot/issues/5584) Linear OnPRCreated controller fix merged (PR#5585/#5586 **reviewed 10-02, APPROVE-w-notes**; follow-up [#5589](https://github.com/qf-studio/pilot/issues/5589) epic PR path; [#5588](https://github.com/qf-studio/pilot/issues/5588) poller retry; sdk#144 Linear UUID). Box: PAT + GitLab clones + Linear polling on; both GitLab `main` locked to MR-only; GitHub mirrors frozen. Founder scope: configure only, no tickets labelled by Navigator. Merges stay manual (GitLab `main` → prod on `prod-*` tags). |
| **P1** | **Included token volume — platform key, metering, own-key overage** ([TASK-502](tasks/TASK-502-included-tokens-platform-key.md)) | ✅ **LEGS 0+1+2+4 LIVE 10-06.** Leg 1 key pool: console PR#358/#359/#360 merged + reviewed; SSM + reconciler wired (Nelya infra 79a4cc4); console redeploy 37352817795 green; pool import on console-reconciler:23 → `status` free 5 / assigned 0 / retired 0. First pool assignment = a TEST org only. Leg 3 shipped 10-06 as TASK-512 (console PR#363/#364, live in dry-run). Next: leg 5 copy (moves with the Paddle catalog); WIF = leg 1d later. Org credits prepaid $9.57, auto-reload off (founder deferred). |
| ~~P1~~ | **Real allowance exhaustion on a prod test org** ([TASK-513](tasks/archive/TASK-513-allowance-exhaustion-prod-test.md), TASK-502 close-out) | ✅ **DONE 10-08** — both branches proven on prod (own-key switch; no-key suspend → EC2 stop → own-key save → resume in 36 s → PR on the own key). 3 prod defects fixed on the way (console#367/#369, pilot#5622) + AMI `make`. 8 gap issues filed (ui#205–207, console#371–374, sdk#146). |
| **P1** | **Allowance enforcement at exhaustion — own-key switch, suspend without one, per-period state** ([TASK-512](tasks/archive/TASK-512-allowance-enforcement-leg3.md), TASK-502 leg 3) | ✅ **DONE 10-07, archived.** console#361/#362/#365 → PR#363/#364/#366, ui#203 → PR#204; all reviewed; enforcement live (reconciler rev 27, prod-0.1.15, flag on, 15m poll); UI live 12a7b46. Open under TASK-502: one real exhaustion on a test org. |
| **P1** | **console-ui included allowance — Plan & Billing card, exhausted state, own-key prompt, provision gating** ([TASK-511](tasks/archive/TASK-511-console-ui-included-allowance-leg4.md), TASK-502 leg 4) | ✅ **MERGED + REVIEWED + LIVE 10-05**: ui#197/#198/#199 → PR#200/#201/#202, post-merge APPROVE-w-notes, auto UI deploy at build 07f57a7. **Real-stack verified 10-06** on the local stack: normal / exhausted-no-key / exhausted-with-key, Connections pool row, provision gating github-only. ✅ DONE, archived 10-06. |
| P2 | **Console Docs page — live verification** ([TASK-466](tasks/TASK-466-console-docs-page.md)) | Page renders through the edge (09-22 founder login) but the console DB has no tenant yet → the real `.agent`-tree proof is TASK-499 L3's acceptance (first fleet tenant). infra#51/TASK-498 closed superseded. |
| P2 | **pilot-docs → GitHub + AWS deploy** ([TASK-492](tasks/TASK-492-pilot-docs-gitlab-to-github-migration.md)) | ✅ Cutover done by Nelya 09-05; TASK-494 sync fix DONE + reviewed 09-06 (GitHub-only, preserves pilot-docs `.github/`). **Remaining = step 4 operator:** delete `GITLAB_SSH_KEY` secret · drop `gitlab:` block in hosted config · archive `quant-flow/pilot-docs`. Nelya owes: compression + CSP-RO answer. |
| **P1** | **Console rail implementation** ([TASK-478](tasks/TASK-478-console-rail-implementation.md)) | 11 approved designs → shipped surfaces. **Build-out COMPLETE 08-15 (overnight run): all 16 autopilotable legs executed + reviewed.** Blocked on founder morning sequence (approve PR#67→72→74→76 · close #73/#77 to arm retries · label ui#78 after) → then GH-69/GH-75 retries re-land · **real-stack verify batch UI-2..12** (SOP; blocked on GH-75 re-land) · CON-5 billing portal (founder Stripe gate) · copy pass ($299 · PR#72 "Includes" line · support@ mailto). Daemon-side follow-ups FILED 2026-08-20: [pilot#5027](https://github.com/qf-studio/pilot/issues/5027) merge-time ancestry check (stacked-superset guard, extends GH-4872) + [pilot#5028](https://github.com/qf-studio/pilot/issues/5028) base-presence check before claim (see pitfall `sequential-gates-on-execution-not-merge-fastfollow-misbase`; 4 family incidents in 6 days, nav-research verdict: both fixes needed). |
| **P1** | **Throughput acceleration** ([TASK-393](tasks/TASK-393-throughput-acceleration.md)) | Phase 1 (instrumentation) ✅ shipped 07-09. **M3 baseline window closed ~07-20 — histograms never harvested; phases 2–5 remain gated on that analysis.** Remaining: (2) execution lanes on `Complexity`, (3) N-concurrent per repo (`ProjectWorker` pool — note this is also the sole serialization point, see mem-101/102), (4) SHA-keyed repo primer, (5) risk-score trust tiers. Roadmap: [`throughput-roadmap.md`](system/throughput-roadmap.md) (M0–M8, D1–D6). |
| P2 | **Review-feedback trigger hardening** ([TASK-493](tasks/TASK-493-review-trigger-hardening.md)) | ✅ SHIPPED 09-06 in v2.273.0 (PR#5331–5334 via #5314); post-merge review APPROVE-w-notes → follow-up [#5337](https://github.com/qf-studio/pilot/issues/5337) (HIGH re-adoption cutoff blind spot). Also filed [#5336](https://github.com/qf-studio/pilot/issues/5336): autopilot CI-fix issues deadlock on `Depends on:` an open superseded original. From external [#5228](https://github.com/qf-studio/pilot/issues/5228): feature (bot/`COMMENTED` triggers) **DECLINED — security by design** (`pilot-never-reads-gh-comments-by-design`); its two real bugs taken: webhook path has no bot filter · reviews yank PRs out of `awaiting_approval`. Plus identity-based exclusion via `getBotLogin` and human-only revision-issue body. No config, no dashboard change. |
| **P1** | **Hosted retry path for failed executions** ([TASK-485](tasks/TASK-485-hosted-retry-path-failed-executions.md), [#5008](https://github.com/qf-studio/pilot/issues/5008)) | Daemon legs SHIPPED+REVIEWED 08-25 (PR#5214 classifier · PR#5215 stalled re-arm sweep · PR#5220 streak alert) — ride the 08-26 v2.270.0 train. **Remaining: Leg 3** (console repo: C8 dispatch on failed/stalled card cycles trigger label + removes `pilot-blocked`) **after the train lands on the box**, then **Phase 4** live validation on ship-test-js#6 (expect ≤16min re-arm latency — repick backoff gate). |
| — | ~~Wire `linear.webhook_public_key` YAML~~ | **REMOVED 2026-08-26 — the premise was false.** Verified fully wired end-to-end (see the cleared caveat above). Nothing to do. |
| P1 | Web dashboard polish | React UI functional but needs a design pass. |
| P2 | Delivery-evidence audit — false-success class ([TASK-460](tasks/TASK-460-delivery-evidence-false-success.md)) | Split from TASK-459 by founder scope call 08-08: green CI is not proof the requested change shipped (`mem-151`: scaffold-only PR merged green, parent auto-closed, zero requirements delivered). Planned, NOT dispatched; TASK-459 Phase 4's inventory hook feeds it the success-side site rows. Candidate legs: diff-surface check · ACs fail-when-unwired · epic-collapse guard. |
| P2 | E2E test suite | No integration tests — reliability untested. |
| P2 | Web dashboard auth | Token-based auth for remote access. |
| P2 | Mobile-responsive dashboard | Primary use case is phone access. |
| P3 | GitHub App auth | PAT → installable GitHub App. |
| P3 | Audit §3 Wave 4+ candidates | Not yet decomposed: `RecordAPIError` wiring beyond github · `AlertTypeOOMKilled` · multi-gate scanner phase discipline · subprocess migration end-to-end validation · `autopilot` adapter coupling refactor · SQL `withTx` helper · generic `Poller[T]` extraction · `Releaser` frozen-at-startup fix. Source: `.agent/audits/AUDIT-2026-05-25.md` §3. |

**Operator-parked (not autopilotable):** ~~restart the hosted daemon~~ **DONE 09-07 09:18Z** — box rebuilt from main (`v2.273.0-23-ge054b01c`, carries #5339–#5347) and restarted; `orchestrator.receipts_digest` active (scheduler started, catch-up digest for 09-06 delivered to Telegram 283716179; next 18:00 Europe/Berlin). daily_brief still on America/New_York (arrives 14:00 CEST). ~~`PILOT_DOCS_PAT` workflow scope~~ obsolete since TASK-494 (sync never writes `.github/`) · **domain pick** (`pilot.build` premium $720/yr · `pilot.engineering` $83 · `pilothq.dev` ~$15; = OIDC issuer, sticky) · branch protection on `qf-studio/pilot` main (TASK-405 founder decision 7 — main is currently unprotected) · EBS restore DRILL (runbook exists at pilot-cloud-infra `docs/RESTORE-RUNBOOK.md`; the drill itself is operator work) · tenant box `i-0a3bf271d598196ca` still on **2.259.3** (predates TASK-485 daemon legs — fleet images are immutable by invariant, rolling-upgrade machinery is console#216; operator binary swap is the interim for Phase 4) · rotate ALL box tracker/API tokens (founder-planned; Jira token exposed in a 08-26 session) · infra#2 Golden AMI v2 (stale claim corrected 08-26: `aws-infrastructure-pilot` IS in the box config — issue itself needs re-triage) · console#45 (`pilot-spec-incomplete`/`blocked` since 07-24 — needs rewriting into an implementable spec). NOTE 08-26: infra PR#27 `cdk deploy` DONE at some point — FleetVpc NAT verified at 1, `Environment=fleet` tag live in cost view.

---

## Project Structure

```
pilot/
├── cmd/pilot/           # CLI entrypoint
├── internal/
│   ├── gateway/         # WebSocket + HTTP server
│   ├── adapters/        # Linear, Slack, Telegram, GitHub, Jira
│   ├── executor/        # Claude Code process management + alerts bridge
│   ├── alerts/          # Alert engine + dispatcher + channels
│   ├── memory/          # SQLite + knowledge graph
│   ├── config/          # Configuration loading
│   ├── dashboard/       # Terminal UI (bubbletea)
│   └── testutil/        # Safe test token constants
├── orchestrator/        # Python LLM logic
├── configs/             # Example configs
└── .agent/              # Navigator docs
```

## Key Files

### Gateway
- `internal/gateway/server.go` - Main server with WebSocket + HTTP
- `internal/gateway/router.go` - Message and webhook routing
- `internal/gateway/sessions.go` - WebSocket session management
- `internal/gateway/auth.go` - Authentication handling

### Adapters
- `internal/adapters/linear/client.go` - Linear GraphQL client
- `internal/adapters/linear/webhook.go` - Webhook handler
- `internal/adapters/slack/notifier.go` - Slack notifications
- `internal/adapters/slack/socketmode.go` - Socket Mode client + Listen()
- `internal/adapters/slack/events.go` - Event types + envelope parsing

### Executor
- `internal/executor/runner.go` - Claude Code process spawner with stream-json parsing + slog logging
- `internal/executor/alerts.go` - AlertEventProcessor interface (avoids import cycles)
- `internal/executor/progress.go` - Visual progress bar display (lipgloss)
- `internal/executor/monitor.go` - Task state tracking

### Alerts
- `internal/alerts/engine.go` - Event processing, rule evaluation, cooldowns
- `internal/alerts/dispatcher.go` - Multi-channel alert dispatch
- `internal/alerts/channels.go` - Slack, Telegram, Email, Webhook, PagerDuty
- `internal/alerts/adapter.go` - EngineAdapter bridges executor to alerts engine

### Dashboard
- `internal/dashboard/tui.go` - Bubbletea TUI with token usage, cost, task history

### Memory / Testing
- `internal/memory/store.go` - SQLite storage
- `internal/memory/graph.go` - Knowledge graph
- `internal/testutil/tokens.go` - Safe fake tokens for all test files

## Development Workflow

**Default: release then upgrade — don't run ad-hoc local builds.**

```bash
make test
make fmt && make lint
```

**Cycle-gated exception (2026-07-10):** to run merged-but-unreleased `main`
on the daemon *without* cutting a release (release cycles hold work for the
16:00 train), build from a **detached worktree at `origin/main`** and install
to the daemon's path — NOT the root, NOT `make install` (~/go/bin), NOT brew:

```bash
git worktree add --detach /tmp/pilot-build origin/main
cd /tmp/pilot-build && make build          # bin/pilot, version stamped from git describe
cp -p ~/.local/bin/pilot ~/.local/bin/pilot.bak-<rev>   # rollback
cp bin/pilot ~/.local/bin/pilot            # daemon runs ~/.local/bin/pilot (mem: binary path)
git worktree remove --force /tmp/pilot-build
# restart daemon in the zellij `pilot` pane: pilot start --dashboard --github --telegram --tunnel --replace
```

Config is external (`~/.pilot/config.yaml`) — the new binary shares it
unchanged. Building never releases (release = tag push only). Verify the
running binary with `go version -m ~/.local/bin/pilot | grep -E 'main.version|vcs'`.

## Release Workflow

```bash
# Tag-only: GoReleaser CI handles the rest
git tag v0.X.Y && git push origin v0.X.Y

# Upgrade to new version
pilot upgrade
```

**Fresh Install:**
```bash
curl -fsSL https://raw.githubusercontent.com/qf-studio/pilot/main/install.sh | bash
```

**Known Issue (GH-204):** Install script doesn't auto-configure PATH. Users must add `~/.local/bin` to PATH or open new terminal.

## Configuration

Copy `configs/pilot.example.yaml` to `~/.pilot/config.yaml`.

Key per-adapter env vars:
- `GITHUB_TOKEN` - GitHub polling + PR creation
- `LINEAR_API_KEY` - Linear webhook adapter
- `SLACK_BOT_TOKEN` - Slack Socket Mode adapter
- `TELEGRAM_BOT_TOKEN` - Telegram adapter

## CLI Flags

### `pilot start`
- `--env=ENV` - Enable autopilot mode: `dev`, `stage`, `prod`
- `--dashboard` - Launch TUI dashboard with live task monitoring
- `--telegram` - Enable Telegram polling
- `--github` - Enable GitHub polling
- `--slack` - Enable Slack Socket Mode
- `--daemon` - Run in background
- `--sequential` - Wait for PR merge before next issue (default)

## Documentation Loading Strategy

1. **Every session**: This file
2. **Feature work**: Task doc in `.agent/tasks/`
3. **Architecture changes**: `.agent/system/ARCHITECTURE.md`
4. **Integration work**: Relevant adapter code
