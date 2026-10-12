# Pitfall: escalateAndHold (internal/autopilot/controller.go) has 11 call sites but only 2 

## Summary
escalateAndHold (internal/autopilot/controller.go) has 11 call sites but only 2 revival paths: redriveSizeGuardHeldPR (gated on SizeGuardHoldActive, set only at the 'CI fix size guard fired' site) and reAdoptHeldRebasePR (RebaseHoldActive). A PR held for 'CI failure with zero gathered evidence' or a declined continuation stays in StageFailed forever even after a fix issue pushes a green head, because ProcessPR treats StageFailed as terminal and registerPR is a no-op for an already-tracked PR. Incident: pilot-console PR#388 2026-10-12 (custom CI gate, unparseable log → zero evidence → hold → continuation green → hand merge). Fix: TASK-528 generalizes the hold triple.

## Context
Discovered during development.

## Details
escalateAndHold (internal/autopilot/controller.go) has 11 call sites but only 2 revival paths: redriveSizeGuardHeldPR (gated on SizeGuardHoldActive, set only at the 'CI fix size guard fired' site) and reAdoptHeldRebasePR (RebaseHoldActive). A PR held for 'CI failure with zero gathered evidence' or a declined continuation stays in StageFailed forever even after a fix issue pushes a green head, because ProcessPR treats StageFailed as terminal and registerPR is a no-op for an already-tracked PR. Incident: pilot-console PR#388 2026-10-12 (custom CI gate, unparseable log → zero evidence → hold → continuation green → hand merge). Fix: TASK-528 generalizes the hold triple.

## Recommended Approach
Apply this knowledge when working on related topics.

## Related
- None documented

---
**Captured**: 2026-10-12
**Confidence**: 90%
**Concepts**: autopilot, ci, escalateandhold, redrive, hold
