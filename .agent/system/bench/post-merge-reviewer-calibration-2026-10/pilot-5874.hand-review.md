**VERDICT: APPROVE-WITH-NOTES** — post-merge review (this PR was opened by the agent session and merged by autopilot on CI alone; the executor's intent judge, self-review and evidence gates never ran on it — see #5877/#5878 — so the acceptance list was verified by hand).

### Verified
- Spec (#5862, LEG P2) bullet by bullet: one chokepoint in `ProjectWorker.processQueue` after `Classify`, before `Persist` (`outcome.Status == ExecStatusRateLimited` → `onRateLimited`); owner `AdmissionPauseOwnerUsageLimit` coexists with the self-upgrade and breaker owners; resume = parsed reset + `RetryBuffer`, `fallback_pause` when nothing parses, capped by `max_pause` from now; a second hit extends, never shortens, never re-adds an owner, never re-alerts; generation-guarded timer; `Stop()` cancels it. Knob off is a strict no-op. `/api/v1/status` carries `admission_paused`, `admission_pause_owners`, `admission_resumes_at`; `pilot status` prints the line. Config validated (negatives rejected, fallback > max rejected). Alert rule `usage_limit_pause` fires once per episode.
- `go test -race` on `./internal/executor/ -run 'UsageLimit|Admission'`, `./internal/gateway/`, `./cmd/pilot/`, `./internal/config/`, `./internal/alerts/`: all `ok` locally on main.
- Mutation pins (applied, run, reverted): drop `PauseAdmissionFor` in `armUsageLimitPause` → `TestDispatcher_UsageLimitPausesAdmission` FAIL; drop the `onRateLimited` hook in `processQueue` → `TestDispatcher_UsageLimit*` FAIL (the test drives the real worker loop); drop the `max_pause` cap → `TestDispatcher_UsageLimitPauseCappedByMaxPause` FAIL.
- Two independent reads, same verdict.

### Defects (non-blocking)
1. `internal/executor/ratelimit.go` (pre-existing, amplified here) — a reset time that is already a few minutes in the past when the run finalizes is rolled forward by 24 h (`if resetTime.Before(now) { resetTime = resetTime.Add(24 * time.Hour) }`), so the daemon-wide pause becomes `max_pause` (6 h) instead of ~`RetryBuffer`. The `candidate.After(now)` guard in `armUsageLimitPause` is unreachable because the parser never returns a past time. Before this PR that only delayed one task's retry; now it holds every project for 6 h. Fix: in the parser, treat a reset within the last ~2 h as "already reset" (return now, or a `Passed` flag) instead of +24 h; add a near-boundary test.
2. One usage-limit failure now emits two alerts: the pre-existing `AlertEventTypeRateLimit` from the runner and the new `usage_limit_pause` from the dispatcher. Not wrong, but noisy; consider suppressing the former when the pause arms.
3. `Stop()` cancels the timer but leaves `usageLimitResumeAt` and the owner set; a `Start()` on the same instance would stay paused and the next hit would count as "extended" (no alert). Not reachable today (only `Stop()` at shutdown).
4. Three of the dispatcher tests (disabled, fallback, cap) call `armUsageLimitPause` directly, not through a run; the gateway test uses a mock source. The hook itself is covered by the two run-driven tests.
5. The spec's "verify `ParseRateLimitError` against the current Claude Code wording ('resets in N hours' style)" was not done: formats unchanged, no new test; `fallback_pause` covers an unknown wording.

### Notes
- Epic sub-tasks finalize through `epic.go`, not `processQueue`, so a rate-limited sub-task does not arm the pause; the parent's outcome does if it propagates.
- The pause is in-memory by design (documented in the example config); a self-upgrade restart clears it and the next hit re-arms it.
- Transient status window on release: `usageLimitResumeAt` clears before `ResumeAdmissionFor`, so one status read may show the owner without `admission_resumes_at`.

