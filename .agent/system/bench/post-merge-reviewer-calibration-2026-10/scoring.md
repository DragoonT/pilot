# Scoring detail — post-merge reviewer calibration 2026-10-28

Rules: hand defects = numbered D*/Defects items plus explicit ✗ scope bullets; "Notes (no action)" excluded when a Defects section exists; for the two notes-only hand reviews (pilot#5870, console#427) the concrete notes are the defects. Daemon findings that match a hand *note* count NEW-VALID. Every daemon APPROVE-WITH-NOTES had an empty `defects` list; matches for those are judged on notes.

## ui#252 (hand RC / daemon RC)
- D1 Header Pool/org/Last-shipped bound to wire fields no backend sends → HIT
- D2 View ignores StatCard numerator/pill variants; N is window-scoped → MISS
- D3 Mobile glance still renders per-ticket USD on every tenant → MISS
- D4 PR body lacks make build/test/lint output and adapter name → MISS
- D5 Missing-field notes absent from PR body → MISS
- Extra: toDashboard wire mapping untested (tests stub getDashboard) → NEW-VALID
- Extra: Cost/Shipped degrade test rewritten to assert Time to PR → NEW-VALID
- Extra: no-$/tokens test sets no tenant → UNSURE · costTile.note on mobile tile unrequested → UNSURE

## ui#261 (hand RC / daemon RC)
- D1 Queue binds to project/parentId the console never sends → HIT
- D2 Execution meta binds to 3 fields never sent; N+1 fetch per card → PARTIAL
- D3 No build/test/lint evidence or adapter note → MISS (daemon: "not in the diff")
- Extra NEW-VALID: stale docblock · toBoardCard mapping untested · project filter pill no longer filters · onMounted no error handling · chipFor ignores exec
- Extra UNSURE: DashboardQueue.vue created though issue said "mount existing"

## ui#255 (hand RC / daemon AWN) — the missed REQUEST-CHANGES
- D1 "Needs API" list missing from PR body → PARTIAL (named, then not counted)
- D2 Memory card hides counts the docs tree already serves → MISS
- D3 Graph card is a dead prop → HIT
- D4 Panel bypasses ds-* vocabulary → MISS
- D5 No adapter note → MISS
- Extra NEW-VALID: tests mount with props only · loadContextDocs untested, instances[0], silent catch

## ui#254 (hand A+defects / daemon RC)
- D1 Two activity charts → HIT · D2 7D/30D truncated to newest 50 → PARTIAL · D3 rolling windows, no dates → MISS
- Extra: range switch does not re-request; colours differ → FALSE (hand accepted both)
- Extra: 30D bars overflow → UNSURE · now evaluated once at mount → NEW-VALID · tests skip adapter wiring → NEW-VALID

## ui#246 (hand A+defects / daemon RC)
- D1 Mobile Chat tab lost confirmation cards → MISS
- D2 Sub-agent tree/Context bind to events nothing emits → HIT · D3 mode never leaves the console → HIT · D4 PR body gaps → HIT
- Extra NEW-VALID: tests bypass toChatEvent · report = last text event · composer navigates when chat disabled
- Extra UNSURE: no-token test fixture · cumulative-count double counting

## pilot#5799 (hand A+defects / daemon RC)
- D1 Receipts digest fail-open on key_source=unknown → HIT · D2 Structured brief inherits fixed 09:00 window → MISS
- Extra NEW-VALID (7): pool has no producer · pasted make lint fails · gateway tests racy sleep · brief_payloads no retention · ClassifyFailure over-matches · oneLine splits runes · GenerateStructured vs Generate differ
- Extra UNSURE: pending-approvals path not tested end to end

## pilot#5822 (hand A+defects / daemon RC)
- D1 Monday daily+weekly fire same minute; /latest non-deterministic → MISS · D2 merged_count 0 for untracked families → PARTIAL · D3 PR body pastes FAIL → HIT
- Extra NEW-VALID: maybeCatchUpWeekly untested · WeeklySchedule copies hour field · weekly data built twice
- Extra UNSURE: merged_count source deviates

## pilot#5868 (hand AWN / daemon AWN)
- D1 Daily cap per controller → HIT · D2 follow-up >200 words / backticked paths → MISS · D3 attempt-once drops on transient failure → MISS · D4 CIResult pre-merge → HIT · D5 localMergedDiff untested → HIT
- Extra NEW-VALID: title not PR-number-first · ^1 misses rebase-merge commits · startup log prints empty model · review→fix→review loop
- Extra FALSE: "prompt passed as argv, E2BIG" (it goes through stdin)
- Extra UNSURE (3): SDK JSON tag names · negative review_id · ResolveModel nil guard

## pilot#5874 (hand AWN / daemon AWN)
- D1 reset rolls +24h → 6h pause → MISS · D2 double alert → MISS · D3 Stop leaves owner → MISS · D4 tests bypass processQueue → HIT · D5 parser vs current wording → MISS
- Extra NEW-VALID: "(cached)" evidence · comment split from code · epic runs finalize outside processQueue
- Extra UNSURE: max_pause-alone validation · severity vs platform breaker

## pilot#5870 (hand notes-only / daemon AWN)
- D1 no recovery ref for discarded commits → MISS · D2 GetCurrentBranch error swallowed → HIT · D3 no log on detach → MISS · D4 dirty refusal unreachable in direct mode → MISS · D5 test gaps → MISS · D6 PR body re-runs make → HIT
- Extra NEW-VALID: lint output shows SA4023 under a "pass" heading · UNSURE: mutation criterion not evidenced

## pilot#5871 (hand AWN, 1 defect / daemon AWN)
- D1 githubEventHasLabel exact-case → PARTIAL ("not verified")
- Extra NEW-VALID: fetch-error subtest pin · issue GET precedes needs-human backstop

## pilot#5872 (hand AWN, 1 defect / daemon AWN)
- D1 RecordDecision widening regresses ErrNoRows path → PARTIAL
- Extra NEW-VALID (4): cached test output · mutation checks not evidenced · "next poll tick retries" impossible · CancelFn mutated outside h.mu

## pilot#5875 (hand AWN, 2 defects / daemon AWN) — defect-bearing miss
- D1 budget-killed command renders as evidence → MISS · D2 reused gate output not pinned to pushed HEAD → MISS (daemon: "reuse: met")
- Extra NEW-VALID (5): epic/timeout paths pass nil gates · Classify on task ctx · budget-kill by string prefix · finalizeCtx WithCancel when nearly spent · reuse only unit-tested
- Extra UNSURE: recovery-ref assertion checks string

## console#427 (hand notes-only / daemon RC)
- D1 USDGate test substring hits nested → HIT · D2 three copies of "switched" rule → HIT · D3 second Service without Meter → MISS · D4 reportedUsdCents null → MISS · D5 percent_used denominator → MISS · D6 UI types USD as number → PARTIAL · D7 dashboard /metrics proxy → MISS
- Extra NEW-VALID: hideUSD before days validation (500 not 400) · UNSURE: platform fixture USDCents=0

## Totals
RC caught 2/3 · recall (17 + 3.5)/52 = 39.4 % · FALSE 2/14 = 0.14 per verdict · UNSURE 16 · NEW-VALID 44 · defect-bearing approves matched 10/11.

Miss class: reasoning past the visible hunks (~18/28), then PR-body evidence asks declined (~6). False class: spec-literal deviation without the documented reason. Daemon is stricter on verdict (7 RC vs 3) and softer on substance.
