# Pitfall: the acceptance-evidence step re-runs the quality gates inside the task budget — the task ctx dies during evidence and PR creation fails on the dead ctx (branch pushed, PR lost, re-pick from scratch)

## Summary
On the pilot repo the standard issue bullet "`make build`, `make test`, `make lint` pass — paste the output" makes the evidence runner repeat the 21–36-minute quality-gate run after the gates already passed. finalizeCtx (GH-5342) only grants a fresh window when the task ctx is already dead at call time; it is called before the push, so a deadline that blows during evidence leaves git.CreatePR and the recovery ref on the dead ctx: "pr-create failed after 3 attempt(s): failed to create PR: context deadline exceeded" with three attempts 300 ms apart and the SHA already pushed. 2026-10-26: GH-5861 twice, GH-5864, console-ui GH-280 (trivial 30 min). Each re-pick restarted from scratch (and until #5864 ships cannot push over the stale head).

## Context
Founder asked why the dashboard's outcomes column was red for the day. 26 completed vs 15 non-success rows; 7 were the cancelled C14 epic decomposition, 5 were "orphaned by daemon restart" from two hot self-upgrades, and 4 were this class. Signature in daemon.log: "Acceptance classification … items=N" followed by silence until the exact task deadline, then "PR creation failed, retrying" ×2 within a second.

## Details
- Timeline GH-5864: Claude 23 min → gates 21m34s → judge/self-review 1 min → evidence from 17:03:04 → deadline 17:17:54 (start 16:17:54 + 60m) → PR create fails.
- Per-command evidence timeout is 10 min (defaultAcceptanceEvidenceCommandTimeout) but every command is also bounded by the parent task ctx; the three make targets in one bullet run sequentially.
- Box config: executor.timeout complex 60m, medium 30m, simple 25m, trivial 15m (config.yaml `timeout:` block). Gates on the pilot repo take 21–36 min on the box, so any complex task that uses 25+ min of Claude time cannot also afford an evidence re-run.

## Recommended Approach
- Authoring: never put make build/test/lint paste-output bullets in pilot-repo issues (SOP Rule 5d). Use one targeted `go test -race ./pkg/ -run TestName` bullet per package; a package-wide `./internal/executor/` run is 10 min by itself.
- Durable fix: TASK-597 — re-derive finalizeCtx before PR create and the recovery ref; give evidence its own bounded budget; reuse the gate output for identical argv.
- Salvage: the pushed branch pilot/GH-N holds the work (the error names the SHA); open the PR by hand on that head so autopilot adopts it, instead of letting the re-pick redo the task.

## Related
- backend-timeout-finalization-on-expired-ctx-discards-committed-work
- autopilot-selfclose-handoff-leaves-original-task-repickable
