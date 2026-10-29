# Post-merge reviewer calibration — 2026-10-28 (v2.297.0, claude-sonnet-5-5)

**Run**: `pilot review-merge --json` on the founder box (v2.297.0, reviewer budget 200000 chars, no diff trimmed) over 14 merged PRs that carry a hand post-merge review. Raw outputs and the hand reviews: `post-merge-reviewer-calibration-2026-10/`. Scoring: one general-purpose agent, strict rules (HIT = same problem; PARTIAL = same area, weaker claim; FALSE = wrong on its face or contradicted by the hand review; UNSURE = unverifiable hedge). Task: TASK-612.

## Numbers vs thresholds

| Metric | Result | Threshold | |
|---|---|---|---|
| REQUEST-CHANGES caught | 2 of 3 (ui#252, ui#261; ui#255 missed) | ≥ 2 of 3 | PASS |
| Defect recall (HIT + ½ PARTIAL) / hand defects | 20.5 / 52 = **39.4 %** | ≥ 0.5 | **FAIL** |
| False notes per verdict | 2 / 14 = 0.14 | ≤ 1 | PASS |
| Defect-bearing approves matched | 10 of 11 (pilot PR#5875 named neither hand defect) | — | |
| New valid findings the human did not list | 44 across 14 PRs | — | |
| Unverifiable hedges ("could not see / please verify") | 16 (1.14 per verdict) | — | |

## Per-PR

| PR | hand | daemon | match | hand n | HIT | PARTIAL | MISS | NEW-VALID | FALSE | UNSURE |
|---|---|---|---|---|---|---|---|---|---|---|
| ui#252 | RC | RC | Y | 5 | 1 | 0 | 4 | 2 | 0 | 2 |
| ui#261 | RC | RC | Y | 3 | 1 | 1 | 1 | 5 | 0 | 1 |
| ui#255 | RC | AWN | N | 5 | 1 | 1 | 3 | 2 | 0 | 0 |
| ui#254 | A+defects | RC | Y | 3 | 1 | 1 | 1 | 2 | 1 | 1 |
| ui#246 | A+defects | RC | Y | 4 | 3 | 0 | 1 | 3 | 0 | 2 |
| pilot#5799 | A+defects | RC | Y | 2 | 1 | 0 | 1 | 7 | 0 | 1 |
| pilot#5822 | A+defects | RC | Y | 3 | 1 | 1 | 1 | 3 | 0 | 1 |
| pilot#5868 | AWN | AWN | Y | 5 | 3 | 0 | 2 | 4 | 1 | 3 |
| pilot#5874 | AWN | AWN | Y | 5 | 1 | 0 | 4 | 3 | 0 | 2 |
| pilot#5870 | AWN | AWN | Y | 6 | 2 | 0 | 4 | 1 | 0 | 1 |
| pilot#5871 | AWN | AWN | partial | 1 | 0 | 1 | 0 | 2 | 0 | 0 |
| pilot#5872 | AWN | AWN | partial | 1 | 0 | 1 | 0 | 4 | 0 | 0 |
| pilot#5875 | AWN | AWN | N | 2 | 0 | 0 | 2 | 5 | 0 | 1 |
| console#427 | A+notes | RC | Y | 7 | 2 | 1 | 4 | 1 | 0 | 1 |
| **total** | | | 12/14 | 52 | 17 | 7 | 28 | 44 | 2 | 16 |

RC = REQUEST-CHANGES, AWN = APPROVE-WITH-NOTES. Per-defect detail is in the scoring agent's output, kept in the raw folder as `scoring.md`.

## What the misses are (28)

- **~18: reasoning past the visible hunks.** Pre-existing code the diff interacts with (ratelimit rolls +24h, the git_clean pre-flight makes a guard unreachable, ErrNoRows path in a shared helper), sibling or cross-repo contracts (console DTOs, StatCard variants, the mobile ChatWindow), and time semantics (fixed 09:00 window, Monday collision, calendar bucket alignment). The reviewer sees the diff only; it has no checkout and no memory of the project.
- **~6: PR-body evidence asks it declined to check** although the body was supplied (ui#252/#261/#255 "no build/test/lint output or adapter note").
- **Structural:** every APPROVE-WITH-NOTES carries an empty `defects` list. The model fills DEFECTS only when it escalates. A reader of an AWN verdict gets prose, not an actionable list.

## What the false and the noise are

- 2 FALSE: a spec-literal "deviation" flagged without reading the documented reason (ui#254 range re-request/colour), and one factual error (pilot#5868 "prompt passed as argv" — it goes through stdin).
- 16 UNSURE hedges pad the notes. They are honest but cost reader time.
- Parser defect: the model writes defect lines with " - " separators; the comma-split parser leaves the claim inside the file field (see pilot#5799 defects).

## Verdict shape

Stricter on verdict, softer on substance. REQUEST-CHANGES on 7 of 14 vs the human's 3; escalation is driven by checklist hits (a wire field with no producer, a failed paste) rather than defect weight. It found 44 valid things the human did not list, mostly test-coverage gaps and evidence gaps. It missed 28 of 52 human findings, mostly things that need code outside the diff.

## Decision inputs (TASK-612 rule: below any threshold → prompt-tuning task with the misses as fixtures)

1. Recall fails the 0.5 bar. The miss class is "needs code outside the diff" — the exact gate for TASK-613 M2 (read-only checkout + Read/Grep/Glob tools). Dispatch M2.
2. Prompt and parser fixes (TASK-614 candidate): DEFECTS must be filled on APPROVE-WITH-NOTES too; read PR-body evidence when supplied; verdict weight by defect severity, not by checklist hit count; parse " - " separated defect lines; cap hedges ("at most three Not-verified items, as a list, not inline").
3. Memory injection (#5911, in flight) targets the known-class misses (unwired config, stale-snapshot guards, doc-vs-wire).
4. Until recall passes: keep hand review on tier-1 merges; read daemon REQUEST-CHANGES follow-ups; treat AWN as "no human needed" only after the TASK-614 rerun.

## Rerun recipe
Same 14 PRs, same command, after each change; compare the three numbers. Script and outputs: box `~/calibration/calib.sh`, local copies in the raw folder.

---

# Rerun 2 — 2026-10-29 11:51–11:56Z, v2.298.0 (TASK-614 prompt/parser · TASK-613 M1 memories, M2 checkout + tools, M3 confinement · TASK-610 budget)

Same 14 PRs, same scorer rules (hand defects 53 under this scorer's counting; run 1 counted 52). Raw: `run2/`.

| Metric | Run 1 (v2.297.0) | Run 2 (v2.298.0) | Bar |
|---|---|---|---|
| REQUEST-CHANGES caught | 2 of 3 | 2 of 3 (ui#255 approved again) | ≥2 |
| Defect recall | 39.4 % | **34.9 %** (18.5 / 53) | ≥ 0.5 — FAIL |
| False notes per verdict | 0.14 | **0.36** (5 / 14) | ≤ 1 |
| Daemon REQUEST-CHANGES on hand-approved PRs | 5 of 11 | 5 of 11 | — |
| Defect-bearing approves matched | 10 of 11 | 10 of 11 | — |
| New valid findings | 44 | 27 | — |
| Unverifiable hedges | 16 | 4 (now a capped NOT-VERIFIED list) | — |
| Contract: empty defect lists / RC without blocking | 10 empty | 0 / 0 | — |

## What changed and what did not
- **Structure is fixed.** Every verdict carries a defect list with severity tags; no REQUEST-CHANGES without a [blocking] item; hedges are a short list, not inline prose; dash-separated defect lines parse. Review time 16–33 s.
- **Substance did not move.** Recall fell within noise. The misses are the same class as run 1: behaviour in code adjacent to the diff (pre-existing paths, cross-repo consumers, design-token rules). The checkout and read tools were available; the only tool-use evidence in the logs is one denied Grep into the Go module cache (confinement working). Nothing logs how many files the model read in the CLI path, so tool use cannot be quantified from this run.
- **Over-escalation is unchanged and has one cause.** Four of the five REQUEST-CHANGES on human-approved PRs hang on a single [blocking] item about PR-body evidence (make output missing or showing a failure), not on code. The human waived those via CI. The severity rule in TASK-614 defines "a requirement of the issue not met" as blocking, and the model reads an evidence bullet as a requirement.
- **False notes rose** (0.14 → 0.36): claims contradicted by the PR body or the project's conventions (bucketing "not stated" when it was; ds-* called legacy; JSON routes called a deviation from "plain text").

## Decision inputs
1. Prompt rule, one line: PR-body evidence gaps are [minor] unless the pasted output shows a failing test or build for code the diff changed. Expected effect: daemon REQUEST-CHANGES falls from 7 to about 3, matching the human, and the review→fix→review loop stops firing on bookkeeping.
2. Recall is a model-capability question now, not a plumbing one. Cheapest test: rerun the same 14 with `post_merge_review.model: claude-opus-5-5` (one knob, no code) and compare recall. If Opus moves recall past 0.5, pay the per-review cost for the daemon reviewer only.
3. Make tool use measurable: the review-merge JSON and the "post-merge review" log line carry files_read; a rerun then shows whether the model opens counterpart files or answers from the diff.
4. Until recall passes: keep hand review on tier-1 merges; read daemon REQUEST-CHANGES follow-ups; treat APPROVE-WITH-NOTES as "no human needed" only for non-tier-1 merges.

---

# Run 3 — 2026-10-29 12:16–12:28Z, v2.298.0, reviewer model claude-opus-5-5 (founder call 12:16Z)

Same 14 PRs, same rules, denominator 53. Raw: `run3/`. Two outputs (pilot#5872, ui#246) came back `unknown`: the model broke the VERDICT line contract and the text was discarded (TASK-618 / #5946 keeps it next time).

| Metric | Run 1 Sonnet | Run 2 Sonnet + v2.298.0 | Run 3 Opus | Bar |
|---|---|---|---|---|
| REQUEST-CHANGES caught | 2 of 3 | 2 of 3 | **3 of 3** (ui#255 caught at last) | ≥2 |
| Defect recall, all 14 | 39.4 % | 34.9 % | 32.1 % (17 / 53) | ≥ 0.5 — FAIL |
| Defect recall, parsed PRs only | — | — | 36.2 % (17 / 47) | |
| False notes per verdict | 0.14 | 0.36 | **0.07** (1 / 14) | ≤ 1 |
| REQUEST-CHANGES on human-approved PRs | 5 of 11 | 5 of 11 | 5 of 11 | — |
| Defect-bearing approves matched | 10 of 11 | 10 of 11 | 7 of 11 (two unknown, 5874 and 5871 missed) | — |
| New valid findings | 44 | 27 | 34 | — |
| Format failures (verdict unknown) | 0 | 0 | **2** | — |
| Mean review time | ~25 s | ~21 s | 48 s | — |

## Reading
- **Opus caught the third REQUEST-CHANGES and made almost no false claims.** On the two PRs that matter most to the policy (wrong code shipped green) it is the better reviewer.
- **Recall did not move.** On the twelve parsed PRs it is 36.2 %, inside the noise of the Sonnet runs. The miss class is identical across all three runs: behaviour outside the diff hunks (adjacent code, callers, cross-repo contracts, project conventions). The model answers "met" from the diff where the human traced callers. The checkout and read tools are available since v2.298.0; nothing yet shows how much they are used (files_read lands with #5946).
- **Over-escalation is the same five PRs for the same reason**: a [blocking] item about PR-body evidence the human waived via CI. For three of them (5822, 5868, 427) it is the only blocking item. The severity rule in #5946 makes those minor.
- **Two format failures are a real regression** with Opus (markdown-wrapped or preceded VERDICT line, the TASK-591 prediction); they cost 11 points of headline recall. #5946 adds a tolerant parse and keeps the raw text.
- New verified findings worth a look: pilot#5874 `pilot status` calls /api/v1/status without the bearer the route requires; RetryBuffer read from DefaultSchedulerConfig, not the live scheduler.

## Decision inputs after three runs
1. Keep Opus for the reviewer: 3/3 REQUEST-CHANGES and the lowest false rate are the two properties the policy needs. Cost: ~2× review time, higher per-token price, bounded by the daily cap of 20.
2. Recall is bounded by behaviour, not model: the reviewer must trace callers. Next prompt change (TASK-619 candidate): for every changed exported function and every wire field, open the callers and the producer in the checkout and cite file:line; a requirement may be marked "met" only with a checkout citation; raise max-turns from 12 to 30; report files_read. Measure on the same 14.
3. Until recall passes 0.5: hand review stays on tier-1 merges; daemon REQUEST-CHANGES follow-ups are read; APPROVE-WITH-NOTES is "no human needed" for non-tier-1 merges only.
