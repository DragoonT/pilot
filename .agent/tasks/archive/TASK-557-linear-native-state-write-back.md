# TASK-557: Linear native state write-back on start, PR and merge (Jira verified by category fallback)

**Status**: ✅ DONE 2026-10-15 — PR#5702 (merged 11:41Z) + fast-follows PR#5704 (12:22Z) + PR#5706 (13:35Z), all in **v2.287.0** (box self-upgraded 14:07Z). **Live proof 15:06–15:25Z on QF-301/302**: `leg=start` transition logged, ✅ completion comment with the GitLab MR URL posted, issues now `Done` (the Done move is not Pilot's — no merge leg for GitLab MRs; `in_review` unconfigured so the PR leg is comment-only). Open follow-up: #5708 (review defects of PR#5706: needs_human push-failed text, superseded must not move state, double `failed:` prefix, stale no-PR text, docs paragraph).
**Created**: 2026-10-15
**Assignee**: Pilot (one issue, this repo)

---

## Context

**Problem**:
Pilot completes Linear-sourced tasks (`LIN-<TEAM>-<n>`) but never moves the Linear
issue's workflow state. Live evidence 2026-10-15 (box key, nine issues `QF-290..298`,
all with completed executions and MRs 12–15 opened): every issue is still in
`Backlog`, carries `pilot` + `pilot-done`, has exactly one "🤖 Pilot started" comment,
no completion comment, no PR link, and a history made of label changes only.
The daemon log has no state-write line and no error — the only finish-time Linear
line is `Not registering PR with autopilot … not a GitHub PR URL`.

Root cause (nav-research 2026-10-15): the Linear leg is labels + start comment only.

- `cmd/pilot/poller_linear.go:437-466` — handler closure calls `notifier.NotifyTaskStarted` (comment) then `handleLinearIssueWithResult`. Nothing runs on the result.
- studio-sdk v0.38.3 linear poller.go lines 310 and 320-333 — adds/removes `pilot-in-progress`/`pilot-done`/`pilot-failed` labels, errors swallowed with `_ =`.
- studio-sdk linear notifier.go lines 54, 77 and 86 — `NotifyTaskCompleted`, `NotifyTaskFailed`, `LinkPR` exist; no production caller on the poll path.
- studio-sdk linear sync.go line 317 `SyncAdapter.TransitionState(ctx, nativeID, stateNameOrUUID)` and linear client.go line 231 `UpdateIssueState` exist; **zero callers** anywhere in the pilot module (grep verified; only Plane and GitHub call their own `UpdateIssueState`).
- `internal/adapters/linear/types.go:6-24` has no `transitions` config; the example yaml and `docs/content/integrations/linear.mdx` document none. The docs table "Status Notifications" (docs linear.mdx lines 199-210) promises Completed/Failed comments the poll path never posts.
- Autopilot's merge leg `notifyJiraDone` (`internal/autopilot/controller.go:5484-5507`) is gated on the pilot/JIRA- branch prefix; pilot/LIN-* branches fall through untouched.

Not a regression: the adapter has behaved this way since GH-323 introduced the notifier.

**Jira is NOT broken.** `jiraSDK.NewNotifier` (studio-sdk jira notifier.go lines 45-55)
falls back to the status-category transition (`indeterminate` on start, `done` on merge)
when `transitions.*` is empty, and the box config has no `transitions` block. The Jira
pattern — notifier owns the transition, called from the handler closure and from the
autopilot merge leg via `SetJiraDoneNotifier` — is the shape to copy.

**Goal**:
Linear issues follow the task lifecycle natively: start → `started`-type state, PR
opened → completion comment with the PR/MR URL (+ optional review state), PR merged
(autopilot-observed PRs) → `completed`-type state, failure → failure comment
(+ optional failed state). Zero config needed for the defaults; names/UUIDs override.
Every transition logs at INFO so a silent miss is detectable from the daemon log.

---

## Known Pitfalls & Patterns

