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

**Current Version:** **v2.291.0** cut OUT-OF-BAND 10-21 11:31Z (tag on `808bba8b2`; Release + homebrew-tap + Docker green); box hot self-upgraded (board ver=2.291.0). Contents since v2.290.0: #5782 sweep log lines carry `repo`, empty-train skip at Info · #5785 queue panel grouped by project (3×3, `+N projects`) · #5786 epic-parent pass deadline race (timeout counted when a reconciler honors ctx). v2.290.0 (10-20): TASK-576 outbound messaging #5763–#5768 · #5769 auto-preserve lease-push · #5775 stale `pilot/*` branch sweep · #5778 one `failureInScope` predicate · #5779 `ListBranches` single request.

**PRIORITY (founder directive 2026-07-26 — supersedes 07-17):** **SaaS/platform UNPARKED — TASK-405 is active work again.** The 07-17 ordering (pointer delivery → pilot reliability → SaaS parked) held while the dispatch-reliability chain was open; that chain closed with v2.246.0 on 07-25. Pointer and pilot reliability remain live tracks but no longer gate S-milestone dispatch. Memory: `founder-priority-pointer-first-saas-parked` (superseded).

**Recent (Oct 12 – Oct 19 2026; detail lives in `system/saas-roadmap.md`, `system/side-chat-navigator.md`, `tasks/archive/`, memories and git log — do not re-grow this block, replace it):**
- **10-20 am: #5770 UN-PARKED (OUR OWN BASE-PRESENCE MISS) · CONSOLE#390 PREMISE DEAD, RE-SCOPED + DISPATCHED · GOLDEN-AMI GAP FOUND.** [#5770](https://github.com/qf-studio/pilot/issues/5770) (TASK-577) sat `pilot-needs-human` 11 h: the task doc backticked the two new files it asks for → gate hold → park (pitfall `issue-body-backticked-paths-not-on-main-trip-base-presence-hold`, 8th). Seven tokens → prose, label off. [console#390](https://github.com/qf-studio/pilot-console/issues/390): nav-research + two live checks (GH-5651 first tag **v2.282.0**; tenant `i-0289111000cebcee9` on **2.289.0**, hot self-upgraded 10-19 14:06Z) killed the "train never reaches tenants" premise; founder 10-13 decision stands (daemon self-upgrade = tenant path). Re-titled + re-scoped to **observed Pilot version per tenant** (`/health` in the existing ready probe → migration 0030 `observed_pilot_version` → `consolectl status` VERSION → floor warning `PILOT_CONSOLE_FLEET_MIN_PILOT_VERSION`), 701 words, gate-clean, labeled `pilot`+`no-decompose`. **New infra gap:** reconciler AMI `ami-06825978577ce40d4` bakes pilot **2.277.4** (< v2.282.0), no S3 override → a tenant provisioned today never self-upgrades until one SSM hop. Needs an AMI refresh in `aws-infrastructure-pilot` (not filed yet). SOP `tenant-binary-upgrade-ssm.md` re-headed as LEGACY. Memory `verify-issue-premise-against-live-fleet-before-dispatch`. **Reviews 10-20 09:xx:** [PR#5775](https://github.com/qf-studio/pilot/pull/5775) (#5770 sweeper) merged 08:23Z, post-merge **APPROVE-w-notes** → D1 `ListBranches` paginates `matching-refs`, which ignores `per_page` → [#5777](https://github.com/qf-studio/pilot/issues/5777). [console PR#417](https://github.com/qf-studio/pilot-console/pull/417) (#390) **REQUEST-CHANGES** (wire-contract test missing + snake_case json tags; fleet side sound), parked `pilot-needs-human` by a daemon bug: GH-5468 fails the gate on unlisted checks but evidence collectors still allowlist-scope → zero evidence → [#5776](https://github.com/qf-studio/pilot/issues/5776) (`pilot`); box mitigation = per-project `ci_checks.required_checks: []` for the 3 console projects. [infra#23](https://github.com/qf-studio/aws-infrastructure-pilot/issues/23) golden-AMI refresh filed, but the box does not poll that repo → route to Nelya or add the project. **PR#417 hand-fixed 10-20 08:50Z** (founder call): camelCase tags + `TestHandleListObservedPilotVersionJSON`, pushed `94e2bea`; autopilot re-adopted (redrive 1/2), `test` flaked (shared-Postgres TRUNCATE race, memory `console-ci-shared-postgres-truncate-races-instances-e2e`), size guard re-parked it, rerun → all 5 checks green → **squash-merged by hand 09:29Z (`f3c8555c1`), #390 closed**; next: deploy + `consolectl status` shows `2.289.0`. infra#23 **handed to Nelya 10:05 CEST** (thread ts `1792489082.804169`); the box does not poll `aws-infrastructure-pilot`. **Both follow-ups shipped + post-merge reviewed before noon:** [#5776](https://github.com/qf-studio/pilot/issues/5776) → [PR#5778](https://github.com/qf-studio/pilot/pull/5778) merged 09:10Z, **APPROVE-w-notes** (one `failureInScope` predicate for gate + 3 collectors, both mutations caught; stale doc comment only) · [#5777](https://github.com/qf-studio/pilot/issues/5777) → [PR#5779](https://github.com/qf-studio/pilot/pull/5779) merged 09:27Z, **APPROVE** (single request + dedupe, request count asserted, 3 mutations caught). All three (#5775/#5778/#5779) ride v2.290.0 at 14:00Z. **Train landed 14:10Z (hot restart); post-train config applied 15:04Z** (backup `config.yaml.bak-20261020-train290`): `lifecycle_notifications: true` · `stale_branch_sweep: true` · `required_checks: []` on the 3 console projects; **restarted 15:06Z, verified 15:09Z** (1 proc, 2.290.0, queue 0, Slack ingress OK, no lifecycle WARN). **First sweep deleted 46 orphaned `pilot/*` branches across 10 projects, 0 errors; all repos now at 0 `pilot/*` refs.** No open founder calls on this line.
- **10-15→10-17: EXECUTOR FAST-FOLLOW TRACK — 8 REVIEWS, 7 ISSUES, ONE RE-PICK LOOP ([TASK-560](tasks/archive/TASK-560-adoption-finalizer-all-gate-exits.md)…[573](tasks/archive/TASK-573-selfclose-handoff-marks-original-superseded.md)).** Post-merge reviews of the #5712 wave found defects in PR#5713 (adoption unfinished on 4 gate exits), #5714 (strip HEAD-only, settings lost under hooks-off) and #5717 (`To https://` header on Linear, `branch_pushed` after the terminal status) → TASK-560/561/568 → #5718/#5719/#5720 shipped same evening (PR#5722/#5723/#5728, reviewed APPROVE-w-notes/-defects). Their reviews → TASK-569/570 → #5731/#5732 (PR#5737 after a lint red, PR#5736) → TASK-571/572 → #5738/#5739 ([PR#5740](https://github.com/qf-studio/pilot/pull/5740) 12:35Z · [PR#5742](https://github.com/qf-studio/pilot/pull/5742) 13:01Z; both reviewed 10-17: APPROVE-w-notes / APPROVE-w-defects — the runner call site is untested (pin survives) and `navBootstrapAttempted` is keyed per worktree → [TASK-574](tasks/archive/TASK-574-bootstrap-callsite-test-and-attempt-guard-key.md) → [#5745](https://github.com/qf-studio/pilot/issues/5745) → PR#5750 merged 10-19 10:38Z, reviewed APPROVE-w-notes (runner subtest lookup count not isolating; no follow-up); [571](tasks/archive/TASK-571-coauthor-strip-no-origin-warn-head-only.md)/[572](tasks/archive/TASK-572-navigator-bootstrap-gate-clone-path.md) archived). **Incident 10-16 14:13–15:34Z:** the autopilot fix chain self-closed PR#5733 and left #5731 re-pickable; the dispatcher re-ran GH-5731 twice into the fix run's branch (rejected push → `infra` → re-pick without cap); stopped by hand (label off, PR#5737 `Closes #5731`) → [TASK-573](tasks/archive/TASK-573-selfclose-handoff-marks-original-superseded.md) → #5741 → [PR#5743](https://github.com/qf-studio/pilot/pull/5743) merged 10-17 13:35Z, reviewed 10-19 APPROVE-w-notes (closed original keeps `pilot` labels — `owner_death.go` returns on closed before the label strip; supersede on a still-`running` row is a silent no-op → [TASK-575](tasks/archive/TASK-575-selfclose-supersede-running-row-and-closed-original-labels.md) → #5747 → PR#5751 merged + reviewed 10-19). The Slack approve click for PR#5737 never reached the daemon; decision relayed via the box's local `/api/v1/approvals/{id}/decision` (memory `slack-approval-click-not-received-relay-via-local-decision-api`). Base-presence holds #6/#7 (example path, `~/.pilot/config.yaml`) → mechanical path probe before every `gh issue create`, zero holds since. Memories: `autopilot-selfclose-handoff-leaves-original-task-repickable`, `infra-repicks-bypass-hard-cap-backoff-and-identical-failure-streak`, `rev-list-without-topo-order-breaks-oldest-first-reparent`.
- **10-19: APPROVAL ROUTING HARDENED + OUTBOUND MESSAGING MAPPED ([TASK-576](tasks/TASK-576-outbound-messaging-gaps.md)).** Two external reports (scrappydog) verified by nav-research and shipped same day, each post-merge reviewed with a comment on the PR: [#5716](https://github.com/qf-studio/pilot/issues/5716) github-review approvals checked only the default repo — the worse half was a **false approval** when the default repo's PR #N had an approval → PR#5746 (per-request owner/repo, fail closed); [#5699](https://github.com/qf-studio/pilot/issues/5699) epic sub-issues ignored `default_branch` → PR#5748. Follow-ups: [#5749](https://github.com/qf-studio/pilot/issues/5749) → PR#5752 (`HasApprovalReview` needs an open PR + approval on the head SHA); [#5753](https://github.com/qf-studio/pilot/issues/5753) → PR#5754 (`approvers_by_channel` + `projects[].approval.approvers`, so Slack/Telegram mixed routing works); [#5755](https://github.com/qf-studio/pilot/issues/5755) Telegram channel-first → PR#5768 (same evening). **Evening: all 5 TASK-576 legs + #5755 merged and post-merge reviewed (PR#5763–#5768, 16:37→19:00Z)**; leg A's GH-5756 looped 6× on a stale auto-preserve branch → executor bug [#5762](https://github.com/qf-studio/pilot/issues/5762) dispatched same evening → PR#5769 merged 20:24Z (reviewed APPROVE-w-notes: lease-push only over the run's own auto-preserve SHA, escalate on any other non-FF); a GitHub Actions incident tripped the platform breaker once (held, re-driven, merged). Box steps wait for v2.290.0. **Evening hygiene (two side sessions):** 96 finished task docs archived (`df55954af`, active docs 125→30); branch audit deleted all 73 stale remote `pilot/*` branches with per-round founder approval (recovery SHAs in the audit's `remote-evidence.tsv`; autopilot already deletes merged-PR branches — the orphans were no-PR / closed-PR pushes) → [TASK-577](tasks/archive/TASK-577-orphan-pilot-branch-sweeper.md) opt-in sweeper dispatched as [#5770](https://github.com/qf-studio/pilot/issues/5770). Memory: `github-events-api-undercounts-multi-ref-delete-pushes`. Founder box unaffected throughout (Slack approvals, `adapters.github.approval: null`, all `default_branch: main`). nav-research then mapped every outbound path (approvals, alerts, task lifecycle, PR notices, briefs, chat) → 5 gaps → TASK-576 legs #5756–#5760 chained by risk. Memories: `approval-no-handler-returns-success-wall-clock-applies-default-action`, `autopilot-notifier-never-wired-pr-notices-never-sent`, `pr-numbers-collide-across-repos-approval-must-key-on-owner-repo`, `approver-identity-is-per-channel-approvers-by-channel`, `box-slack-socket-mode-config-false-but-socket-mode-starts`, `task-to-graph-rewrites-graph-json-with-unicode-escapes`.
- **10-16: ORG INVITES LIVE END TO END — first real invitee joined 12:51Z.** The TASK-546 wave closed: console#403 daily caps ([TASK-562](tasks/archive/TASK-562-console-403-rebase-daily-caps-onto-402.md), PR#408 10:00Z, review APPROVE-w-notes) and console#404 invites ([TASK-564](tasks/archive/TASK-564-console-404-wire-test-and-migration-renumber.md), PR#406 10:49Z) unblocked by continuation issues; the runner's swallowed non-fast-forward push found on the way → [TASK-563](tasks/archive/TASK-563-executor-push-rejection-swallowed-as-success.md) / PR#5730 (rides the 16:00 train). Invites needed three more legs the same morning: infra PR#22 (`PILOT_CONSOLE_INVITE_BASE_URL`, [TASK-565](tasks/archive/TASK-565-infra-console-api-invite-base-url.md), console-api rev 57), the UI accept page ([TASK-566](tasks/archive/TASK-566-ui-accept-invite-page.md), ui PR#236) and invite-aware registration ([TASK-567](tasks/archive/TASK-567-ui-register-with-invite-skips-org.md), ui PR#238 — the smoke found that registration always created an org, so an invitee could never accept). Smoke: owner invited a plus-address → 201 + SES delivered → invitee registered through the link (no org field) → accept 200 → `org_members` row `member`, `org_invites.accepted_at` set. Memory `executor-swallowed-rejected-push-as-success-branch-exists-is-not-pushed`.
- **10-15: LINEAR NEVER MOVED TICKET STATE — FOUND, FIXED, LIVE SAME DAY ([TASK-557](tasks/archive/TASK-557-linear-native-state-write-back.md)).** nav-research: Linear leg was labels + start comment only, `TransitionState`/`UpdateIssueState` had zero callers (nine `LIN-QF-*` issues with MRs still Backlog); Jira fine via SDK category fallback; GitLab/Azure/Asana same class. Three PRs (#5702 → #5704 → #5706, each reviewed, pins killed) in **v2.287.0**; live proof QF-301/302 15:06–15:25Z. The #5701 executor run stalled with the full work uncommitted (session backgrounded `go test`, ended its turn, killed after the GH-5530 grace, auto-preserved) → Navigator verified + opened PR#5702 by hand; pitfall + [#5709](https://github.com/qf-studio/pilot/issues/5709). Box: project go.mod bumped to Go 1.26.9 broke every LIN gate 13:24Z → founder installed 1.26.9 14:41Z, `GOTOOLCHAIN=auto` in the wrapper as a net. Also filed #5710 (copy-back vs `navigator:false` + tripwire), #5711 (co-author trailer). **Operator: rotate Slack bot/app tokens (exposed in a session transcript).**
- **10-15: v2.286.0 RELEASED OUT-OF-BAND (09:42Z) — box 09:45Z, tenant 09:48Z, Release run green incl. `homebrew-tap`.** Contents: usage route `kind` + chat rows (TASK-553), write-boundary guard (551/555), worktree + chat + lint + autopilot follow the project default branch (external PR#5620 by sandeepraju, APPROVE, + TASK-556), hermetic bootstrap tests (552). **Afternoon: TICKET LEDGER PROVEN END TO END + FOUNDER TENANT METERED.** The post-release ledger check found the console's first poll omitted `since` and the daemon answered 400 every 15 min since 10-14 (cursor deadlock; the test fake accepted an empty `since`) → [TASK-558](tasks/archive/TASK-558-console-ledger-first-poll-sends-since.md) → console#411 → PR#412 merged 11:44Z, reviewed APPROVE-w-notes (reviewer ran the DB-gated tests + pin), prod-0.1.33 11:59Z; `ticket_ledger` holds execution + chat_turn rows by 12:55Z. The founder tenant then recorded `key_source=unknown` (09-25 SSM layout, no `PILOT_ANTHROPIC_KEY_SOURCE`): fixed by hand 15:15Z (String param + idle restart), proven `own` in the ledger 15:26Z, and the console gap closed by [TASK-559](tasks/archive/TASK-559-console-own-key-save-writes-selector.md) → console#413 → PR#414 merged 15:58Z (recovery PR from Pilot's preserved commit — executor-ends-turn-with-background-test pitfall, 2nd instance today). Memories: `test-fake-daemon-more-permissive-than-real-route-hides-400`, `founder-tenant-legacy-ssm-layout-key-source-unknown-unmetered`; base-presence hold recurrence #5.
- **10-14: SMOKE v2 ON THE TENANT 5/5 AFTER ONE FIX · OAUTH ROTATED · USAGE CONTRACT DRIFT FOUND.** Smoke: chat→card 40 s, File → pilot-ship-test-go#9 (zero `.agent/` refs), In Progress <1 min, PR#10 merged 4m26s — then the board went blank on the first `pr_merged` row (ui wire mapper had no case; [TASK-550](tasks/archive/TASK-550-ui-board-activity-mapper-pr-merged-blank-board.md) → ui PR#234, live 65 min after found). Box Claude OAuth token rotated + CLI 2.1.104→2.1.299 (SOP `sops/operations/box-claude-oauth-token-rotation.md`). PR#5683 review found `--allowedTools` inert under skip-permissions → TASK-551/555; nav-research on the #5677 rebase failure found console PR#405 and daemon GH-5676 built to different wire shapes (ledger ingested zero rows) → [TASK-553](tasks/archive/TASK-553-usage-route-kind-and-chat-rows-supersedes-5677.md)/[554](tasks/archive/TASK-554-console-ledger-decode-daemon-usage-shape.md). Memories: `allowedtools-inert-under-dangerously-skip-permissions`, `console-ledger-poller-decoded-assumed-usage-shape-zero-rows`, `issue-body-backticked-paths-not-on-main-trip-base-presence-hold`, `evidence-runner-pastes-nonzero-exit-under-passes-bullet`.
- **10-14: PRICING V3 + LEGACY BOOTSTRAP DISPATCHED, PRICE UNCHANGED ([TASK-546](tasks/TASK-546-pricing-v3-honest-allowance-overage-packs.md), [TASK-549](tasks/TASK-549-legacy-repo-navigator-bootstrap.md)).** 10-13 research (nav-research on 4 repos + nav-deep-research, 47 sources, 11 graph memories): founder's cost+1-4%/ticket rejected (nets -$57..-$2 vs +$321 flat; Paddle 5%+$0.50 > markup); "100 tickets" is enforced as a $100 cap; chat turns are unmetered and uncapped per org; an org is one person (no invites); legacy repos run every ticket cold (placeholder scaffold, no copy-back). 10-14: ten issues filed across pilot/console/ui for metering, caps, invites, bootstrap; packs/copy/$300 deferred to a price decision. TASK-547 (#5671 → PR#5674) reviewed APPROVE and archived after an overnight `pilot-needs-human` park caused by the dispatch commit archiving the TASK-542 doc it cited. **`product/LEGAL-TERMS.md` written** as the source of truth for the site's `/terms` `/refunds` `/privacy` and licence summary (TASK-515 S2); four `[FOUNDER]` fields + lawyer review open; the 90-day small-org sunset is a proposal, not in `LICENSE`.
- **10-20 pm: FOLLOW-UPS SHIPPED, CONSOLE TEST-DB FLAKE CLOSED, QUEUE PANEL GROUPED.** [#5781](https://github.com/qf-studio/pilot/issues/5781) → PR#5782 merged (sweep logs carry `repo`, empty-train skip at Info; review APPROVE-w-notes: Info also fires on every empty daily tick). Its post-merge CI red was a pre-existing race in the epic-parent pass deadline accounting (`TestEpicParentPass_DeadlineLogsAndCounts`) → autopilot #5784 → PR#5786 (production change in `controller.go`, unreviewed). [console#418](https://github.com/qf-studio/pilot-console/issues/418) → PR#419 per-package test databases: held as draft, two revisions ([TASK-578](tasks/archive/TASK-578-console-419-revision-test-db-lock.md) → console#420, [TASK-580](tasks/archive/TASK-580-console-419-revision-2-scratch-migrate-lock.md) → console#421) after a local `-count=3` reproduced `tuple concurrently updated` (migration 0014 `ALTER ROLE` from unlocked scratch-DB migrations); final: every test migration under one base-DB advisory lock, CI green 3/3 on fresh Postgres, merged 17:37Z. [TASK-579](tasks/archive/TASK-579-dashboard-queue-grouped-by-project.md) → #5783 → PR#5785: queue panel grouped by project (3 × 3, `+N projects`, dim header with phase/age, finished rows `run · ago`, `TaskDisplay` timestamps, selection by ID), review APPROVE. Lessons: the executor box has no Postgres, so Pilot's DB-test evidence is invalid — verify on CI reruns; nav-task ID generator ignores `tasks/archive/` (returned the archived TASK-577).
- **10-12→10-19: PILOTCLOUD.DEV SITE MERGED, HOSTING LIVE, DEPLOY WORKFLOW = NELYA'S PR, RUNNER-GROUP GRANTED ([TASK-515](tasks/TASK-515-pilotcloud-landing-and-legal-pages.md)).** Private repo `pilotcloud-site`: scaffold (PR#3), landing (PR#4), product pages (PR#6), legal pages (PR#8), install + licence copy (PR#9); CI builds only. **I1 delivered 10-17** (Nelya, `#infrastructure` thread `1791555910.941859`): bucket `pilot-fleet-s3-site`, distribution `E39M9CANDXR187`, apex+www, console edge WAF, www→apex 301, `/path`→`/path/index.html`, `/404.html` mapping, placeholder 200. Founder 10-19: Nelya writes the deploy workflow; our sync facts posted 10:51 (ts `1792402284.706689`). **Her 20:39 reply (ts `1792435192.787699`)**: workflow ready, "attached" (order: `_next/` first no-delete → pages 300 s `--delete` → invalidate `/*` + wait → `_next --delete`; edge checks `/`+`/refunds` 200, build-sha, 404, www 301; runner label `aws-pilot-fleet-deployer`); docs **option A** confirmed, the 301 keeps path + query. **The attachment is unreachable from here** (Slack connector = text only; nothing on GitHub) → reply 22:43 (ts `1792442625.018579`): push it as a PR to `pilotcloud-site`, she is collaborator `nelyaparfenova-dev`; memory `slack-connector-returns-text-only-colleague-attachments-need-a-pr`. **Runner-group access DONE 22:50**: `pilotcloud-site` added to org runner group 5 `pilot-fleet-deployer` after `gh auth refresh -s admin:org`; memory `org-runner-group-repo-access-needs-admin-org-scope`. Next: review her PR → first deploy → Paddle resubmit; after her cert switch (slot still unnamed): docs base URL (4 files under `docs/`, README, ~30 refs) + `docsUrl` in the site. Legal pages still founder-fact-gated (`product/LEGAL-TERMS.md`).
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
| **P1** | **Executor fast-follow track — self-close hand-off re-pick, bootstrap gate follow-up** ([TASK-573](tasks/archive/TASK-573-selfclose-handoff-marks-original-superseded.md) · [574](tasks/archive/TASK-574-bootstrap-callsite-test-and-attempt-guard-key.md)) | ✅ 10-17: #5741 → PR#5743 merged 13:35Z, **reviewed 10-19 APPROVE-w-notes** (supersede at both self-close sites, 3 pins hold; notes: closed original keeps `pilot` labels, silent no-op on a `running` row) → [TASK-575](tasks/archive/TASK-575-selfclose-supersede-running-row-and-closed-original-labels.md) → #5747 → PR#5751 merged 10-19 11:09Z, reviewed APPROVE-w-notes (closed+no-overlap now flagged — correct; "leaving open" wording stale; CAS-reject ERROR log per hand-off). TASK-573 archived. TASK-574 → #5745 → PR#5750 merged 10-19 10:38Z, **reviewed APPROVE-w-notes**, archived. Done 10-17: PR#5740 reviewed APPROVE-w-notes, PR#5742 APPROVE-w-defects, 571/572 archived. Open: Slack approve click not received (unfiled); infra re-pick cap 8 with no backoff (memory). |
| **P2** | **Outbound messaging gaps — approvals and notices that silently go nowhere** ([TASK-576](tasks/TASK-576-outbound-messaging-gaps.md)) | ✅ 10-19 ALL MERGED + REVIEWED (PR#5763–#5767, plus #5755 → PR#5768 same evening; box steps after v2.290.0: `Slack ingress` line read ✅ 10-20 15:09Z · `lifecycle_notifications` enabled ✅ 15:04Z (first Telegram notice not yet confirmed) · `approvers_by_channel.telegram` hold lift NOT yet verified). Legs were: [#5756](https://github.com/qf-studio/pilot/issues/5756) no-handler fail-closed → [#5757](https://github.com/qf-studio/pilot/issues/5757) GitHub approval rehydrate → [#5758](https://github.com/qf-studio/pilot/issues/5758) one Slack click path per mode (adds INFO per interaction — covers the unfiled click gap above) → [#5759](https://github.com/qf-studio/pilot/issues/5759) wire PR lifecycle notifier (opt-in) → [#5760](https://github.com/qf-studio/pilot/issues/5760) deterministic empty channel. Same day: #5716/#5699/#5749/#5753 shipped. Leg A hit an executor retry loop (stale auto-preserve branch) → [#5762](https://github.com/qf-studio/pilot/issues/5762) filed. |
| P3 | **Post-merge CI fix — three unfiled follow-ups** ([TASK-508](tasks/TASK-508-post-merge-fix-borrowed-branch.md)) | #5564 shipped. Unfiled: flake re-run before filing (code class) · ownership check in `checkExternalMergeOrClose` (PR merged before the issue existed) · dedup vs human-filed fix issues (`findExistingFixIssue` is exact-title only). |
| **P1** | **Pricing v3 — honest allowance + prepaid overage packs** ([TASK-546](tasks/TASK-546-pricing-v3-honest-allowance-overage-packs.md)) | 🚀 **10-14: waves 1–3 DISPATCHED, price unchanged** — pilot #5676/#5677/#5678 (key source + reported cost + usage rows · chat-turn rows · daily chat cap), console #401/#402/#403/#404 (ledger · tickets-or-USD · daily caps · invites), ui#231 (Members page). Research 10-13: cost +1-4%/ticket nets -$57..-$2 vs +$321 flat; "100 tickets" enforced as $100 (fires ~ticket 32 on Sonnet 5). Deferred until the founder changes the price: packs 25/$99 · 100/$349, $300 ceiling value, copy/catalog. Decisions D1–D11 in the doc. |
| **P1** | **Legacy repo bootstrap — real Navigator context on first attach, persisted, priced** ([TASK-549](tasks/TASK-549-legacy-repo-navigator-bootstrap.md)) | 🚀 10-14: #5679 (bootstrap session, trigger default manual) + #5680 (copy-back) dispatched. Verified: scaffold's injected context sections are placeholders nothing fills; no copy-back from worktrees; chat turns are cold research sessions. Next: cold-start bench (Navigator job), then D1–D3 (auto trigger, console snapshot, 10-ticket price). |
| **P1** | **Pilot SaaS platform** ([TASK-405](tasks/TASK-405-pilot-saas-platform.md)) | S0–S2 ✅ · S3 exit met local-first 08-18 · S4 build complete · **S4 exit path UNBLOCKED 09-21: console-api + reconciler LIVE on Nelya's `pilot-fleet` (ECS, `prod-0.1.0`, factory off)** — the minimal-EC2 route ([TASK-490](tasks/TASK-490-s4-minimal-invpc-console.md)) is superseded by the ECS transfer. **Domain decided `pilotcloud.dev`.** **09-25: first fleet tenant provisioned + shipped twice on the hosted path; board live after enabling the sync workers in prod (infra#14) — S4 exit evidence on the fleet.** Next: **Paddle L7** (sandbox MCP key → $299 price object → live checkout) → console model pin. Email track (TASK-501) shipped, smoked and archived 09-29. |
| **P1** | **Fleet TO-BE alignment (Nelya)** ([TASK-495](tasks/TASK-495-fleet-to-be-alignment-nelya.md)) | ✅ **EXIT EVIDENCE MET 09-25**: reconciler-provisioned tenant `i-0289111000cebcee9` shipped two issues end-to-end; tenant id posted to Nelya for her account-side checklist (Slack draft). Old-estate backup chain verified closed 09-25. Open on her side: none blocking. Ours: infra#16 (replicas=1) via her pipeline = our dispatch. |
| **P1** | **Golden AMI refresh → first fleet tenant** ([TASK-499](tasks/TASK-499-golden-ami-refresh-first-fleet-tenant.md)) | ✅ **L3 DONE 09-25: first fleet tenant provisioned + issue→PR→merge in 4m35s on the hosted path** (defects filed: console#323 repo-switch inert · console#324 worktree parity · pilot#5459 pr_url · pilot#5460 hook cleanup). Prior: L1 ✅ (bake fetches release by version, sha256, version pin, both SSM params) · L2 ✅ `ami-01ecd7cefa1e6f316` pilot 2.276.1 · **L3 BLOCKED**: reconciler redeploy rolled back on Nelya's AZ-rebalancing template (binpack singleton); after her fix: re-run → `tenant_factory=true` (ask founder) → dogfood tenant → Docs real tree. Old AMI kept as rollback. |
| **P1** | **Paddle Billing integration** ([TASK-497](tasks/TASK-497-paddle-billing-integration.md)) | Code complete, L6 smoke passed 09-14. **L7 started 09-29: sandbox key in Doppler, sandbox price $499 `pri_01m3rf7qws3gzscj9fttg4aywe` (decided 09-30).** **Nelya template ask POSTED 09-30 09:57Z** (thread `1790762207.809729`; flag-off gated, values later). **10-09: live $499 twin `pri_01m4g870rh98m207cjwhjn8taq` + live client token created via paddle-live MCP; token in Doppler `prd`.** Next, founder (dashboard): live API key · notification destination (`console.pilotcloud.dev/api/v1/billing/webhook`, `subscription.*` + `transaction.completed`) · submit checkout domain · payment link. Nelya template ask unanswered since 09-30 — nudge. Then point prod at live, readiness audit. |
| **P1** | **Linear Invoices → GitLab cutover** ([TASK-510](tasks/archive/TASK-510-linear-invoices-gitlab-cutover.md); forge half supersedes [TASK-509](tasks/TASK-509-linear-invoices-onboarding.md)) | ✅ **LIVE 10-02 08:46Z on v2.277.1** (cut by hand; the train is daily 16:00 Berlin, the 10-01 "not cutting" note was a misread). [#5583](https://github.com/qf-studio/pilot/issues/5583) per-project `gitlab:` forge + [#5584](https://github.com/qf-studio/pilot/issues/5584) Linear OnPRCreated controller fix merged (PR#5585/#5586 **reviewed 10-02, APPROVE-w-notes**; follow-up [#5589](https://github.com/qf-studio/pilot/issues/5589) epic PR path; [#5588](https://github.com/qf-studio/pilot/issues/5588) poller retry; sdk#144 Linear UUID). Box: PAT + GitLab clones + Linear polling on; both GitLab `main` locked to MR-only; GitHub mirrors frozen. Founder scope: configure only, no tickets labelled by Navigator. Merges stay manual (GitLab `main` → prod on `prod-*` tags). |
| **P1** | **Included token volume — platform key, metering, own-key overage** ([TASK-502](tasks/TASK-502-included-tokens-platform-key.md)) | ✅ **LEGS 0+1+2+4 LIVE 10-06.** Leg 1 key pool: console PR#358/#359/#360 merged + reviewed; SSM + reconciler wired (Nelya infra 79a4cc4); console redeploy 37352817795 green; pool import on console-reconciler:23 → `status` free 5 / assigned 0 / retired 0. First pool assignment = a TEST org only. Leg 3 shipped 10-06 as TASK-512 (console PR#363/#364, live in dry-run). Next: leg 5 copy (moves with the Paddle catalog); WIF = leg 1d later. Org credits prepaid $9.57, auto-reload off (founder deferred). |
| P2 | **Console Docs page — live verification** ([TASK-466](tasks/TASK-466-console-docs-page.md)) | Page renders through the edge (09-22 founder login) but the console DB has no tenant yet → the real `.agent`-tree proof is TASK-499 L3's acceptance (first fleet tenant). infra#51/TASK-498 closed superseded. |
| P2 | **pilot-docs → GitHub + AWS deploy** ([TASK-492](tasks/TASK-492-pilot-docs-gitlab-to-github-migration.md)) | ✅ Cutover done by Nelya 09-05; TASK-494 sync fix DONE + reviewed 09-06 (GitHub-only, preserves pilot-docs `.github/`). **Remaining = step 4 operator:** delete `GITLAB_SSH_KEY` secret · drop `gitlab:` block in hosted config · archive `quant-flow/pilot-docs`. Nelya owes: compression + CSP-RO answer. |
| **P1** | **Console rail implementation** ([TASK-478](tasks/TASK-478-console-rail-implementation.md)) | 11 approved designs → shipped surfaces. **Build-out COMPLETE 08-15 (overnight run): all 16 autopilotable legs executed + reviewed.** Blocked on founder morning sequence (approve PR#67→72→74→76 · close #73/#77 to arm retries · label ui#78 after) → then GH-69/GH-75 retries re-land · **real-stack verify batch UI-2..12** (SOP; blocked on GH-75 re-land) · CON-5 billing portal (founder Stripe gate) · copy pass ($299 · PR#72 "Includes" line · support@ mailto). Daemon-side follow-ups FILED 2026-08-20: [pilot#5027](https://github.com/qf-studio/pilot/issues/5027) merge-time ancestry check (stacked-superset guard, extends GH-4872) + [pilot#5028](https://github.com/qf-studio/pilot/issues/5028) base-presence check before claim (see pitfall `sequential-gates-on-execution-not-merge-fastfollow-misbase`; 4 family incidents in 6 days, nav-research verdict: both fixes needed). |
| **P1** | **Throughput acceleration** ([TASK-393](tasks/TASK-393-throughput-acceleration.md)) | Phase 1 (instrumentation) ✅ shipped 07-09. **M3 baseline window closed ~07-20 — histograms never harvested; phases 2–5 remain gated on that analysis.** Remaining: (2) execution lanes on `Complexity`, (3) N-concurrent per repo (`ProjectWorker` pool — note this is also the sole serialization point, see mem-101/102), (4) SHA-keyed repo primer, (5) risk-score trust tiers. Roadmap: [`throughput-roadmap.md`](system/throughput-roadmap.md) (M0–M8, D1–D6). |
| **P1** | **Hosted retry path for failed executions** ([TASK-485](tasks/TASK-485-hosted-retry-path-failed-executions.md), [#5008](https://github.com/qf-studio/pilot/issues/5008)) | Daemon legs SHIPPED+REVIEWED 08-25 (PR#5214 classifier · PR#5215 stalled re-arm sweep · PR#5220 streak alert) — ride the 08-26 v2.270.0 train. **Remaining: Leg 3** (console repo: C8 dispatch on failed/stalled card cycles trigger label + removes `pilot-blocked`) **after the train lands on the box**, then **Phase 4** live validation on ship-test-js#6 (expect ≤16min re-arm latency — repick backoff gate). |
| P1 | Web dashboard polish | React UI functional but needs a design pass. |
| P2 | Delivery-evidence audit — false-success class ([TASK-460](tasks/TASK-460-delivery-evidence-false-success.md)) | Split from TASK-459 by founder scope call 08-08: green CI is not proof the requested change shipped (`mem-151`: scaffold-only PR merged green, parent auto-closed, zero requirements delivered). Planned, NOT dispatched; TASK-459 Phase 4's inventory hook feeds it the success-side site rows. Candidate legs: diff-surface check · ACs fail-when-unwired · epic-collapse guard. |
| P2 | E2E test suite | No integration tests — reliability untested. |
| P2 | Web dashboard auth | Token-based auth for remote access. |
| P2 | Mobile-responsive dashboard | Primary use case is phone access. |
| P3 | GitHub App auth | PAT → installable GitHub App. |
| P3 | Audit §3 Wave 4+ candidates | Not yet decomposed: `RecordAPIError` wiring beyond github · `AlertTypeOOMKilled` · multi-gate scanner phase discipline · subprocess migration end-to-end validation · `autopilot` adapter coupling refactor · SQL `withTx` helper · generic `Poller[T]` extraction · `Releaser` frozen-at-startup fix. Source: `.agent/audits/AUDIT-2026-05-25.md` §3. |

**Operator-parked (not autopilotable):** ~~restart the hosted daemon~~ **DONE 09-07 09:18Z** — box rebuilt from main (`v2.273.0-23-ge054b01c`, carries #5339–#5347) and restarted; `orchestrator.receipts_digest` active (scheduler started, catch-up digest for 09-06 delivered to Telegram 283716179; next 18:00 Europe/Berlin). daily_brief still on America/New_York (arrives 14:00 CEST). ~~`PILOT_DOCS_PAT` workflow scope~~ obsolete since TASK-494 (sync never writes `.github/`) · **domain pick** (`pilot.build` premium $720/yr · `pilot.engineering` $83 · `pilothq.dev` ~$15; = OIDC issuer, sticky) · branch protection on `qf-studio/pilot` main (TASK-405 founder decision 7 — main is currently unprotected) · EBS restore DRILL (runbook exists at pilot-cloud-infra `docs/RESTORE-RUNBOOK.md`; the drill itself is operator work) · tenant box `i-0a3bf271d598196ca` still on **2.259.3** (predates TASK-485 daemon legs — fleet images are immutable by invariant, rolling-upgrade machinery is console#216; operator binary swap is the interim for Phase 4) · rotate ALL box tracker/API tokens (founder-planned; Jira token exposed in a 08-26 session; **10-19: the laptop config's Slack bot+app, Telegram bot and Discord bot tokens printed into a session transcript — rotate all four**) · infra#2 Golden AMI v2 (stale claim corrected 08-26: `aws-infrastructure-pilot` IS in the box config — issue itself needs re-triage) · console#45 (`pilot-spec-incomplete`/`blocked` since 07-24 — needs rewriting into an implementable spec). NOTE 08-26: infra PR#27 `cdk deploy` DONE at some point — FleetVpc NAT verified at 1, `Environment=fleet` tag live in cost view.

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
