# Learning: Do not enable the Claude desktop app's PR Auto-fix in Pilot sessions — autopilot owns the CI-fix and merge loop

## Summary
Founder instruction 2026-10-26: never offer or enable the Code tab's "Auto-fix" (and auto-merge) on a Pilot-repo PR. The daemon's autopilot (CI monitor, fix-request chain, merge) is the mechanism for PR follow-through; a second watcher that pushes fixes to the same branch would race it. Autopilot keys on Pilot-created PRs on pilot/GH-* branches, so a hand-made PR (e.g. a docs upgrade branch) is merged by hand after CI, or handed to Pilot as an issue in the first place.

## Context
After opening PR#5866 (docs Next.js 16 upgrade) from an interactive session, the wrap-up offered the app's Auto-fix toggle. Founder: "Don't use it. We have autopilot for this."

## Details
- The app binds the PR to the session and, with Auto-fix on, wakes the session on CI failure, merge conflict or review comment to push fixes. That duplicates autopilot's handleCIFailed → fix-request issue → fix PR chain and the self-close/supersede logic; two writers on one branch produce the non-FF push and duplicate-fix classes already recorded (#5853 duplicate fix request, #5762/#5864 stale-head pushes).
- Keep the session's PR binding (status read via get_status is fine); leave auto_fix, address_comments and auto_merge off.

## Recommended Approach
After `gh pr create` in an interactive session: read status once, report the PR, stop. Do not ask about Auto-fix. For a non-pilot branch, note that autopilot may not adopt it and the merge is manual.

## Related
- autopilot-selfclose-handoff-leaves-original-task-repickable
- infra-repicks-bypass-hard-cap-backoff-and-identical-failure-streak