- **PITFALL** (merged-feature-dead-callback-not-bridged-onprcreated): PR#4992 shipped a Jira merge leg with no production effect because the SDK adapter dropped the callback. → Phase 3 acceptance requires a test that fails when the Linear leg is unwired from the live call site (both the handler closure and the autopilot merge path), not just unit tests of the mover.
- **PITFALL** (95%, config-env-expansion-eats-dollar-vars-in-commands): YAML values are env-expanded at load; a `$` in a state name would be blanked. → Docs state: state names are plain strings; no `$`. No new `${VAR}` is introduced (mem-209 upgrade-restart trap does not apply).
- **PITFALL** (90%, linear-sdk-poller-migration-dropped-project-routing): per-issue routing lives in `newLinearWorkspaceHandler`; the start/completion legs must run **inside** the per-workspace closure (each workspace has its own client/API key — GH-4717), never on a global notifier.
- **LEARNING** (95%, linear-invoices-tickets-founder-owned-hands-off): the `LIN-QF-*` queue is the founder's; this task touches the pilot repo only and never edits those issues by hand. Live verification reads them, does not write.
- **PATTERN** (GH-4987 Jira merge leg): attempt-once flag on `PRState` (`JiraDoneNotified`) + immediate `persistPRState`, WARN-only, never blocks merge. Copy as `LinearDoneNotified`.

---

## Acceptance Criteria

