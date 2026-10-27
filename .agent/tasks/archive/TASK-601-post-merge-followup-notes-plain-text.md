# TASK-601: post-merge follow-up issue — Reviewer Notes rendered without backticks (base-presence gate)

**Status**: ✅ Merged 2026-10-27 10:28Z — pilot#5882 → PR#5886 (11 lines). Post-merge review posted 2026-10-27 **APPROVE** (all three scope items landed, whole-body no-backtick assertion, pin holds). Ready to archive.
**Spec refs**: TASK-598 / #5873, PR#5876 review comment (APPROVE-WITH-NOTES), SOP `sops/onboarding/new-project-issue-authoring.md` Rule 3b.
**Origin**: post-merge review 2026-10-27 — own read + independent second read + `go test -race` + five mutation pins (all hold).

## Why
`CreatePostMergeReviewIssue` now renders defect locations in plain text, but the `## Reviewer Notes` section still goes through `sanitizePostMergeField` (backticks kept). The base-presence gate extracts paths from backtick spans over the whole body (`backtickSpanRe`, `internal/executor/dependency_detector.go`), so a counterpart path cited in Notes still parks the follow-up issue — the hold GH-5873 set out to prevent.

## Legs — pilot (daemon)

### LEG N1 — repo: qf-studio/pilot — issue #5882
Body as filed (Context / Scope / Acceptance / Out of scope). One targeted `-run` evidence bullet, no gate re-runs (SOP Rule 5d).

## Review notes carried from PR#5876 (no action)
- PR comment also lost backticks (shares `formatPostMergeDefects`); allowed by spec.
- `NewPostMergeReviewBudget(cap<=0)` denies forever; unreachable from config (wiring calls `EffectiveDailyCap`).
- `wirePostMergeReviewer` is a budget factory — a second call would make a second cap.
- Label dedup is case-sensitive; GitHub tolerates duplicate spellings.
- Shared cap is in-memory; resets on restart / hot self-upgrade.

## Refs
- https://github.com/qf-studio/pilot/issues/5882
- https://github.com/qf-studio/pilot/pull/5876#issuecomment-6438308727
