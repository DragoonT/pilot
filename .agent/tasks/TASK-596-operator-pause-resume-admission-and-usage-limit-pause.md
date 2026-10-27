# TASK-596: operator pause / resume of task admission, and an automatic admission pause on a Claude usage-limit failure

**Status**: ✅ P2 MERGED (PR#5874 `076bb48f4`, 19:59Z — agent-opened PR, merged by autopilot on CI alone, incident → TASK-599) + **post-merge review POSTED 2026-10-27: APPROVE-WITH-NOTES** (https://github.com/qf-studio/pilot/pull/5874#issuecomment-6437389321). Non-blocking: parser rolls a just-passed reset +24h → 6h daemon-wide hold (pre-existing, amplified) · double alert (rate_limit + usage_limit_pause) · Stop() leaves the owner set · three tests call armUsageLimitPause directly · wording check not done. P1 still held. Was: 🚀 P2 DISPATCHED 2026-10-26 (founder: "real issue") → body applied to the reporter's issue pilot#5862, labeled `pilot`+`no-decompose`+`enhancement`. **P1 (CLI pause/resume) HELD** as a `### LEG` below; file with `nav-dispatch-legs.py --only P1` when wanted. Premises verified by nav-research: one refuted, one infeasible (table below).
**Spec refs**: `internal/executor/dispatcher.go` admission pause (`PauseAdmissionFor` / `ResumeAdmissionFor` / `IsAdmissionPaused`, owner-keyed, used today by the self-upgrade drain and the platform breaker); `internal/executor/ratelimit.go` (`ParseRateLimitError`); `internal/executor/scheduler.go` (re-queue at reset time); `internal/executor/runner.go` (`rateLimitedSignatures`, outcome `rate_limited`, `IsInfraNoise`); `internal/gateway/server.go` (`/api/v1/status`); `cmd/pilot/commands.go` (`pilot status`, `pilot stop`).
**Origin**: external feature request 2026-10-26. The reporter runs Pilot on a Claude Max subscription shared with interactive Claude Code work and wants admission to stop near the end of a 5-hour usage window without `pilot stop`.

## Premise check (nav-research, main at v2.295.0)

| # | Reporter premise | Verdict | Evidence |
|---|---|---|---|
| 1 | No pause / resume exists | PARTIAL | No CLI or API. An owner-keyed in-memory admission pause exists in the dispatcher (owners: `self-upgrade`, platform breaker). Running tasks finish; pollers and `QueueTask` keep running. |
| 2 | Only `pilot stop` stops admission | REFUTED in spirit | True for the operator; the daemon already pauses admission internally in two situations and exposes neither. |
| 3 | "In 2.289.0 a restart drops autopilot's in-memory PR tracking, approved PRs no longer merge" | REFUTED | `Controller.RestoreState` rehydrates PR state from SQLite at startup and existed at v2.289.0. What the reporter saw is most likely #5803 (TASK-593: polled approvals dropped since v2.290.0), not a restart loss. |
| 4 | `pilot stop` can interrupt a task mid-run | VERIFIED | Shutdown calls `runner.CancelAll()` then `dispatcher.Stop()`. A drain exists only on the self-upgrade path (`upgrade.RequestDrain`). |
| 5 | `pilot budget` is dollars only | VERIFIED | Nothing reads subscription windows. |
| 6 | A usage-limit failure counts as a failure and the next task starts | PARTIAL | Classification is already done: "usage limit" → `rate_limited`, infra noise, no retry budget consumed, the one task is re-queued at the parsed reset time. Gap: admission is not paused, so the next queued task starts and hits the same wall. |
| 7 | Usage-window threshold (pause at 80 % of the 5-hour window) | INFEASIBLE today | No API or local data source for Claude Max window usage; nothing in the repo reads it. Only the reactive form (pause on the limit error until the reported reset) is buildable. |
| 8 | Pause should survive restart | GAP | Pause state is an `atomic.Bool`; SQLite has no settings/kv table. Needs a small table or a marker file like the drain status file. |

## Proposed scope (if approved)

Two small legs, both on the existing dispatcher pause; no new chokepoint.

- **LEG P1 — operator pause**: `pilot pause [--for <duration> | --until <RFC3339>] [--reason <text>] [--project <name>]` and `pilot resume`, implemented as `PauseAdmissionFor("operator")` / `ResumeAdmissionFor("operator")` over a new local API endpoint (`POST /api/v1/admission/pause`, `/resume`); `/api/v1/status` and `pilot status` report paused, since, until, reason, owners. Persist the operator pause (owner, reason, until) in a new SQLite table so a restart re-applies it; the self-upgrade and breaker owners stay in-memory. A timer resumes at `until`. Log on pause and resume; one alert through the existing alert plumbing.
- **LEG P2 — usage-limit pause**: when an execution ends `rate_limited` with a parsed `ResetTime`, call `PauseAdmissionFor("usage-limit")` and resume at reset time plus the scheduler's `RetryBuffer`; status says "paused: usage limit, resumes at <time>". No threshold, no window tracking. Knob `executor.usage_limit_pause.enabled` (default true). Verify `ParseRateLimitError` against the current Claude Code wording ("resets in N hours" style may be missing).

Not in scope (tell the reporter): the percentage-of-window threshold (no data source); a drain on plain `pilot stop` (separate task; the marker's "drain before the train" note is the same gap on our side).


## Legs — pilot (daemon)

### LEG P2 — repo: qf-studio/pilot — title: feat(executor): pause task admission on a Claude usage-limit failure until the reported reset, instead of starting the next queued task into the same wall

## Context
Requested by @scrappydog (original request in this issue's edit history). They run Pilot on a Claude subscription with a rolling 5-hour usage window, shared with interactive Claude Code work on the same machine. When the window is exhausted, the running task fails with a usage-limit error and the next queued task starts and fails the same way. Today the only way to hold Pilot back is pilot stop, which kills running tasks and needs a manual restart.

Verified state (main at v2.295.0). The daemon already classifies the failure: rateLimitedSignatures in `internal/executor/runner.go` includes "usage limit" and "rate limit", the outcome is rate_limited, it is infra noise and does not consume the retry budget, and ParseRateLimitError in `internal/executor/ratelimit.go` extracts the reset time; the GitHub poller adapter in `cmd/pilot/poller_github.go` re-queues that one task through the Scheduler at reset time plus RetryBuffer (`internal/executor/scheduler.go`). The dispatcher already has an owner-keyed admission pause: PauseAdmissionFor, ResumeAdmissionFor and IsAdmissionPaused in `internal/executor/dispatcher.go`, used by the self-upgrade drain and the platform breaker; a paused worker starts no new task while running tasks finish, pollers keep running and QueueTask keeps accepting. The gap: nothing calls the pause on a rate_limited result, so admission continues into the same wall. There is no data source for the subscription window itself, so a percentage threshold is out of scope; this leg is the reactive form only.

probe: present qf-studio/pilot func \(d \*Dispatcher\) PauseAdmissionFor
probe: present qf-studio/pilot func ParseRateLimitError
probe: present qf-studio/pilot rateLimitedSignatures
probe: absent  qf-studio/pilot yaml:"usage_limit_pause"
probe: absent  qf-studio/pilot AdmissionPauseOwnerUsageLimit

## Scope
- New knob executor.usage_limit_pause on the executor config in `internal/config/config.go` (enabled, default true; max_pause, default 6h, the cap when the parsed reset is further away or absent; fallback_pause, default 30m, used when no reset time parses). Validated there; documented in `configs/pilot.example.yaml`.
- Hook: where the dispatcher finalizes a run whose outcome is rate_limited, parse the error with ParseRateLimitError; call PauseAdmissionFor with a new exported owner constant AdmissionPauseOwnerUsageLimit (value usage-limit) next to the existing owners; schedule ResumeAdmissionFor for the same owner at reset time plus the scheduler's RetryBuffer (or fallback_pause), capped by max_pause. A second rate_limited result while paused extends the resume time to the later reset; it never stacks owners.
- The pause is idempotent and in-memory, like the other two owners. On restart the pause is gone; that is acceptable because the next rate_limited result re-arms it.
- Status: the local API status response in `internal/gateway/server.go` gains admission_paused (bool), admission_pause_owners (list) and admission_resumes_at (time, when the usage-limit owner is set); pilot status prints one line "admission paused: usage limit, resumes at <time>" when set.
- Logging: one INFO line on pause (owner, reset time, resume time, task id that tripped it) and one on resume. One alert through the existing alert engine on pause, same severity as the platform breaker's.
- Keep the existing single-task re-queue at reset time unchanged; this leg only stops the other queued tasks from starting meanwhile.

## Acceptance
- [ ] Dispatcher test: a run that finalizes rate_limited with a parsable reset time pauses admission for the owner usage-limit, the next queued task does not start, and a fake clock at reset plus RetryBuffer resumes it; a second rate_limited result during the pause moves the resume time later and leaves one owner.
- [ ] Dispatcher test: with the knob disabled nothing pauses; with no parsable reset time the pause lasts fallback_pause; a reset beyond max_pause is capped.
- [ ] Gateway test: the status response carries admission_paused true, the owner list and admission_resumes_at while paused, and admission_paused false after resume.
- [ ] remove the PauseAdmissionFor call from the rate_limited finalization -> TestDispatcher_UsageLimitPausesAdmission fails
- [ ] remove the max_pause cap -> TestDispatcher_UsageLimitPauseCappedByMaxPause fails
- [ ] `go test -race ./internal/executor/ -run TestDispatcher_UsageLimit` passes; paste the output into the PR body.
- [ ] `go test -race ./internal/gateway/` passes; paste the output into the PR body.
- [ ] Do not re-run make build, make test or make lint as evidence: the daemon's quality gates already run them on this repo (21–36 min on the box), and a second run overruns the 1-hour task budget before the PR is created.

## Out of scope
- A manual pilot pause / pilot resume CLI and a persisted pause (separate leg P1, held).
- A percentage-of-window threshold: the daemon has no data source for subscription usage.
- A drain on plain pilot stop.
- Changing how the one rate-limited task itself is re-queued.

## Held

### LEG P1 — repo: qf-studio/pilot — title: feat(cli): pilot pause and pilot resume — operator pause of task admission with --for, --until and --reason, persisted across restart and shown in pilot status

## Context
Companion to the usage-limit pause: the dispatcher's owner-keyed admission pause (PauseAdmissionFor, ResumeAdmissionFor, IsAdmissionPaused in `internal/executor/dispatcher.go`) has no operator surface. The local API in `internal/gateway/server.go` serves /api/v1/status and friends; `cmd/pilot/commands.go` has pilot status and pilot stop. SQLite (`internal/memory/store.go`) has no settings table; the drain status file in `internal/upgrade/drain.go` is the existing idiom for small persisted operator state.

probe: present qf-studio/pilot func \(d \*Dispatcher\) ResumeAdmissionFor
probe: absent  qf-studio/pilot "/api/v1/admission/pause"

## Scope
- Routes POST /api/v1/admission/pause (body: reason, until or for, optional project) and POST /api/v1/admission/resume, owner operator; GET /api/v1/status reports paused, since, until, reason and owners.
- CLI pilot pause [--for d | --until t] [--reason s] [--project p] and pilot resume, over the local API, with the same auth as pilot status.
- Persist the operator pause (reason, until, project) in a new SQLite table; re-apply it on startup; a timer resumes at until. The self-upgrade and breaker owners stay in-memory.
- Log pause and resume; one alert on each.

## Acceptance
- [ ] API test: pause then status shows paused with the owner operator and the until time; resume clears it; a pause with for computes until from the server clock.
- [ ] Persistence test: pause, restart the dispatcher with the same store, admission is still paused until the stored time.
- [ ] remove the startup re-apply -> TestOperatorPause_SurvivesRestart fails
- [ ] `go test -race ./internal/gateway/` passes; paste the output into the PR body.
- [ ] Do not re-run make build, make test or make lint as evidence: the daemon's quality gates already run them on this repo (21–36 min on the box), and a second run overruns the 1-hour task budget before the PR is created.

## Out of scope
- Pausing a single running task; the usage-limit automatic pause (leg P2).

## Decision (founder 2026-10-26)
- P2 dispatched. P1 held. Reporter reply: pending a yes to post (draft in the session).

## Decision log (superseded)

- Dispatch P1 + P2 as `pilot` issues (one `no-decompose` issue each, P2 blocked by nothing)? Or P2 only (smallest useful piece, pure daemon, no CLI surface)? Or park.
- Reply to the reporter on #5862 with the premise table (premise 3 points them at #5803) — needs a yes to post.

## Refs
- P2 → https://github.com/qf-studio/pilot/issues/5862
- Pilot issue: https://github.com/qf-studio/pilot/issues/5862 (reporter @scrappydog; original text in the edit history)
- Related: TASK-593 (#5803) · self-upgrade drain #4683 · platform breaker #4780 / #4792 (admission pause owner idiom)

**Last Updated**: 2026-10-26
