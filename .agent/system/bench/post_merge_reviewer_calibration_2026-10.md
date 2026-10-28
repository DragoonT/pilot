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
