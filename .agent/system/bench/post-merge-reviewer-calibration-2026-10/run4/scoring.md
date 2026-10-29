# Scoring detail — run 4 (post-merge reviewer calibration 2026-10, daemon outputs of 2026-10-29 21:53–21:59Z, model claude-opus-5-5)

Rules: hand defects = numbered D*/Defects items plus explicit ✗ scope bullets, "Notes (no action)" excluded when a Defects section exists, the concrete notes are the defects for the two notes-only hand reviews (pilot#5870, console#427); each hand defect is HIT (same problem) / PARTIAL (same area, weaker claim) / MISS; each unmatched daemon finding is NEW-VALID (real, verifiable, or matches a hand note) / FALSE (wrong on its face or contradicted by the hand review) / UNSURE (unverifiable hedge); run 4 APPROVE-WITH-NOTES outputs carry a non-empty `defects` list, so each PR is judged on `defects` first, then `notes`, then `not_verified` only where it names a concrete problem; verdict match = Y when both are RC or both are non-RC (A+defects / A+notes / AWN = non-RC), "partial" only for a one-defect hand review that the daemon PARTIAL-matched. Claims marked (verified) were checked against the merge commit in the repo on disk.

## ui#252 (hand RC / daemon RC)
- D1 Header Pool/org/Last-shipped bound to wire fields no backend sends → HIT (defects 1–4: `httpAdapter.ts:1046` no producer for `orgName`/`lastShippedAt`/`poolPercentUsed`, `:1016` `timeToPrMinutes`; `DashboardView.vue:89` "the view never calls `getAllowance`"; `:84` real org source is `auth.org?.name`)
- D2 View ignores StatCard numerator/pill variants; N is window-scoped, not billing-month → PARTIAL (defect 8 `DashboardView.vue:305`: Delivered misses the `text-ds-green` numerator variant and `/100` is a literal; nothing on the Review pill variant or on `stats.shipped` vs allowance `included_tickets`)
- D3 Mobile glance still renders per-ticket USD on every tenant → MISS (notes see the Cost/Shipped note on the mobile glance at `:353` and call it a documented trim)
- D4 PR body lacks make build/test/lint output and adapter name → PARTIAL (named only in `not_verified`: "no `## Evidence` block … green CI is the only signal"; not a defect, adapter name not mentioned)
- D5 Missing-field notes absent from PR body → MISS
- Extra: `toDashboard` wire mapping untested, tests stub `getDashboard` (defect 5) → NEW-VALID
- Extra: no-$/tokens test sets no platform-key tenant (defect 6) → UNSURE · inline `Math.round` formatting "style point only" (defect 9) → UNSURE
- (defect 7 "adapter/mock/fixtures lockstep" is D1 restated; defect 2 `timeToPrMinutes` is inside D1 — not counted separately)

## ui#261 (hand RC / daemon RC)
- D1 Queue binds to `project`/`parentId` the console never sends → HIT (defect 1 `httpAdapter.ts:589`, `queue.ts:57` `card.project ?? NO_PROJECT` → one "Board" group)
- D2 Execution meta binds to 3 fields never sent; N+1 fetch per card → PARTIAL (defect 3 names "one `getCardExecution` request per card on mount" at `DashboardQueue.vue:28`; nothing on `durationMs`/`linesAdded`/`linesRemoved` having no producer)
- D3 No build/test/lint evidence or adapter note → HIT (defect 9 "There is no `## Evidence` block")
- Extra NEW-VALID: `toBoardCard` mapping untested, spec mocks the whole adapter (defect 2) · stale `DashboardShippedByProject` / GH-243 docblock refs (defects 4–5, hand N4) · project filter pill no longer filters the Queue (defect 6) · `chipFor` ignores `exec` (defect 7, hand N1)
- Extra UNSURE: "PR goes outside the scope fence, builds the GH-257 sibling" (defect 3; the hand records PR #260 was closed and its code merged inside #261) · docblock cites "Figma 2026-10" instead of a `design/<file>.html` (defect 8)

## ui#255 (hand RC / daemon RC) — the run-1 missed REQUEST-CHANGES, caught this run
- D1 "Needs API" list missing from PR body → HIT (defect 1, blocking)
- D2 Memory card hides counts the docs tree already serves → HIT (defect 4 `ContextPanel.vue:82`: Memory header hardcoded `—` though `DocsCounts {patterns; pitfalls; learnings; decisions}` is produced at `httpAdapter.ts:281`)
- D3 Graph card is a dead prop → PARTIAL (defect 2: thresholds "made up by the frontend", should go to the API owner; the never-passed `graph` prop at `DashboardView.vue:367` is cited as mitigation, not as the defect)
- D4 Panel bypasses `ds-*` vocabulary → MISS (notes: "16px padding and 13px rows: met")
- D5 No adapter note → MISS
- Extra NEW-VALID: Docs header client-recounts `entries.length` against the `types.ts` "never client-recount" warning (defect 5, hand N4) · no test covers `loadContextDocs` or the mount in `DashboardView` (defect 6)
- Extra UNSURE: Context column hidden below `md` (defect 3; verified true at the merge — `hidden gap-4 md:grid` at `:324`, mobile block `:373` has no `ContextPanel` — but the mobile glance is the pre-existing dashboard design, so whether it is a problem is a design call) · docblock cites no design file (defect 7)

## ui#254 (hand A+defects / daemon RC)
- D1 Two activity charts → HIT (defect 1 `DashboardView.vue:339/342`)
- D2 7D/30D truncated to newest 50 → PARTIAL (`not_verified`: "whether `/api/v1/board/activity` returns the full 30-day history or a capped page … 30D bars may undercount"; not run to ground, not a defect)
- D3 Rolling windows ending at `now`, no dates in the tooltip → HIT (defect 6 `DashboardActivityChart.vue:20`: "counted back from that moment, not from calendar day or hour boundaries"; tooltip dates not mentioned)
- Extra: "PR body must say bucketing is client-side; it does not" (defect 2, blocking) → FALSE (hand: "bucketed client-side, stated in PR body and docblock")
- Extra NEW-VALID: `now` evaluated once at mount, long-open dashboard goes stale (second half of defect 6) · `bg-needs-you` is magenta, deviation documented (defect 4, hand N1) · no test covers `loadBoardActivity` wiring or the chart mount (defect 7)
- Extra UNSURE: docblock cites Figma not `design/dashboard-v4.html` (defect 5) · 30 bars may overflow at `md` (`not_verified`)
- (defect 3 "docblock hides that DashboardView uses the old chart too" is part of D1)

## ui#246 (hand A+defects / daemon RC)
- D1 Mobile Chat tab lost confirmation cards → HIT (defect 8 `ChatView.vue:1`: "Confirmation cards … have no renderer on the new page, so mobile users cannot act on them")
- D2 Sub-agent tree/Context bind to events nothing emits → HIT (defect 1 `httpAdapter.ts:897`)
- D3 `mode` never leaves the console → HIT (defect 2 `httpAdapter.ts:1649`: nothing consumes `mode`, "the RESEARCH/DOCS pills do nothing")
- D4 PR body gaps: adapter line, missing-event-field list → HIT (defects 3 and 5)
- Extra NEW-VALID: no test for the new `toChatEvent` fields or the `mode` body; `ChatView.spec.ts` writes fixtures into `chat.messages` and stubs `chat.send` (defect 4) · `ChatSendOptions` docblock now sits on `ChatMode` (defect 6; verified at the merge, `types.ts:464-467`)
- Extra UNSURE: `text-ds-text/60` opacity dialect vs CLAUDE.md token dialect (defect 7; the hand accepted that exact class as the spec's "60%")

## pilot#5799 (hand A+defects / daemon RC)
- D1 Receipts digest fail-open on `key_source=unknown` → HIT (defect 1 `receipts.go:345`, cites the founder-tenant pitfall; defect 2 `formatReceiptsTotal` is the same defect's second function)
- D2 Structured brief inherits the fixed 09:00→09:00 window → MISS
- Extra NEW-VALID: `SetPoolSource` has no production caller, `pool` always null (defect 3, hand N1) · pasted `make lint` fails on SA4023 in `cmd/pilot/tunnel.go` (defect 4) · `brief_payloads` has no retention (defect 5, hand N5)
- Extra UNSURE: gateway-only mode has no `briefs.NewScheduler` so the routes serve only polling-mode payloads (`not_verified`, "I didn't trace whether that mode is used")

## pilot#5822 (hand A+defects / daemon AWN)
- D1 Monday daily+weekly fire the same minute; `/latest` non-deterministic → PARTIAL (defect 2 `scheduler.go:79`: "Monday gets two briefs"; nothing on `brief_payloads` ordering, `/latest` or the missing `kind` filter)
- D2 `merged_count` 0 for task families autopilot never tracks → MISS (notes: `merged` from `execution_events` "met", documented deviation)
- D3 PR body pastes FAIL for `make test`/`make lint` → HIT (defect 3; `not_verified` adds the "36099 lines omitted" point the hand also makes)
- Extra NEW-VALID: weekly catch-up can never fire — `catchUp` looks up `GetLastBriefSent("telegram", kind)` but deliveries are recorded as `telegram:<chat>`, so with `requirePrior` the record is always nil (defect 1; verified at merge `b8fa430`: `delivery.go:235` `Channel: fmt.Sprintf("telegram:%s", …)`, `scheduler.go:336` exact-match lookup, `:376` `requirePrior && lastRecord == nil`; stronger than hand N4)
- (`not_verified` "no consumer for `kind`/`weekly` in the checkout" is a hedge, not counted)

## pilot#5868 (hand AWN / daemon AWN)
- D1 Daily cap per controller → HIT (defect 2 `post_merge_review.go:172`, "N projects × daily_cap")
- D2 Follow-up issue >200 words / backticked cross-repo paths trip the SOP gates → MISS
- D3 Attempt-once drops the review on transient failure; ledger skipped when `commentID <= 0` → HIT (defect 5 `post_merge_review.go:144`)
- D4 `CIResult` is pre-merge → MISS (notes: "passes … the CI status" as met)
- D5 `localMergedDiff` untested → MISS
- Extra NEW-VALID: title is `fix(#N):` not PR-number-first (defect 1, hand note) · budget in memory only, restart resets the day's count (defect 3) · startup log prints empty `pmr.Model` on fallback (defect 6) · PR body has no Evidence block with the `go test -race` output (defect 7; verified — body has Summary/Changes/Review only)
- Extra UNSURE: cap test does not assert the "logged" part (defect 4)

## pilot#5874 (hand AWN / daemon AWN) — defect-bearing miss
- D1 Past reset rolls +24h → 6h pause → MISS
- D2 Double alert (runner `rate_limit` + `usage_limit_pause`) → MISS (defect 2 is about two INFO log lines, not two alerts)
- D3 `Stop()` leaves `usageLimitResumeAt` and the owner → MISS
- D4 Three dispatcher tests call `armUsageLimitPause` directly → MISS (notes: "They drive a real Dispatcher and ProjectWorker")
- D5 Parser not verified against current Claude Code wording → MISS
- Extra NEW-VALID: `pilot status` GETs `/api/v1/status` with no `Authorization` while the route sits on the auth-protected mux, so the pause line silently disappears on an auth-enabled daemon (defect 1; verified at merge `076bb48`: `commands.go:311` plain `client.Get`, `server.go:309` `auth.Middleware(apiMux)`) · gateway test output pasted as `(cached)` (`not_verified`)
- Extra UNSURE: two INFO lines where the issue asks for one (defect 2) · severity "warning" by substitution for a breaker alert with no engine rule (defect 3) · status test feeds hand-written JSON (defect 4, self-rated "risk is low")

## pilot#5870 (hand notes-only / daemon AWN)
- D1 No recovery ref for the discarded commits → MISS
- D2 `GetCurrentBranch` error swallowed → MISS (notes quote `if curErr == nil && current == branchName` as "met")
- D3 No log on the detach path → MISS
- D4 Dirty refusal unreachable from the runner in direct mode → MISS
- D5 Test gaps: dirty case uses an untracked file, no detached-HEAD start → PARTIAL (defect 2's evidence: "the dirty test case at `git_test.go:2279` only exercises the untracked-file case")
- D6 PR body re-runs `make` against the replaced bullet → HIT (defect 3, plus the SA4023 lint failure under it)
- Extra NEW-VALID: after `detachHeadAt`, a failing `DeleteBranch`/`checkoutNewBranchFrom` leaves the clone detached and the error does not say so (defect 1; verified at merge `c699647`, `git.go:199-209` error paths return without restoring)
- Extra UNSURE: a lone untracked file triggers the refusal though `checkout --detach` would carry it (defect 2's claim; the spec says dirty → refuse) · mutation bullet not run (`not_verified`)

## pilot#5871 (hand AWN, 1 defect / daemon AWN)
- D1 `githubEventHasLabel` exact-case vs SDK/webhook `EqualFold` → MISS
- Extra NEW-VALID: fetch-error subtest never pins "proceeds with `ev.Labels`" (defect 1, hand note) · GH-5056 needs-human backstop unreachable once the live fetch succeeds (defect 2) · `resolveAutopilotFixBranch`/`taskDesc`/`AcceptanceCriteria` still read the stale snapshot (defect 3, hand note) · both mutation bullets recorded "Not verified", not run (`not_verified`, hand note)

## pilot#5872 (hand AWN, 1 defect / daemon AWN)
- D1 `RecordDecision` widening regresses the `sql.ErrNoRows` unlinked-request path → HIT (defect 2 `manager.go:517`: waiter and armed button alive until the dispatch timeout, `gateway/approvals.go:294`; run 1 was PARTIAL)
- Extra NEW-VALID: "next poll tick retries" impossible — rehydrated path loses a failed write for good, fresh path retries only via the async waiter (defect 1, hand note) · pasted `go test -race` output is `(cached)` (defect 3, hand note) · mutation bullets "run manually", not evidenced (`not_verified`, hand note)

## pilot#5875 (hand AWN, 2 defects / daemon AWN)
- D1 Budget-killed command inside a mixed item renders as evidence → HIT (defect 1 `acceptance_evidence_run.go:322`: `allErrored` stays false, `NotVerifiedReason` never set, item lands under `## Evidence`; the "partial output reads as a pass" angle is not drawn)
- D2 Reused gate output not pinned to the pushed HEAD → MISS (notes: "Reuse: met")
- Extra NEW-VALID: `finalizeCtx` grants a window only once the deadline has blown (defect 2, hand note) · WARN fires once per reused command, not once (defect 3, hand note) · epic and timeout-salvage paths pass `nil` gates (defect 4)
- Extra UNSURE: three mutation claims checked "by reading" only (`not_verified`; the hand ran them)

## console#427 (hand notes-only / daemon AWN)
- D1 USDGate test substring also matches nested `usage.key_source` → HIT (defect 2 `routes_test.go:662-663`)
- D2 Three copies of the "switched this period" rule → MISS (notes: "uses the same current-period switched rule")
- D3 Second `allowance.Service` without `Meter` → MISS
- D4 `reportedUsdCents` `null` → omitted wire change → MISS
- D5 `percent_used` denominator includes pack tickets → MISS
- D6 UI types USD as `number`, reads only nested `key_source` → PARTIAL (`not_verified`: "no SPA/frontend client … in this checkout, so client handling of the now-omitted keys was not checked")
- D7 Dashboard cost via the `/metrics` instance proxy is ungated → MISS (notes: "Dashboard gate: not applicable")
- Extra NEW-VALID: no make build/test/lint output pasted (defect 1; the hand noted the gap and accepted CI) · `KeySourceForOrg` has no test of its own, usage gate tested only through `fakeKeys` (defect 3; verified — the only `_test.go` hit at merge `b823a0d` is the fake)

## Per-PR table

| PR | hand | daemon | match | hand n | HIT | PARTIAL | MISS | NEW-VALID | FALSE | UNSURE |
|---|---|---|---|---|---|---|---|---|---|---|
| ui#252 | RC | RC | Y | 5 | 1 | 2 | 2 | 1 | 0 | 2 |
| ui#261 | RC | RC | Y | 3 | 2 | 1 | 0 | 4 | 0 | 2 |
| ui#255 | RC | RC | Y | 5 | 2 | 1 | 2 | 2 | 0 | 3 |
| ui#254 | A+defects | RC | N | 3 | 2 | 1 | 0 | 3 | 1 | 2 |
| ui#246 | A+defects | RC | N | 4 | 4 | 0 | 0 | 2 | 0 | 1 |
| pilot#5799 | A+defects | RC | N | 2 | 1 | 0 | 1 | 3 | 0 | 1 |
| pilot#5822 | A+defects | AWN | Y | 3 | 1 | 1 | 1 | 1 | 0 | 0 |
| pilot#5868 | AWN | AWN | Y | 5 | 2 | 0 | 3 | 4 | 0 | 1 |
| pilot#5874 | AWN | AWN | Y | 5 | 0 | 0 | 5 | 2 | 0 | 3 |
| pilot#5870 | A+notes | AWN | Y | 6 | 1 | 1 | 4 | 1 | 0 | 2 |
| pilot#5871 | AWN | AWN | Y | 1 | 0 | 0 | 1 | 4 | 0 | 0 |
| pilot#5872 | AWN | AWN | Y | 1 | 1 | 0 | 0 | 3 | 0 | 0 |
| pilot#5875 | AWN | AWN | Y | 2 | 1 | 0 | 1 | 3 | 0 | 1 |
| console#427 | A+notes | AWN | Y | 7 | 1 | 1 | 5 | 2 | 0 | 0 |
| **total** | | | 11/14 Y | **52** | **19** | **8** | **25** | **35** | **1** | **18** |

Denominator: 52 under the stated rules (ui#252 5 = D1–D3 + ✗ make-output + ✗ missing-field notes; ui#261 3; ui#255 5 = D1–D4 + ✗ adapter note; ui#254 3; ui#246 4 = D1–D3 + ✗ PR body; pilot#5799 2; pilot#5822 3 = D1–D2 + ✗ FAIL pasted; pilot#5868 5; pilot#5874 5; pilot#5870 6 notes; pilot#5871 1; pilot#5872 1; pilot#5875 2; console#427 7 notes). Run 1 also counted 52; runs 2–3 reported 53. The one-item difference is not recoverable from the hand reviews — the candidates are ui#246's ✗ PR-body bullet counted as two (adapter line + missing-field list), ui#252's two ✗ StatCard bullets counted separately from D2, or pilot#5799's pasted `make lint` FAIL counted although its scope bullet is ✓-via-CI. Recall below uses 52; on 53 it would be 43.4 % / 35.8 %.

## Metrics

- REQUEST-CHANGES caught: **3/3** (ui#252, ui#261, ui#255 — ui#255 was missed in run 1)
- Defect recall, all 14: (19 + 0.5×8)/52 = **44.2 %**; plain HIT/hand n = 19/52 = **36.5 %**
- False notes per verdict: 1/14 = **0.07** (ui#254 "PR body does not say client-side bucketing")
- REQUEST-CHANGES on human-approved PRs: **3/11** (ui#254, ui#246, pilot#5799 — all three are A+defects hand verdicts; 6 RC verdicts total vs 3 hand)
- Defect-bearing approves matched: **9/11** (misses: pilot#5874 0/5, pilot#5871 0/1)
- New valid findings: **35** (18 UNSURE)
- Format failures (verdict `unknown`): **0**
- Mean review time: 944,349 ms / 14 = **67.5 s** (min 35.8 s pilot#5870, max 95.7 s pilot#5868)
- Mean files_read: 70/14 = **5.0** (range 2–7)

## Observations

- The 25 misses still split the run-1 way: ~18 are behaviour outside the diff hunks — pre-existing adjacent code (`ratelimit.go` +24h roll, the runner's second alert, `generator.go`'s fixed 09:00 window, the `git_clean` preflight that makes the dirty refusal unreachable, self-review commits after the gates), cross-repo contracts (console#427 D6/D7, ui#255 `ds-*` tokens), cross-subsystem facts (`merged` events only from autopilot, `detectEpic` on a >200-word follow-up, `CIResult` being pre-merge) and adjacent-code duplication (three copies of the switched rule, second `Service` without `Meter`). The class holds.
- files_read 2–7 did not move that class. The extra reads go to producers and consumers of the wire fields the diff names — that is exactly where the new HITs come from (ui#246 D1/D3, ui#252 D1 down to `auth.org?.name` and `getAllowance`, pilot#5872's ErrNoRows path, the pilot#5822 catch-up key mismatch) — not to the callers and sibling parsers the hand reads. Recall does not track files_read: pilot#5874 read 7 files for 0/5, pilot#5870 read 2 for 1.5/6.
- ~4 misses are inside the hunk and were written as "met": `if curErr == nil && current == branchName` quoted verbatim as meeting the spec (5870 D2), the detach path "met" with no log (5870 D3), "They drive a real Dispatcher and ProjectWorker" for tests that call `armUsageLimitPause` directly (5874 D4), "passes the CI status" for a value that is pre-merge (5868 D4). The "writes 'met' from the diff" half of the run-1 description still holds — the model confirms the text of the spec bullet against the text of the hunk, not the behaviour.
- The PR-body evidence class from run 1 (~6 declined asks) is mostly gone: missing or failing pasted output is now a defect on ui#261, ui#246, pilot#5822, pilot#5870, pilot#5868, console#427. What remains missed is the sub-clause inside the same bullet — the adapter-name line (ui#252, ui#255) and the "name the missing field in the PR body" ask (ui#252 D5).
- Verdicts are still stricter than the hand (6 RC vs 3) but FALSE fell from 2 to 1 and the three over-strict RCs all land on PRs the hand itself tagged A+defects, with at least one blocking-grade HIT each. Notes-only hand reviews remain the weakest surface (pilot#5870 1.5/6, console#427 1.5/7): those hand notes are semantics and adjacent-code observations, which the daemon's producer/consumer grep does not reach.
- NEW-VALID is down from 44 to 35 with fewer, more concrete items; five of them were verified against the merge commit here and are real follow-up material: weekly catch-up never fires (#5822), `pilot status` unauthenticated against the protected mux (#5874), detached clone on a failed recreate (#5870), `ChatSendOptions` docblock displaced (ui#246), `KeySourceForOrg` untested (console#427).
