# TASK-609: auto mode dispatches an issue whose scope overlaps an older issue's open, unmerged PR — SDK overlap guard holds on open PRs

**Status**: 🚀 S2 DISPATCHED 2026-10-27 18:06Z → studio-sdk#149 (`pilot`+`no-decompose`, Depends on #148 so it holds until S1 closes). Pilot side ships in TASK-608 P1 (bump + docs).
**Spec refs**: pilot#5897 (scrappydog). Docs promise: `docs/content/features/execution-modes.mdx` Auto Mode, "B waits for A's PR to merge".
**Origin**: external bug report 2026-10-27.

## Why (verified)
- SDK `sdk/integrations/github/poller.go` checkForNewIssues (~980) skips pilot-in-progress, pilot-done and processed issues first, then calls groupByOverlappingScope(candidates) (~1096). A dispatched A is in no group; B is the only member of its group and goes out as soon as the slot frees — i.e. the moment A's PR opens.
- Auto and parallel modes have no merge waiter; only sequential does (and its settings are inert until TASK-608).
- Scope signal is file paths in the issue body only (extractDirectoriesFromText); the docs say title, body and labels. Root-level files never group.
- Pilot has no dispatch-side scope guard; the only injection points are PollerDeps checkers, which see (taskID, projectPath) only. Pilot-only mitigation would duplicate the SDK regexes and cost one API call per candidate per poll. Fix belongs in the SDK.
- Operator workaround today: a "Depends on #A" line in B's body (hasPendingDependencies holds while A is open).

## Legs — studio-sdk

### LEG S2 — repo: qf-studio/studio-sdk — title: fix(github/poller): the auto-mode overlap guard holds an issue while an older overlapping issue is still open with an unmerged PR, bounded by PRTimeout
probe: present qf-studio/studio-sdk func groupByOverlappingScope
probe: present qf-studio/studio-sdk Deferring issue due to overlapping scope with older issue
probe: absent  qf-studio/studio-sdk overlaps open PR of older issue

## Context

Reported as qf-studio/pilot#5897. Depends on #148 (same file; this leg uses the PRTimeout it adds). In checkForNewIssues in `sdk/integrations/github/poller.go`, the loop first drops every open issue that carries the in-progress label, the done label, or is in the processed map, and only then groups the remaining candidates by overlapping scope. So the guard only serializes issues that are both still waiting. Once the older issue A is dispatched, it leaves the candidate set; the younger overlapping issue B becomes the sole member of its group and is dispatched as soon as a slot frees, which with max_concurrent 1 is the moment A's PR opens. B is built on a base without A's change and conflicts after A merges. The host docs promise "B waits for A's PR to merge". In one real run A's PR was created at 02:14:23Z and B was labelled in-progress at 02:14:25Z.

## Implementation

1. Build a holder set in checkForNewIssues before grouping: every open issue from the fetched list that was skipped as in-progress, done, or processed (an open issue with the done label means its PR is not merged yet; an in-progress issue is running). Keep each holder's scope directories (same extractDirectoriesFromText on the sanitized body) and its issue number and CreatedAt.
2. After grouping, for each candidate that would be dispatched, intersect its scope directories with each holder's. On a hit, defer the candidate and log at Info "Deferring issue: overlaps open PR of older issue" with number, holder number and the shared directory. Only older holders hold (holder CreatedAt before the candidate's), so a newer in-flight issue never blocks an older candidate.
3. Bound the hold with p.prTimeout: keep an in-memory map from holder number to the time the poller first saw it as a holder; once that age exceeds prTimeout, the holder no longer holds (log once at Warn "overlap hold expired") so a PR nobody reviews cannot wedge the lane forever. Clear the map entry when the holder issue is no longer open or no longer labelled.
4. Apply in auto mode and parallel mode (sequential already serializes everything). Leave sequential untouched.
5. Metrics: increment the existing deferred counter (or add one labelled reason=open_pr_overlap) so hosts can see holds.
6. Tests, table-driven, with the fake GitHub client already used by the poller tests: A in progress with an open issue, B overlapping → B deferred; A done-labelled but issue open → B deferred; A's issue closed → B dispatched; holder older than prTimeout → B dispatched with the expiry warning; non-overlapping C dispatched while A holds; A newer than B → B dispatched.

## Acceptance

- With A in progress and B naming a path in the same directory, the next poll logs the deferral line for B and dispatches nothing for B.
- When A's issue closes, the following poll dispatches B.
- When the holder has been held longer than prTimeout, B is dispatched and the expiry warning is logged once.
- A candidate with no overlapping holder is dispatched as today.
- `go test -race ./sdk/integrations/github/ -run TestCheckForNewIssuesOpenPROverlap` passes; paste the output into the PR body.
- remove the holder intersection so only waiting candidates are grouped -> TestCheckForNewIssuesOpenPROverlap_InProgressHolderDefers fails
- remove the prTimeout expiry -> TestCheckForNewIssuesOpenPROverlap_ExpiredHolderReleases fails
- remove the CreatedAt ordering so newer holders also hold -> TestCheckForNewIssuesOpenPROverlap_NewerHolderDoesNotBlock fails

## Out of scope

- Scope extraction from title or labels, and root-level file collisions (docs will be corrected to body paths in the pilot leg).
- Sequential-mode behaviour.
- Host-side wiring and docs (qf-studio/pilot leg in TASK-608 P1).

## Refs

- https://github.com/qf-studio/pilot/issues/5897
- #148

## Refs

- S2 → https://github.com/qf-studio/studio-sdk/issues/149
