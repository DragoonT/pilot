# TASK-599: an agent-opened PR bypasses the gates (reconciler adopts it, autopilot merges on CI alone) and the stale-running reaper then prunes the live execution's worktree

**Status**: 🟡 #5877 → PR#5880 merged 2026-10-27 08:59Z, post-merge review posted **APPROVE-WITH-NOTES** (argv surface closed, audit path pre-existing, 2 mutation pins hold; defect: CLAUDE.md L46 told executor sessions to open a PR → fixed on main; notes: shim bypass via `$PILOT_GH_REAL`/absolute path/`curl`+kept token, dead `--head` parser code, merge reason text). #5878 → PR#5881 merged 2026-10-27 09:26Z, post-merge review posted **APPROVE-WITH-NOTES** (veto ahead of every delete/prune/claim reap, registry spans the whole run; M2 fails as required, M1/M3/M4 survive → wiring unpinned, skip line Debug-invisible, `CompletedExecutionID` outside the invariant → TASK-602 / #5883). **Both legs merged and reviewed — task done; keep for the open follow-ups #5882/#5883 then archive.**
**Spec refs**: `internal/executor/ghguard/policy.go` (`pr create` allowed as an own artifact on the current branch), `internal/executor/prompt_builder.go` (scope rule lets the agent act on "its own PR"), `internal/executor/dispatcher.go` `recoverStaleRunningTasks` (GH-3732; `HasCompletedExecution` shortcut before `hasLiveWorker`), `StaleRunningThreshold` 30m, `internal/autopilot` reconciler ("adopting untracked open PR"), GH-5273 claim reaper, TASK-597 (#5867, same day: finalization budget).
**Origin**: founder 2026-10-26 20:40Z "check again, 5862 failed". The ticket shipped (PR#5874 merged 19:59Z) but the run ended `failed` and bypassed every executor gate.

## Timeline (box daemon.log, 2026-10-26)

| time | event |
|---|---|
| 19:34:04 | GH-5862 run 2 starts (worktree, 1h budget) |
| 19:46:41 | **the Claude session runs `gh pr create --base main --head pilot/GH-5862`** (recording TG-1793043244584); PR#5874 exists, body is the agent's own |
| 19:46:51 | executor "Task completed"; quality gates start (19m35s) |
| 19:47:33 | autopilot reconciler: "adopting untracked open PR" pr=5874 → `waiting_ci` on stage |
| 19:59:43 | CI green → autopilot merges PR#5874, closes #5862 `pilot-done`, deletes the branch; the task's claim row becomes `completed` |
| 20:05:36 | dispatcher `recoverStaleRunningTasks`: the 19:33 running row is older than `StaleRunningThreshold` (30m); `HasCompletedExecution` is true → "Deleting orphan running row (task already completed)" → "Pruned orphaned task worktree"; GH-5273 reaps the claim |
| 20:06:27 | gates finish `all_passed=true` in a directory that no longer exists; intent judge, self-review (`fork/exec /usr/bin/claude: no such file or directory` — the cwd is gone), contract evidence and the commit-count guard all fail → "Task ended without success … failed to verify commit count" |

Three untracked PRs were adopted today the same way: auth-service PR#544 (GH-533), PR#571 (GH-527, later `failed pending`), pilot PR#5874.

## Legs — pilot (daemon)

### LEG G1 — repo: qf-studio/pilot — title: fix(executor): the gh guard must deny gh pr create and gh pr merge from the agent session — Pilot opens the PR after the gates, and an agent-opened PR is adopted and merged on CI alone

## Context
On 2026-10-26 the GH-5862 session ran gh pr create on its own branch at 19:46:41, ten seconds before the executor logged Task completed. The autopilot reconciler adopted the untracked PR at 19:47:33 and merged it at 19:59:43 on green CI. The quality gates (which finished at 20:06:27), the intent judge, self-review, the contract-evidence gate and the acceptance-evidence block never gated that merge. Two auth-service PRs (544 for GH-533, 571 for GH-527) were adopted the same way today. The recording for the run is on the box under the recordings directory, id TG-1793043244584.

The guard in `internal/executor/ghguard/policy.go` classifies pr create as an own artifact and allows it when the head is the current branch ("pr create on current branch"). The scope rule in `internal/executor/prompt_builder.go` tells the agent it may act on its own issue or its own PR and forbids mutations only against other issues and PRs. Nothing tells the agent that Pilot opens the PR after the gates. The runner's own PR step (the Pull request created log line) runs only after gates, judge, self-review and evidence.

probe: present qf-studio/pilot pr create on current branch
probe: present qf-studio/pilot \{"pr", "create", kindOwnArtifact\}
probe: absent  qf-studio/pilot pr create is Pilot's step

## Scope
- In the guard policy, deny gh pr create, gh pr merge, gh pr close, gh pr ready and gh pr edit --base from the agent session regardless of branch, with the reason "pr create is Pilot's step: the executor opens the PR after the quality gates". Keep gh pr comment, gh pr view, gh pr checks and gh issue comment on the own artifact as today.
- Add one line to the scope rule in the prompt builder: Pilot opens the pull request after the gates; never run gh pr create or gh pr merge; commit and push to the task branch only.
- Audit log line through the existing ghguard audit path when a denial fires, with task id and the denied argv.
- When the runner's own PR step finds a PR already open for the branch (an older binary or a bypass), keep the existing behaviour.

## Acceptance
- [ ] Policy test: gh pr create --head pilot/GH-1 on branch pilot/GH-1 is denied with a reason that contains "Pilot's step"; gh pr merge 12 is denied; gh pr comment 12 and gh pr view 12 on the own PR stay allowed. Allow pr create on the current branch again -> TestPolicy_PRCreateDeniedForAgent fails.
- [ ] Prompt test: the built prompt contains "never run gh pr create". Remove the line -> TestBuildPrompt_PRCreationIsPilotsStep fails.
- [ ] `go test -race ./internal/executor/ghguard/` passes; paste the output into the PR body.
- [ ] `go test -race ./internal/executor/ -run TestBuildPrompt` passes; paste the output into the PR body.

## Out of scope
- Making the autopilot reconciler defer adoption of an untracked PR while its task is still running (worth a follow-up if denials keep showing in the audit log).
- GitLab and Azure DevOps equivalents.

### LEG G2 — repo: qf-studio/pilot — title: fix(executor): the stale-running reaper must never delete a row or prune a worktree that this process is still executing — check the runner's live registry before the completed-task shortcut

## Context
On 2026-10-26 20:05:36 the dispatcher's stale-running pass deleted the running row of GH-5862 and pruned its worktree while the quality gates were still running in that worktree (they completed at 20:06:27 with all_passed true). The run then failed every later step on the missing directory and ended "Task ended without success … failed to verify commit count", a false failure on a ticket that had already shipped (PR#5874). The chain: an agent-opened PR had merged at 19:59 and marked the task's claim row completed; the execution row from 19:33 was older than StaleRunningThreshold (30 minutes, the default in `internal/executor/dispatcher.go`); recoverStaleRunningTasks checks HasCompletedExecution and deletes the row before it checks hasLiveWorker, and never asks the runner whether the execution is live in this process. With complex runs spending 20 to 36 minutes in the gates alone, every long run is a crash candidate under the 30-minute rule, and only the ordering of those checks protects it. The runner already has a live registry: IsRunning in `internal/executor/runner.go` reports whether a task id is executing in this process.

probe: present qf-studio/pilot Deleting orphan running row \(task already completed\)
probe: present qf-studio/pilot func \(r \*Runner\) IsRunning\(
probe: present qf-studio/pilot func \(d \*Dispatcher\) hasLiveWorker\(
probe: absent  qf-studio/pilot live in this process, not stale

## Scope
- In recoverStaleRunningTasks, before the decomposed-parent guard and the HasCompletedExecution shortcut: when the runner reports the task as running in this process, skip the row with one Debug line "stale-running reap skipped: execution is live in this process, not stale" and continue. Give the dispatcher the runner handle it needs (it already dispatches through it); a nil runner keeps today's behaviour.
- Apply the same guard to the orphan worktree prune and to the GH-5273 claim reaper for the same execution id, so a live execution's worktree and claim are never removed from under it.
- The HasCompletedExecution shortcut must compare against rows other than the one being reaped and only when the runner does not hold the task; log which completed row satisfied it (execution id) so the next incident is readable.
- Leave StaleRunningThreshold at 30 minutes; the fix is the liveness check, not the timer.

## Acceptance
- [ ] Dispatcher test: a running row older than the threshold whose task the fake runner reports as live is neither deleted nor marked failed, and its worktree path is not pruned, even when a completed row for the same task exists. Remove the live-registry check -> TestRecoverStaleRunning_SkipsLiveExecution fails.
- [ ] Dispatcher test: the same row with the runner reporting not live and a completed sibling row is deleted as today; with no completed row and no live worker it is marked failed as today.
- [ ] Claim-reaper test: a claim whose execution id is live in this process is not reaped. Remove the guard -> TestReapOrphanedClaims_SkipsLiveExecution fails.
- [ ] `go test -race ./internal/executor/ -run TestRecoverStaleRunning` passes; paste the output into the PR body.
- [ ] `go test -race ./internal/executor/ -run TestReapOrphanedClaims` passes; paste the output into the PR body.

## Out of scope
- Changing how autopilot marks the claim row completed on merge.
- A heartbeat column for running rows (a larger change; the liveness registry is enough for a single-process daemon).

## Refs
- G1 → - G1 → https://github.com/qf-studio/pilot/issues/5877
- G2 → https://github.com/qf-studio/pilot/issues/5878
- G2 → (filled by the dispatch script)
- Incident: PR#5874 (merged 19:59:43Z by autopilot, agent-opened at 19:46:41Z); recording TG-1793043244584; daemon.log lines 144063–144456.
- Same-day sibling: TASK-597 → #5867 → PR#5875 (finalization budget).

**Last Updated**: 2026-10-26
