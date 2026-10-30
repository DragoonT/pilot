# Scoring detail — run 5 (post-merge reviewer calibration 2026-10, daemon outputs in `run5/`, model claude-opus-5-5, reviewer prompt step 3 = #5975: sibling functions + untouched branch opened beside each hunk, "met" must name the breaking input)

Rules: hand defects = numbered D*/Defects items plus explicit ✗ scope bullets, "Notes (no action)" excluded when a Defects section exists, the concrete notes are the defects for the two notes-only hand reviews (pilot#5870, console#427); each hand defect is HIT (same problem) / PARTIAL (same area, weaker claim) / MISS; each unmatched daemon finding is NEW-VALID (real, verifiable, or matches a hand note) / FALSE (wrong on its face or contradicted by the hand review) / UNSURE (unverifiable hedge); each PR is judged on `defects` first, then `notes`, then `not_verified` only where it names a concrete problem; verdict match = Y when both are RC or both are non-RC (A+defects / A+notes / AWN = non-RC); strict: HIT needs the same problem not the same file, doubt between HIT and PARTIAL → PARTIAL, doubt between NEW-VALID and UNSURE → UNSURE. Hand-defect numbering and hand n per PR are run 4's (total 52); each bullet carries the run-4 result in brackets. Claims marked (verified) were checked against the merge commit in the repo on disk (pilot, pilot-console, pilot-console-ui).

## ui#252 (hand RC / daemon RC)
- D1 Header Pool/org/Last-shipped bound to wire fields no backend sends → HIT [run 4: HIT] (defect 1 `httpAdapter.ts:1046`: no producer for `orgName`/`lastShippedAt`/`poolPercentUsed`, `:1016` `timeToPrMinutes`; mock `buildDashboard` returns none; nothing on `getAllowance` being uncalled or `auth.org?.name` this run)
- D2 View ignores StatCard numerator/pill variants; N is window-scoped, not billing-month → PARTIAL [run 4: PARTIAL] (defect 3 `DashboardView.vue:305` `/100` literal; defect 7 `:307` outer `RouterLink` instead of StatCard's `to`; nothing on the `numerator`/`denominator` or `pill`+`count` variants, nothing on `stats.shipped` vs allowance `usage.tickets`)
- D3 Mobile glance still renders per-ticket USD on every tenant → MISS [run 4: MISS] (notes: "Cost/shipped left the desktop grid but keeps its em-dash on mobile … the docblock records this as a trim")
- D4 PR body lacks make build/test/lint output and adapter name → PARTIAL [run 4: PARTIAL] (`not_verified`: "the PR body has no Evidence block with pasted output"; not a defect, adapter name not mentioned)
- D5 Missing-field notes absent from PR body → MISS [run 4: MISS]
- Extra NEW-VALID: GH-249 tests spy on `getDashboard`, `toDashboard` mapping of the 4 new keys untested (defect 2) · `BoardView` never reads `route.query`, `?lane=needs-you` is inert (defect 4, hand N2)
- Extra UNSURE: "platform-key tenant" test sets no tenant/key state (defect 5) · old em-dash assertion on the Time-to-PR tile replaced by a label check (defect 6)
- (defects 3 and 7 are inside D2; `not_verified` "design/ has no `/100`, `Last shipped` … strings" is a hedge, not counted)

## ui#261 (hand RC / daemon RC)
- D1 Queue binds to `project`/`parentId` the console never sends → HIT [run 4: HIT] (defect 1 `httpAdapter.ts:589`; `queue.ts:57` `card.project ?? NO_PROJECT` → one "Board" group, nothing nests; mock seed cards carry no `project`)
- D2 Execution meta binds to 3 fields never sent; N+1 fetch per card → PARTIAL [run 4: PARTIAL] (defect 7 `DashboardQueue.vue:25`: "one `getCardExecution` request per card, for every card including backlog cards"; nothing on `durationMs`/`linesAdded`/`linesRemoved` having no producer)
- D3 No build/test/lint evidence or adapter note → HIT [run 4: HIT] (defect 8 "no `## Evidence` block and no pasted output"; notes "not met")
- Extra NEW-VALID: `toBoardCard` untested, spec mocks the whole adapter (defect 2) · stale `DashboardShippedByProject` refs in the `DashboardView.vue` docblock `:66/:131/:153` (defect 4, hand N4) · `dashboardShippedColors.ts:3` comment still names the deleted `DashboardShippedByProject.vue` (defect 5; verified at merge `b881f20`) · `onMounted` has no error handling, a rejected `listCards()` is an unhandled rejection (defect 7 first half, hand N5)
- Extra UNSURE: "PR goes outside the scope fence, builds the GH-257 sibling" (defect 3; the hand records PR #260 closed and its code merged inside #261) · docblock cites "Figma 2026-10" instead of `design/<file>.html` (defect 6)

## ui#255 (hand RC / daemon RC)
- D1 "Needs API" list missing from PR body → HIT [run 4: HIT] (defect 1, blocking: "no Needs API section … listed only in a code docblock")
- D2 Memory card hides counts the docs tree already serves → MISS [run 4: HIT] (notes: "Memory card … met as all `—`. No memory endpoint exists. The only memory fields are per-chat-turn `memoriesRead/memoriesCreated`" — the `DocsCounts {patterns; pitfalls; learnings; decisions}` on the same `DocsTreeResponse` was not found this run)
- D3 Graph card is a dead prop → PARTIAL [run 4: PARTIAL] (weaker than run 4: no defect; `not_verified` "Graph health rule … is invented here … No backend counterpart exists", and the notes call the never-passed prop "the honest outcome")
- D4 Panel bypasses `ds-*` vocabulary → MISS [run 4: MISS] (notes: "16px padding and 13px rows: met"; defect 5 objects to `text-needs-you` on Drift for its meaning, not to the pre-U1 vocabulary)
- D5 No adapter note → MISS [run 4: MISS]
- Extra NEW-VALID: Docs header client-recounts `entries.length` against the `types.ts:644` "never client-recount" contract, mock already slices on `limit` (defect 2, hand N4) · no test covers `loadContextDocs` or the `ContextPanel` mount in `DashboardView` (defect 6)
- Extra UNSURE: Context column hidden below `md` (defect 3; true at the merge, design call as in run 4) · rows show one value, no "count left of a muted secondary number" (defect 4, self-rated "where available") · Drift coloured `text-needs-you`, the Review-needed accent (defect 5; verified `ContextPanel.vue:56` at `c05dbd1`, whether it is wrong is a design call)

## ui#254 (hand A+defects / daemon RC)
- D1 Two activity charts → HIT [run 4: HIT] (defect 1 `DashboardView.vue:339/342`, blocking; adds that the new panel sits below the old chart, not under the stat row)
- D2 7D/30D truncated to newest 50 → PARTIAL [run 4: PARTIAL] (`not_verified`: "Whether the server's `GET /api/v1/board/activity` caps or pages its results. A cap would undercount the 30D range"; not run to ground)
- D3 Rolling windows ending at `now`, no dates in the tooltip → MISS [run 4: HIT] (notes item 2: "Bucket size per range … met at :26-28"; nothing on calendar-hour/day alignment or the tooltip. Defect 5's "`now` … once, when the component mounts" is the stale-window finding run 4 scored as NEW-VALID, kept separate here for consistency)
- Extra: "PR body must say bucketing is client-side; it does not" (defect 2) → FALSE (hand: "bucketed client-side, stated in PR body and docblock"; repeated from run 4)
- Extra NEW-VALID: mock activity feed never produces `pr_merged`, so the chart never highlights in mock/dev (defect 3; verified — no `pr_merged` in `mockAdapter.ts` at `49b4555`) · `bg-needs-you` is a departure from `dashboardShippedColors.ts`, documented (defect 4, hand N1) · `now` evaluated once at mount, long-open dashboard drops later events (defect 5) · no view test covers `loadBoardActivity` or the chart mount (defect 6)
- (`not_verified` "make output pasted: met" is not a finding)

## ui#246 (hand A+defects / daemon RC)
- D1 Mobile Chat tab lost confirmation cards → MISS [run 4: HIT] (no mention of `confirmation` events or the mobile tab; the sibling read of `ChatWindow.vue` landed on its polling hook, defect 4, not its confirmation renderer)
- D2 Sub-agent tree/Context bind to events nothing emits → HIT [run 4: HIT] (defect 1 `httpAdapter.ts:897`: mock emits only `progress`/`confirmation`/`text`, no `subagent`/`context` event anywhere, `types.ts:437` "ASSUMED wire contract")
- D3 `mode` never leaves the console → HIT [run 4: HIT] (defect 2 `httpAdapter.ts:1649`: nothing reads `mode`, no chat mode existed before this diff, "RESEARCH/DOCS pills are a new wire field with no confirmed consumer")
- D4 PR body gaps: adapter line, missing-event-field list → HIT [run 4: HIT] (defect 3, blocking: body "lists no missing fields"; notes: "one line names the adapter used is not met")
- Extra NEW-VALID: `ChatWindow.vue:196` `onUnmounted(() => chat.stopPolling())` stops the store's single `pollTimer` for the Research page when the Operator panel closes; `ChatView` guards only its own unmount (defect 4; verified at `8b14c8e`: `ChatWindow.vue:195-196`, `ChatView.vue:75/84-85`, `stores/chat.ts:86` one shared timer) · tests set `chat.messages` / spy on `chat.send`, neither `toChatEvent` nor the `mode` body exercised (defect 5) · `AppShell.vue:24` "desktop never actually renders this route" is stale now that `DashboardView.vue:116` pushes to `chat` (defect 6; verified)
- Extra UNSURE: `text-ds-text/60` opacity dialect (defect 7; the hand accepted that class) · docblock cites only the Figma node, no `design/<file>.html` or `no mock` marker (defect 8)

## pilot#5799 (hand A+defects / daemon RC)
- D1 Receipts digest fail-open on `key_source=unknown` → HIT [run 4: HIT] (defect 1 `receipts.go:345` with the `COALESCE(… 'unknown')` producer at `store.go:866` and the founder-tenant pitfall; defect 2 `:370` total is the same defect's second function, adds that the test covers only `own`/`platform`)
- D2 Structured brief inherits the fixed 09:00→09:00 window → MISS [run 4: MISS]
- Extra NEW-VALID: `SetPoolSource` has no production caller, `pool` always null (defect 3, hand N1) · structured briefs are stored only via `Scheduler.runBriefWithResults`, built only when `daily_brief` is enabled with a store, so a tenant with the daily brief off gets a permanent 404 on `/latest` (defect 4; verified at merge `d814c2381`: the only `briefs.NewScheduler` call is `main.go:4009` inside the daily-brief block; run 4's gateway-only hedge, now concrete) · `LoadPendingApprovals()` has no project filter while executions honour `Filters.Projects`, so `review_needed` lists other projects' approvals (defect 5; verified `generator.go:314/320` at the merge) · `brief_payloads` has no retention (defect 6, hand N5) · pasted `make lint` fails on SA4023 in `cmd/pilot/tunnel.go` (defect 8)
- Extra UNSURE: "new route in plain text" might mean the response body (defect 7; self-hedged misreading of the issue)
- (`not_verified` "make test omits 17523 lines", "gwStore satisfies BriefPayloadStore" are hedges, not counted)

## pilot#5822 (hand A+defects / daemon AWN)
- D1 Monday daily+weekly fire the same minute; `/latest` non-deterministic → HIT [run 4: PARTIAL] (defect 3 `weekly.go:29`: both fire at 09:00 Monday, both store a payload, "`/latest` returns `rows[0]` … whichever finished last"; the missing `kind` filter is not drawn)
- D2 `merged_count` 0 for task families autopilot never tracks → PARTIAL [run 4: MISS] (notes, not a defect: "if autopilot isn't running, no controller merged events are written and merged_count quietly drops toward 0; only `runner.go:2717` still records merges"; nothing on Jira/Linear PRs never entering `activePRs` or the `tickets_shipped` contradiction)
- D3 PR body pastes FAIL for `make test`/`make lint` → HIT [run 4: HIT] (defect 5 lint SA4023; notes "Both pasted outputs end in failure … not met"; `not_verified` adds the "36099 omitted lines" point the hand also makes)
- Extra NEW-VALID: weekly catch-up looks only at channel `"telegram"`, Slack/email-only tenants never catch up (defect 2, hand N4; weaker than run 4's verified key-mismatch finding, which is not repeated this run) · `earliestStageOccurrences(pr_created)` scans the whole ledger per run (defect 4, hand N9)
- Extra UNSURE: catch-up fires on a non-Monday day within the 8-day lookback and the window ends at `time.Now()` (defect 1; catch-up by design, and run 4 showed the path is dead on the channel-key mismatch)
- (`not_verified` "`SaveExecution` `CompletedAt` format" is a hedge, not counted)

## pilot#5868 (hand AWN / daemon AWN)
- D1 Daily cap per controller → MISS [run 4: HIT] (`not_verified`: "Budget: met. The budget is an in-memory counter per UTC day, separate from `DailyCapGate`" — the per-controller `postMergeBudget()` × `wirePostMergeReviewer` fan-out was not traced)
- D2 Follow-up issue >200 words / backticked cross-repo paths trip the SOP gates → MISS [run 4: MISS]
- D3 Attempt-once drops the review on transient failure; ledger skipped when `commentID <= 0` → MISS [run 4: HIT] (notes: "The flag is set and saved before the goroutine starts … A restarted daemon sees `true`" — written as met, no failure case named)
- D4 `CIResult` is pre-merge → HIT [run 4: MISS] (defect 1 `post_merge_review.go:212`: "given the pre-merge CI status and never the post-merge CI result. The review starts before `handleMerged` sets `prState.Stage = StagePostMergeCI` (`controller.go:6246`)")
- D5 `localMergedDiff` untested → HIT [run 4: MISS] (defect 2 `:381`: "Every controller test replaces it with `c.postMergeDiff`")
- Extra NEW-VALID: startup log prints empty `pmr.Model` on fallback (defect 3; verified `post_merge_reviewer.go:55` at `018e450d0`) · the `deploy failed` early return at `controller.go:6127` runs before `maybeStartPostMergeReview` at `:6217`, so a failed deploy skips the review (defect 4; verified) · PR body has no `## Evidence` block with the `go test -race` output (defect 6) · in-flight review goroutines not awaited at shutdown, `waitPostMergeReviews` only called from tests (`not_verified`, hand note)
- Extra UNSURE: cap test does not assert the "logged once" part (defect 5)

## pilot#5874 (hand AWN / daemon AWN)
- D1 Past reset rolls +24h → 6h pause → HIT [run 4: MISS] (defect 2 `usage_limit_pause.go:100` with `ratelimit.go:96` `if resetTime.Before(now) { resetTime = resetTime.Add(24 * time.Hour) }`: "a 'resets 2pm' message read at 2:01pm rolls over to tomorrow and holds admission for the full max_pause (6h) instead of about 5 minutes … the new pause turns it into a fleet-wide 6h hold")
- D2 Double alert (runner `rate_limit` + `usage_limit_pause`) → MISS [run 4: MISS] (notes: "Alert met: one alert per episode")
- D3 `Stop()` leaves `usageLimitResumeAt` and the owner → MISS [run 4: MISS] (notes: "`Stop` calls `stopUsageLimitPauseTimer` before `d.mu.Lock`" — lock order only)
- D4 Three dispatcher tests call `armUsageLimitPause` directly → MISS [run 4: MISS] (defect 4 is the `cmd/pilot` status test's hand-written JSON, a different test; scored UNSURE as in run 4)
- D5 Parser not verified against current Claude Code wording → PARTIAL [run 4: MISS] (`not_verified` "Production wording: … I did not trace whether the real Claude backend fails the same way. If it returns a non-nil `execErr` instead, `Classify` sets `ExecStatusFailed` and the pause never arms" — same gap, production usage-limit output unverified, but about the error channel, not `ParseRateLimitError` formats)
- Extra NEW-VALID: `pilot status` GETs `/api/v1/status` with no bearer token against the auth-protected mux, pause line silently disappears (defect 1; verified in run 4) · gateway test output pasted as `(cached)` (`not_verified`)
- Extra UNSURE: GH-5862 block sits between the GH-4412 comment and the loop it describes (defect 3; verified true at `076bb48` `main.go:3409-3419`, but a GH-5862 one-liner precedes the block, cosmetic) · status test decodes hand-written JSON (defect 4, self-rated "weaker than it looks rather than wrong")

## pilot#5870 (hand notes-only / daemon AWN)
- D1 No recovery ref for the discarded commits → MISS [run 4: MISS]
- D2 `GetCurrentBranch` error swallowed → HIT [run 4: MISS] (defect 1 `git.go:190`: "If GetCurrentBranch fails, the error is ignored and the code goes on to DeleteBranch … the operator then gets git's 'cannot delete branch' message again"; `if curErr == nil && current == branchName` quoted as the fault this time)
- D3 No log on the detach path → MISS [run 4: MISS]
- D4 Dirty refusal unreachable from the runner in direct mode → MISS [run 4: MISS] (notes trace the only caller to `runner.go:4652` inside `!useWorktree` but not the `git_clean` preflight ahead of it)
- D5 Test gaps: dirty case uses an untracked file, no detached-HEAD start → MISS [run 4: PARTIAL] (notes item 2 now reads the untracked file as a feature: "untracked files also count as dirty. That means the test's untracked dirty.txt triggers the refusal rather than slipping through")
- D6 PR body re-runs `make` against the replaced bullet → HIT [run 4: HIT] (defect 3: rewrote the sixth acceptance bullet and ran all three, plus the SA4023 lint failure)
- Extra UNSURE: a stale branch checked out in a different linked worktree still reaches `branch -D` (defect 2, self-rated "not a requirement gap"; worktree mode is out of scope per the hand) · mutation bullet never run, checked "by reasoning only" (`not_verified`)
- (run 4's verified NEW-VALID — detached clone on a failed `DeleteBranch`/recreate — is not repeated)

## pilot#5871 (hand AWN, 1 defect / daemon AWN)
- D1 `githubEventHasLabel` exact-case vs SDK/webhook `EqualFold` → MISS [run 4: MISS]
- Extra NEW-VALID: `shouldStripPilotAfterTerminalDrops` still passes `ev.Labels` though `liveLabels` is in scope (defect 1, hand note "pilot-strip guard still read the pre-wait snapshot") · live-gate skips increment `claimLostDrops`, so admission skips and claim-lost drops are conflated against `terminalDropPilotStripThreshold = 3` (defect 2, hand note) · backoff pre-check reports `skipReasonNeedsHuman` for every armed key, wrong reason after a closed/trigger-removed skip (defect 3, hand note) · fetch-error subtest never pins "proceeds with `ev.Labels`" (defect 4, hand note) · both mutation bullets "run manually", not executed (`not_verified`, hand note)

## pilot#5872 (hand AWN, 1 defect / daemon AWN)
- D1 `RecordDecision` widening regresses the `sql.ErrNoRows` unlinked-request path → HIT [run 4: HIT] (defect 1 `manager.go:517`: returns early without the delete or `pr.CancelFn`, "leaves the manager waiter and GitHub poll running until the dispatch timeout", `gateway/approvals.go:294-298` relied on the cleanup)
- Extra NEW-VALID: "next poll tick retries" impossible — `resolvePending` deletes the persisted row first, `checkApproval` already removed the entry, rehydrated path has no async goroutine (defect 2, hand note) · rehydrated test builds its own `pollCtx` and wraps `p.CancelFn`, so Rehydrate's real `pollCtx` wiring at `github.go:225` is not exercised (defect 3; verified `github_test.go:924-927` at `bfa013cbc`) · pasted `go test -race` is `(cached)` (defect 4, hand note) · mutation bullets "run manually", not evidenced (`not_verified`, hand note)

## pilot#5875 (hand AWN, 2 defects / daemon AWN)
- D1 Budget-killed command inside a mixed item renders as evidence → MISS [run 4: HIT] (notes: "A command killed by the budget is relabelled by the prefix check against `te.Error()` 'timed out after %s' (:206)" — the relabel at `:206` was traced, the `allErrored` aggregation at `:322` that run 4 found was not)
- D2 Reused gate output not pinned to the pushed HEAD → MISS [run 4: MISS] (notes: "Quality-gate output is reused on an exact argv match: met")
- Extra NEW-VALID: the GH-5346 salvage path passes `nil` gates although `result.QualityGates` is set at `runner.go:3157` right before it (defect 1; run 4's "epic and timeout-salvage pass nil gates", now with the producer line) · runner test covers only the shared-creator branch, gh-CLI and SDK branches untested (defect 2, hand note) · `finalizeCtx` grants a window only once the deadline has blown (defect 3, hand note) · WARN fires once per reused command, not once (defect 4, hand note)
- Extra UNSURE: three mutation bullets listed "run manually" so "nobody has shown" the tests fail (defect 5; the hand applied all four pins)

## console#427 (hand notes-only / daemon AWN)
- D1 USDGate test substring also matches nested `usage.key_source` → MISS [run 4: HIT] (defect 3 is about the same test's missing switched-to-own case, not the substring)
- D2 Three copies of the "switched this period" rule → PARTIAL [run 4: MISS] (defect 2's sub-clause: `KeySourceForOrg` "copies the rule in `StatusForOrg` (status.go:345) by hand"; two of the three copies, `CurrentPeriodSwitched` not named)
- D3 Second `allowance.Service` without `Meter` → MISS [run 4: MISS]
- D4 `reportedUsdCents` `null` → omitted wire change → MISS [run 4: MISS]
- D5 `percent_used` denominator includes pack tickets → MISS [run 4: MISS]
- D6 UI types USD as `number`, reads only nested `key_source` → PARTIAL [run 4: PARTIAL] (`not_verified`: "SPA consumers of the newly optional `totalCostUsd`/`costUsd`/… fields: no frontend in this checkout")
- D7 Dashboard cost via the `/metrics` instance proxy is ungated → HIT [run 4: MISS] (defect 1 `proxy.go:49`: allowlist holds `"metrics"`, `usagepoller.go:64` decodes `totalCostUSD`, `dashboardapi/dto.go:37-39` says the SPA fetches costPerShipped "via the C13 instance passthrough"; "defeats the 'never shows per-ticket cost' context")
- Extra NEW-VALID: `KeySourceForOrg` never run by any test, gate tested only through `fakeKeys` (defect 2; verified in run 4) · USDGate test has no "key assigned but switched to own this period" case (defect 3; verified at `b823a0d` `routes_test.go` cases are `{"platform", true}` and `{"own", false}` only) · no make build/test/lint output pasted (defect 5; the hand accepted CI)
- Extra UNSURE: `ExhaustedBy: "usd"` still sent to platform-key tenants (defect 4, self-rated "does not breach the issue's USD-field rule")

## Per-PR table

| PR | hand | daemon | match | hand n | HIT | PARTIAL | MISS | NEW-VALID | FALSE | UNSURE |
|---|---|---|---|---|---|---|---|---|---|---|
| ui#252 | RC | RC | Y | 5 | 1 | 2 | 2 | 2 | 0 | 2 |
| ui#261 | RC | RC | Y | 3 | 2 | 1 | 0 | 4 | 0 | 2 |
| ui#255 | RC | RC | Y | 5 | 1 | 1 | 3 | 2 | 0 | 3 |
| ui#254 | A+defects | RC | N | 3 | 1 | 1 | 1 | 4 | 1 | 0 |
| ui#246 | A+defects | RC | N | 4 | 3 | 0 | 1 | 3 | 0 | 2 |
| pilot#5799 | A+defects | RC | N | 2 | 1 | 0 | 1 | 5 | 0 | 1 |
| pilot#5822 | A+defects | AWN | Y | 3 | 2 | 1 | 0 | 2 | 0 | 1 |
| pilot#5868 | AWN | AWN | Y | 5 | 2 | 0 | 3 | 4 | 0 | 1 |
| pilot#5874 | AWN | AWN | Y | 5 | 1 | 1 | 3 | 2 | 0 | 2 |
| pilot#5870 | A+notes | AWN | Y | 6 | 2 | 0 | 4 | 0 | 0 | 2 |
| pilot#5871 | AWN | AWN | Y | 1 | 0 | 0 | 1 | 5 | 0 | 0 |
| pilot#5872 | AWN | AWN | Y | 1 | 1 | 0 | 0 | 4 | 0 | 0 |
| pilot#5875 | AWN | AWN | Y | 2 | 0 | 0 | 2 | 4 | 0 | 1 |
| console#427 | A+notes | AWN | Y | 7 | 1 | 2 | 4 | 3 | 0 | 1 |
| **total** | | | 11/14 Y | **52** | **18** | **9** | **25** | **44** | **1** | **18** |

Denominator 52, same composition as run 4 (ui#252 5, ui#261 3, ui#255 5, ui#254 3, ui#246 4, pilot#5799 2, pilot#5822 3, pilot#5868 5, pilot#5874 5, pilot#5870 6, pilot#5871 1, pilot#5872 1, pilot#5875 2, console#427 7).

## Metrics

- REQUEST-CHANGES caught: **3/3** (ui#252, ui#261, ui#255)
- Defect recall, all 14: (18 + 0.5×9)/52 = **43.3 %** (run 4: 44.2 %); plain HIT/hand n = 18/52 = **34.6 %** (run 4: 36.5 %)
- False notes per verdict: 1/14 = **0.07** (ui#254 "PR body does not say client-side bucketing", the same FALSE as run 4)
- REQUEST-CHANGES on human-approved PRs: **3/11** (ui#254, ui#246, pilot#5799 — the same three A+defects PRs as run 4; 6 RC verdicts total vs 3 hand)
- Defect-bearing approves matched: **9/11** (misses: pilot#5871 0/1, pilot#5875 0/2; run 4 missed pilot#5874 and pilot#5871)
- New valid findings: **44** (18 UNSURE; run 4: 35 / 18)
- Format failures (verdict `unknown`): **0**
- Mean review time: 1,010,071 ms / 14 = **72.1 s** (min 37.3 s pilot#5870, max 120.0 s pilot#5868; run 4: 67.5 s)
- Mean files_read: 71/14 = **5.1** (range 3–7; run 4: 5.0, range 2–7)

## Fixtures (the run-4 misses named in TASK-622 step 3)

- pilot#5874 D1 (past reset rolls +24h → 6 h pause) → **HIT** — defect 2 cites `ratelimit.go:96` verbatim and draws the fleet-wide 6 h consequence; the adjacent parser was opened and its failure input named ("resets 2pm" read at 2:01pm).
- pilot#5874 D3 (`Stop()` leaves `usageLimitResumeAt` and the owner) → **MISS** — `Stop()` is discussed only for lock order; no "what if `Start()` follows" input.
- pilot#5874 D2 (two alerts) → **MISS** — "Alert met: one alert per episode"; the runner's pre-existing `AlertEventTypeRateLimit` was not opened.
- pilot#5870 D4 (dirty refusal unreachable from the runner in direct mode / `git_clean` preflight) → **MISS** — the caller chain stops at `runner.go:4652`, one hop short of the preflight.
- pilot#5822 D2 (`merged_count` 0 for families autopilot never tracks) → **PARTIAL** — a note, not a defect, and only the autopilot-off half ("merged_count quietly drops toward 0"); Jira/Linear PRs and the `tickets_shipped` contradiction absent.
- pilot#5870 D2 (`GetCurrentBranch` error swallowed) → **HIT** — defect 1 names the swallow and its consequence.
- pilot#5868 D4 (`CIResult` is pre-merge) → **HIT** — defect 1 ties it to `controller.go:6246` `StagePostMergeCI` being set after the review starts.
- pilot#5875 D2 (reused gate output not pinned to the pushed HEAD) → **MISS** — "Reuse: met"; the self-review-commit path after the gates was not opened.

3 HIT / 1 PARTIAL / 4 MISS of the 8 named fixtures (the issue text says seven; eight are listed).

## Deltas vs run 4

- MISS → HIT (5): pilot#5868 D4 `CIResult` pre-merge · pilot#5868 D5 `localMergedDiff` untested · pilot#5874 D1 +24h roll · pilot#5870 D2 `GetCurrentBranch` swallowed · console#427 D7 `/metrics` proxy ungated.
- MISS → PARTIAL (3): pilot#5822 D2 `merged_count` · pilot#5874 D5 parser wording (via `not_verified`) · console#427 D2 duplicated switched rule.
- PARTIAL → HIT (1): pilot#5822 D1 Monday double fire + `/latest`.
- HIT → MISS (7): ui#255 D2 Memory counts on the docs tree · ui#254 D3 rolling windows vs calendar · ui#246 D1 mobile confirmation cards · pilot#5868 D1 cap per controller · pilot#5868 D3 attempt-once drops on transient failure · pilot#5875 D1 budget-killed command renders as evidence · console#427 D1 USDGate substring.
- PARTIAL → MISS (1): pilot#5870 D5 dirty test uses an untracked file (now read as a feature).
- Net: HIT 19 → 18, PARTIAL 8 → 9, MISS 25 → 25; recall 44.2 % → 43.3 %. Twelve defects changed state in a run with the same model and files_read; the prompt step moved *which* defects are found more than *how many*.

Whether the adjacent-code miss class moved:

- It moved where the adjacent code is one hop from the hunk and the hunk calls it: the `ratelimit.go` roll (called from `armUsageLimitPause`), `StagePostMergeCI` (set two hundred lines below the hook), the C13 proxy allowlist (the other USD path the issue's context names), the `GetCurrentBranch` swallow (in-hunk, a failure-case rule hit). 4 of the 8 fixtures are that shape and 3 of them hit; the fixture score is 3.5/8 against 0/8 in run 4.
- It did not move where the behaviour needs a second hop or a different subsystem: the runner's own `rate_limit` alert (dispatcher vs runner), the `git_clean` preflight (runner, ahead of the call the daemon stopped at), self-review commits after the gates (runner, after `appendAcceptanceEvidence`), `Stop()`/`Start()` state (needs a hypothetical input the "name the breaking input" rule did not produce — the failure cases written in notes are trivial ones: "if a card were conditionally rendered", "if the token changed").
- The cost is a new set of in-hunk "met" misses on things run 4 caught: 5 of the 7 HIT→MISS flips are inside the diff (`postMergeBudget()` per controller written as "Budget: met", attempt-once "flag set and saved before the goroutine starts", `allErrored` at `:322` behind the `:206` relabel, the USDGate substring, `DocsCounts` on the type the daemon already read for `memoriesRead`). The sibling-function read displaced the hunk read on those; ui#246 is the clearest case — `ChatWindow.vue` was opened as a sibling and produced a real NEW-VALID (shared poll timer) but its confirmation renderer, the hand's D1, was not seen.
- Notes-only hand reviews are unchanged as the weakest surface (pilot#5870 2/6, console#427 2/7) and the hand-note overlap grew instead: 44 NEW-VALID of which 15 are hand notes (pilot#5871 5/5, pilot#5872 3/4, pilot#5875 3/4). The step-3 prompt reads the same adjacent lines the hand's notes come from; it reaches the notes more often than the defects.
- Verdicts are unchanged (6 RC vs 3 hand, the same three over-strict A+defects PRs, 1 FALSE, 11/14 match); time +4.6 s mean, files_read flat. Nine NEW-VALID were verified here against the merge commits and are follow-up material: ChatWindow unmount stops the Research page's polling (ui#246), mock emits no `pr_merged` (ui#254), USDGate has no switched-to-own case (console#427), `LoadPendingApprovals` unfiltered by project and `/latest` 404 with the daily brief off (pilot#5799), deploy failure skips the post-merge review (pilot#5868), plus the stale comments in `dashboardShippedColors.ts`, `AppShell.vue` and `main.go`.
