# TASK-596: operator pause / resume of task admission, and an automatic admission pause on a Claude usage-limit failure

**Status**: 📋 PLANNED, NOT DISPATCHED 2026-10-26 — feature request pilot#5862 (@scrappydog). Premises verified by nav-research: one is refuted, one is infeasible. Needs a founder decision on scope before it is labeled `pilot` (see § Decision).
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

## Decision needed

- Dispatch P1 + P2 as `pilot` issues (one `no-decompose` issue each, P2 blocked by nothing)? Or P2 only (smallest useful piece, pure daemon, no CLI surface)? Or park.
- Reply to the reporter on #5862 with the premise table (premise 3 points them at #5803) — needs a yes to post.

## Refs
- Reporter issue: https://github.com/qf-studio/pilot/issues/5862
- Related: TASK-593 (#5803) · self-upgrade drain #4683 · platform breaker #4780 / #4792 (admission pause owner idiom)

**Last Updated**: 2026-10-26