- [ ] `adapters.linear.transitions.{in_progress,in_review,done,failed}` parse at the legacy top level and per `workspaces[]` (workspace overrides top level). Values are a Linear workflow-state **name** or **UUID**; empty = default.
- [ ] Defaults when unset: `in_progress` → the team's first `type: started` state; `done` → first `type: completed` state (reuse `Client.GetTeamDoneStateID`); `in_review` and `failed` → **no state move** (comment only).
- [ ] On dispatch (handler closure, after `NotifyTaskStarted`): issue moves to `in_progress`. Live proof: a `LIN-*` issue in `Backlog` is in a `started`-type state within one poll of dispatch.
- [ ] On handler result `Success && PRURL != ""`: `NotifyTaskCompleted(issueID, PRURL, "")` is posted and, if `in_review` is configured, the issue moves there. GitLab MR URLs take this path too (nothing requires a GitHub URL).
- [ ] On handler result `!Success` (not Skipped): `NotifyTaskFailed(issueID, reason)` is posted and, if `failed` is configured, the issue moves there. Admission-gate declines / superseded (`Skipped`) post nothing.
- [ ] On autopilot merge of a pilot/LIN-* PR (both `handleMerging` and `checkExternalMergeOrClose` merged branch): issue moves to `done` once; `PRState.LinearDoneNotified` persisted; WARN-only on failure. Gated on branch prefix exactly like `jiraIssueKeyFromBranch`.
- [ ] Every attempted transition logs INFO `component=linear msg="Linear state transition" issue=<identifier> to=<state> leg=start|pr|merge|failed`; failures log WARN with the error. Absence of the INFO line after a dispatch is a visible defect.
- [ ] A transition failure never aborts dispatch, never changes `IssueResult`, never blocks a merge.
- [ ] `TransitionState` is called with the Linear issue **UUID** (`ev.IssueID`) on the start/PR/failed legs; the merge leg resolves the identifier parsed from the branch (`QF-295`) to the UUID via `Client.GetIssue` before transitioning (Linear's `issue(id:)` accepts identifiers — confirm in a test against the GraphQL shape, do not assume).
- [ ] Docs: `docs/content/integrations/linear.mdx` "Status Notifications" table rewritten to what the poll path actually posts (started, completed-with-PR, failed) plus a "Workflow state transitions" section with the four keys and the type-based defaults; `configs/pilot.example.yaml` Linear block gains the commented `transitions:` keys. No `$` in example values.
- [ ] Jira: no code change. Add a test pinning that `jiraSDK.NewNotifier` with empty transitions still performs the category fallback (regression guard for the box config shape), or document in the PR body that the fallback was verified in SDK v0.38.3 source with file:line.

---

## Implementation

### Phase 1: Config + state resolver
**Goal**: typed config, resolver that turns a key into a state UUID with type-based defaults, cached per team.

**Tasks**:
- [ ] `internal/adapters/linear/types.go`: add `Transitions LinearTransitions` (`yaml:"transitions,omitempty"`) to both `Config` and `WorkspaceConfig`; `GetWorkspaces()` folds top-level into the synthesized legacy workspace; per-workspace non-empty fields override.
- [ ] a new file linear_state.go under cmd/pilot: `linearStateMover{client *linearSDK.Client, sync *linearSDK.SyncAdapter, teamKey string, cfg LinearTransitions, log}` with `Move(ctx, issueUUID, leg)`; resolves: UUID → pass through; name → `sync.TransitionState`; empty → type default (`started` via a `workflowStates(filter:{team:{key},type:{eq:"started"}})` query through `client.Execute`, ordered by `position`; `completed` via `GetTeamDoneStateID`); `in_review`/`failed` empty → return `errNoTransition` (caller logs DEBUG, skips).
- [ ] Config validation at load: WARN when a configured name does not resolve for the team (preflight next to `preflightLinearLabels`, GH-5092 style).

**Files**:
- `internal/adapters/linear/types.go` — config shape
- new file linear_state.go under cmd/pilot — mover + resolver
- new file linear_state_test.go under cmd/pilot — table tests: UUID passthrough, name resolve, type default, empty optional legs, resolver cache, failure → error not panic

### Phase 2: Wire start, PR and failed legs in the workspace handler
**Goal**: the per-workspace closure in `poller_linear.go` runs the legs around `handleLinearIssueWithResult`.

**Tasks**:
- [ ] In `poller_linear.go:437-466` closure: after `NotifyTaskStarted` → `mover.Move(ctx, ev.IssueID, legStart)` (WARN on error).
- [ ] After `handleLinearIssueWithResult` returns `res`: if `res != nil && !res.Skipped`: `Success && PRURL != ""` → `notifier.NotifyTaskCompleted(ctx, ev.IssueID, res.PRURL, "")` + `Move(legPR)`; `!Success` → `notifier.NotifyTaskFailed(ctx, ev.IssueID, reason(res.Error))` + `Move(legFailed)`. Never alter `res`/`err`.
- [ ] Reason string: `res.Error.Error()` truncated to 300 chars, no token-shaped substrings (reuse an existing redaction helper from the pilot command package if one exists; otherwise the truncation only).
- [ ] INFO/WARN log lines per acceptance.

**Files**:
- `cmd/pilot/poller_linear.go` — closure wiring
- `cmd/pilot/poller_linear_test.go` — add `TestLinearHandlerRunsStateLegs`: fake client recording `issueUpdate`/`commentCreate` mutations; assert start leg before dispatch, PR leg with the MR URL, failed leg on `Success=false`, nothing on `Skipped`. **Mutation pin**: deleting the `Move` calls must fail this test.

### Phase 3: Autopilot merge leg
**Goal**: `done` on merge for autopilot-observed pilot/LIN-* PRs, mirroring GH-4987.

**Tasks**:
- [ ] `internal/autopilot/controller.go`: `LinearDoneNotifier` interface `{ NotifyMerged(ctx, issueIdentifier, prURL string) error }`; `SetLinearDoneNotifier`; `linearIssueIdentifierFromBranch("pilot/LIN-QF-295") == "QF-295"`; `notifyLinearDone(ctx, prState)` called from the same two sites as `notifyJiraDone` (`handleMerging`, `checkExternalMergeOrClose` merged branch); `PRState.LinearDoneNotified` + `internal/autopilot/state_store.go` column/migration + persist.
- [ ] `cmd/pilot/poller_linear.go`: construct one `linearDoneNotifier{mover, client}` per workspace; register on every controller `newLinearOnPRCreated` can route to (per-repo controllers, GH-5584) — the notifier must look up the issue's workspace by team key when more than one workspace is configured.
- [ ] Note in code + docs: PRs not observed by autopilot (today: all GitLab MRs) do not get the merge leg; the PR leg's `in_review` is the terminal state Pilot can reach for them.

**Files**:
- `internal/autopilot/controller.go`, `internal/autopilot/state_store.go`, `internal/autopilot/state_store_test.go`
- `cmd/pilot/poller_linear.go`, the new linear_state.go under cmd/pilot
- new file controller_linear_done_test.go under internal/autopilot — merged once → one call; second merge tick → no call; non-LIN branch → no call; notifier error → merge still completes

### Phase 4: Docs + example config + live verification
**Tasks**:
- [ ] `docs/content/integrations/linear.mdx`: replace the "Status Notifications" table; add "Workflow state transitions" (keys, defaults by state type, name vs UUID, no-merge-leg caveat for GitLab MRs).
- [ ] `configs/pilot.example.yaml` Linear block: commented `transitions:` keys with one-line explanations.
- [ ] PR body: live verification plan for the operator (next `LIN-*` dispatch on the box: expect the INFO transition lines and the issue in a `started` state; after the MR opens: completion comment present).

---

## Out of Scope

- GitLab / Azure DevOps / Asana native state write-back (their `UpdateIssueState` / `UpdateWorkItemState` are also uncalled) — file separately after this lands; same mover pattern.
- Observing GitLab MR merges in autopilot (no GitLab merge signal exists today) — separate task; this is why `done` cannot fire for the Linear Invoices projects yet.
- Legacy webhook path `internal/pilot/pilot.go:1088-1141` (comment-only, not run on the box) — leave as is.
- Progress-phase comments (🔍/🔨/🧪) the docs table promised — delete from docs, do not implement.
- Chat-filed tasks (Slack/Telegram) — no tracker issue, nothing to move.
- Any SDK change. `SyncAdapter.TransitionState`, `GetTeamDoneStateID`, `Client.Execute` and the notifier already cover the need; no studio-sdk bump (avoids a two-leg release).

---

## Technical Decisions

| Decision | Options Considered | Chosen | Reasoning |
|----------|-------------------|--------|-----------|
| Where the transition logic lives | (a) extend SDK `linear.Notifier` like Jira's; (b) pilot-side mover over `SyncAdapter` | (b) pilot-side | No SDK release leg; SDK already exposes everything needed; Jira's notifier-owns-transition shape is kept at the call sites |
| Default behaviour with no config | (a) no-op until configured; (b) type-based defaults (`started`, `completed`) | (b) | Mirrors Jira's category fallback; the box gets correct behaviour on the next train with zero config; Linear state **types** are stable across teams, names are not |
| State at PR-open | (a) `done`; (b) `in_review` optional, `done` only on merge; (c) `done_on_pr` per-project flag | (b) | A PR is not done; `done` on an unmerged MR is the false-success class (TASK-460). GitLab projects stop at `in_review` until autopilot observes GitLab merges |
| Merge-leg gating | branch prefix pilot/LIN- (as Jira) vs. persisted source adapter on PRState | branch prefix | Same contract as `jiraIssueKeyFromBranch`; PRState has no source adapter field; the branch is already the carrier |
| Issue id for the merge leg | identifier from branch vs. persist UUID on PRState | identifier → `GetIssue` → UUID | No schema widening beyond the attempt-once flag; one extra read per merge |
| Failure comment | add now vs. defer | add now | Today a failed `LIN-*` task is invisible in Linear except for a `pilot-failed` label; `NotifyTaskFailed` already exists |

---

## Verify

```bash
go build ./... && go vet ./cmd/pilot/ ./internal/autopilot/ ./internal/adapters/linear/
go test -short -race ./cmd/pilot/ ./internal/autopilot/ ./internal/adapters/linear/
# mutation pins (each must FAIL the named test when applied, then be reverted):
#   1. delete the Move(legStart) call in poller_linear.go      → TestLinearHandlerRunsStateLegs
#   2. delete the notifyLinearDone call in handleMerging        → TestNotifyLinearDone_*
#   3. make resolver return "" for type=started default         → TestLinearStateMover_DefaultStarted
grep -rn 'Linear state transition' cmd/pilot/   # INFO line exists in the new mover file
```

Live (operator, after the train): next `LIN-*` dispatch on the box →
`grep 'Linear state transition' ~/.pilot/logs/daemon.log` shows `leg=start` then `leg=pr`;
the issue is in a `started` state and has a completion comment with the MR URL.

---

## Done

- [x] `adapters.linear.transitions` parses (top level + per workspace) with tests
- [x] Start / PR / failed legs run in the per-workspace closure; mutation pins 1 and 3 fail when applied
- [x] Merge leg fires once per merged pilot/LIN-* PR; pin 2 fails when applied; `LinearDoneNotified` persisted
- [x] INFO transition lines + WARN failures in the daemon log
- [x] Docs + example config updated; no `$` in values
- [x] Live: one `LIN-*` task on the box reaches a `started` state and gets the completion comment (QF-301/302, 2026-10-15)

---

## Refs

- Pilot issue: https://github.com/qf-studio/pilot/issues/5701
- #5705 → PR#5706 merged 13:35Z, post-merge review 10-15: **APPROVE-w-defects** (outcome threading correct, e2e table test through the real dispatcher, pins 2/2 kill; defects: `needs_human` comment claims pushed even on push failure and drops the reason · `superseded` restore clobbers a human close · `failed: execution failed:` double prefix · stale generic no-PR text · docs paragraph contradiction; notes: colon-in-path partial redaction, `Status` vs `Outcome` altitude, dead `TerminalByDesign`). Fast-follow https://github.com/qf-studio/pilot/issues/5708 dispatched (`pilot`). **All three PRs are in v2.287.0 (14:04Z).**
- #5703 → PR#5704 (12:07Z) review 10-15: **CHANGES REQUESTED** (posted as a comment; GitHub refuses request-changes on a same-account PR) — the leg still branches on `Success`/`PRURL`: `no_op` posts a failure with 'unknown error', `needs_human` posts 'nothing waiting for review' and leaves the started state, `BackendError` classification unreachable on the dispatcher path (error rebuilt from a DB string). Pins 3/3 kill, gated flip + error masking fixed. Follow-up https://github.com/qf-studio/pilot/issues/5705 (thread the classified outcome into the leg) — PR#5704 merged 12:22Z; #5705 labeled `pilot` 12:3xZ.
- PR#5702 review 10-15: **APPROVE-w-defects** posted on the PR (4 behaviour defects: start leg before admission gates · success-without-PR dead end · NotifyMerged masks the matched workspace error · raw error in the failure comment; 6 notes). Fast-follow filed: https://github.com/qf-studio/pilot/issues/5703 — label `pilot` after #5702 merges.
- PR: https://github.com/qf-studio/pilot/pull/5702 (opened by Navigator from the auto-preserved commit 8fe4dd2 after a detached-worktree verify; the executor run ended its turn while a background `go test` was still active — pitfall `executor-session-ends-turn-awaiting-background-test-no-commit`)
- nav-research report 2026-10-15 (this session): connector write-back table; Linear = labels + start comment only; GitLab/Azure/Asana same class; Plane and GitHub move native state; Jira via category fallback.
- Jira pattern: GH-4718 (start leg, `cmd/pilot/poller_jira.go:51-82`), GH-4987 + GH-4999 (merge leg, `internal/autopilot/controller.go:5454-5507`).
- Linear start comment: GH-4717 (`cmd/pilot/poller_linear.go:454-462`). Per-repo controller routing: GH-5584.
- Audit that found the start-comment gap: `.agent/system/notify-started-adapter-audit.md`.
- Pitfall: `.agent/knowledge/memories/pitfalls/merged-feature-dead-callback-not-bridged-onprcreated.md`.
- Docs to fix: `docs/content/integrations/linear.mdx` lines 199-210 and 263; `configs/pilot.example.yaml` lines 181-198.

---

## Notes

- The claude.ai Linear MCP in Navigator sessions is bound to a different workspace; QF issues are read through the box's key via SSM (`pilot-aws` skill), never through the MCP.
- 2026-10-15 session: a masked config read on the box still printed `adapters.slack.bot_token` / `app_token` into the session transcript (mask regex matched `token:` only after a space-less key). Rotation is on the operator list; future config reads must mask `[a-z_]*token|key|secret`.
- Existing `pilot-in-progress` / `pilot-done` labels stay (SDK-managed, orphan-recovery invariant); the native state is additive.

---

**Last Updated**: 2026-10-15 (PR open 11:27Z, awaiting approval 11:34Z)
