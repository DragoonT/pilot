# TASK-595: an issue un-labeled or closed while it waits for an execution slot still runs — the handler re-fetches the issue but ignores its live labels and state

**Status**: ✅ Merged 2026-10-26 — #5849 → PR#5871. **Post-merge review not posted** (10-27 docs pass). Was: 🚀 Dispatched 2026-10-26 (nav-research LIKELY-BUG).
**Spec refs**: GH-4050 / GH-4631 (post-wait re-fetch of the issue), GH-5056 (pilot-needs-human admission backstop), GH-5072 (the SDK bridge drops `Skipped`, so a skip must arm `repickBackoff`), TASK-421 (repick cap).
**Origin**: external report by @scrappydog (2026-10-23, v2.289.0, studio-sdk v0.38.3 — the pin on main is still v0.38.3).

## Context

studio-sdk `checkForNewIssues` (poller.go v0.38.3 lines 1108–1143) refreshes each candidate with `GetIssue`, checks only `pilot-done` / `pilot-in-progress`, runs pre-flight, calls `markProcessed`, and **then** blocks on the semaphore — for a whole task's runtime under `max_concurrent: 1`. Pilot's `handleGithubIssueEventSDK` (`cmd/pilot/handlers.go`) runs after the slot is acquired and re-fetches the issue via `fetchGithubIssueForSDKTask`, but reads only `State`, `User` and `Body` from it; the `pilot-needs-human` backstop and the task's `Labels` both use `ev.Labels`, the snapshot from before the wait. A closed issue only skips the `pilot-in-progress` label write; nothing returns early. Corrections to the report: (1) the stale window is the semaphore wait plus pre-flight, not the whole poll interval — `ev` is built from the refreshed issue; (2) a plain `Skipped: true` result is **not** a clean skip — the SDK adapter bridge copies only Success/PR fields, so the poller sees a failure with no PR and unmarks for retry (the GH-5072 loop); every skip must arm `repickBackoff` the way the needs-human backstop does. No change on main since v2.294.0 touches this handler.

## Legs — pilot (daemon)

### LEG B3 — repo: qf-studio/pilot — title: fix(github): after the slot wait, re-check the live issue — closed, trigger label removed or an admission-blocking label added — and skip with a repick backoff instead of running the stale snapshot

## Context
Reported by @scrappydog on v2.289.0 (original report in this issue's edit history). max_concurrent 1, mode auto. A poll picked issue A behind issue B; the maintainer removed the pilot label from A while A waited for the slot; nine minutes later the log showed "Dispatching issue for parallel execution number=A", the executor's "Epic detection check" still printed labels with pilot from the stale event, and A ran and opened a PR.

Verified cause (main at v2.295.0, studio-sdk v0.38.3). SDK side: checkForNewIssues in the sdk's poller (sdk/integrations/github/poller.go, lines 1108 to 1143) refreshes the issue, checks only the done and in-progress labels, runs pre-flight, marks it processed, and only then blocks on the semaphore, which can take a whole task runtime. Pilot side: handleGithubIssueEventSDK in `cmd/pilot/handlers.go` runs after the slot is acquired and calls fetchGithubIssueForSDKTask, but uses only realIssue.State, realIssue.User and realIssue.Body; the pilot-needs-human backstop and the task's Labels read ev.Labels, the pre-wait snapshot. A closed issue only skips the pilot-in-progress label write; nothing stops it from running. Two details in the report are corrected: the stale window is the slot wait plus pre-flight, not the whole poll interval; and a bare Skipped result is not a clean skip, because the SDK adapter bridge copies only the Success and PR fields, so the poller unmarks the issue for retry (the GH-5072 loop documented next to the needs-human backstop). Every skip on this path must arm repickBackoff the same way.

probe: present qf-studio/pilot specBody = realIssue\.Body
probe: present qf-studio/pilot githubEventHasNeedsHumanLabel\(ev\.Labels\)
probe: present qf-studio/pilot repickBackoff\.recordClaimLostDrop
probe: absent  qf-studio/pilot realIssue\.Labels

## Scope
- Pilot side only; no studio-sdk change. In handleGithubIssueEventSDK, when fetchGithubIssueForSDKTask succeeds, derive liveLabels from realIssue.Labels and use them for the needs-human backstop and for the task's Labels. On fetch failure keep the current ev.Labels behaviour (fail open, as today).
- Add one admission check, run before any side effect (spec guard, label write, comment, task construction): skip when the live issue is closed, when it lacks the configured trigger label (cfg.Adapters.GitHub.PilotLabel), or when it carries pilot-needs-human, pilot-blocked or pilot-needs-clarification. Log one INFO line with the task id and the reason.
- Each skip returns Success false, Skipped true with a distinct SkipReason, and arms repickBackoff with recordClaimLostDrop on the same backoff key the needs-human path uses, so the unmark-and-retry loop is damped exactly like GH-5072.
- The poller lists candidates by trigger label and open state, so a closed or un-labeled issue leaves the candidate set on the next poll; re-adding the label re-admits it after the backoff window.

## Acceptance
- [ ] Table-driven test next to the existing GH-5072 backoff test in cmd/pilot: cases are live issue closed, trigger label removed, pilot-blocked added, pilot-needs-clarification added, fetch error. The first four return Skipped true with their SkipReason, write no label and no comment, and arm the backoff; the fetch-error case proceeds with ev.Labels.
- [ ] Existing needs-human test keeps passing with the backstop now reading live labels.
- [ ] remove the trigger-label check from the new admission guard -> TestHandleGithubIssueEventSDK_LiveLabelsGate fails
- [ ] remove the recordClaimLostDrop call from the new skip path -> TestHandleGithubIssueEventSDK_LiveLabelsGate fails
- [ ] `go test -race ./cmd/pilot/ -run TestHandleGithubIssueEventSDK` passes; paste the output into the PR body.
- [ ] Do not re-run make build, make test or make lint as evidence: the daemon's quality gates already run them on this repo (21–36 min on the box), and a second run overruns the 1-hour task budget before the PR is created.

## Out of scope
- Moving the SDK's label refresh after the semaphore acquire, or making the SDK bridge propagate Skipped (studio-sdk changes; file separately if wanted).
- Stopping a task that already started when the label is removed mid-run.
- The other adapters (GitLab, Linear, Jira) — the GitHub poller path only.

## Refs
- B3 → https://github.com/qf-studio/pilot/issues/5849
- Pilot issue: https://github.com/qf-studio/pilot/issues/5849 (reporter @scrappydog; original text in the edit history)
- studio-sdk pin on main: v0.38.3 (go.mod)
- Prior: GH-4050, GH-4631 (post-wait re-fetch), GH-5056 (needs-human backstop), GH-5072 (Skipped dropped by the bridge)

**Last Updated**: 2026-10-26
