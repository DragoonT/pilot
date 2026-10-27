# TASK-608: wait_for_merge, poll_interval and pr_timeout never reach the GitHub SDK poller — SDK fields + pilot wiring

**Status**: ✅ ALL MERGED 2026-10-27 — P1 pilot#5903 → PR#5905 20:15Z (reviewer APPROVE-w-notes: the partial-execution-block worry is moot — Load unmarshals over DefaultConfig, verified wait_for_merge=true with only mode set · the sequential log line is the SDK's own and prints its effective fields). #5898 + #5897 closed. S1 MERGED (sdk#148 → PR#150 18:09Z) · **studio-sdk v0.38.4 cut by hand 19:18Z** at d2fe89a19 (carries PR#150 + PR#151; notes on the release) · sdk#147 closed · **P1 DISPATCHED 19:22Z → pilot#5903** (`pilot`+`no-decompose`; bumps go.mod to v0.38.4, wires the three fields, banner effective values, execution-modes docs).
**Spec refs**: pilot#5898 and studio-sdk#147 (scrappydog); prior art sdk#137 → pilot#5207 (commit 16ccb2281: wire + go.mod bump in one PR).
**Origin**: external bug report 2026-10-27.

## Why (verified)
- `internal/config/config.go` ExecutionConfig has WaitForMerge / PollInterval / PRTimeout (defaults true / 30s / 1h). `cmd/pilot/main.go` reads them for the banner and the epic merge waiter only.
- `cmd/pilot/poller_github.go` sets only ExecutionMode and MaxConcurrent on PollerDeps.
- SDK v0.38.3: core.PollerDeps (sdk/core/registry.go) has no wait/interval/timeout fields. The GitHub poller has WithSequentialConfig (poller.go ~153) and the three private fields with defaults true/30s/1h, but Adapter.NewPoller never calls it. GitLab adapter has the same gap.
- Result: sequential mode always waits up to 1h; `wait_for_merge: false` is ignored; the banner prints the configured timeout, the SDK log prints 1h.

## Legs — studio-sdk first, pilot second

### LEG S1 — repo: qf-studio/studio-sdk — title: feat(core): carry WaitForMerge, PRPollInterval and PRTimeout through PollerDeps; the GitHub and GitLab adapters apply them
probe: present qf-studio/studio-sdk func WithSequentialConfig\(
probe: present qf-studio/studio-sdk ExecutionMode string
probe: absent  qf-studio/studio-sdk PRPollInterval
probe: absent  qf-studio/studio-sdk opts = append\(opts, WithSequentialConfig

## Context

Refs #147 and qf-studio/pilot#5898. #137 made the host's execution mode reachable through core.PollerDeps.ExecutionMode, applied in the GitHub adapter's NewPoller. The other three sequential settings still have no way in. The GitHub poller in `sdk/integrations/github/poller.go` already has the fields waitForMerge, prPollInterval and prTimeout (defaults true, 30s, 1h) and the option WithSequentialConfig that sets all three, but `sdk/integrations/github/adapter.go` NewPoller never calls it, and PollerDeps in `sdk/core/registry.go` has no fields to carry them. So every host running sequential mode gets the constructor defaults whatever it configured: a PR waiting for a human reviewer blocks the repo queue for the fixed hour, and the host cannot shorten, lengthen or disable the wait. The GitLab poller in `sdk/integrations/gitlab/poller.go` has the same option and the same gap.

## Implementation

1. In `sdk/core/registry.go` PollerDeps, next to ExecutionMode, add three fields with doc comments: WaitForMerge as a pointer to bool (nil = adapter default, which is true; a plain false must be distinguishable from unset), PRPollInterval and PRTimeout as time.Duration (zero = adapter default). State in the comments that they apply only in sequential mode.
2. In `sdk/integrations/github/adapter.go` NewPoller, after the ExecutionMode block: resolve the triple — wait from the pointer or true, interval from the field or 30s, timeout from the field or 1h — and append one WithSequentialConfig(wait, interval, timeout) call. Never pass a zero duration through, because WithSequentialConfig overwrites all three poller fields.
3. Same resolution and call in `sdk/integrations/gitlab/adapter.go` for its poller.
4. In the GitHub poller's "Running in sequential mode" log line, add pr_poll_interval next to wait_for_merge and pr_timeout, so a host log shows all three effective values.
5. Re-bless `sdk/core/api.golden` for the new exported fields.
6. Tests, table-driven, in the github and gitlab adapter packages: deps with nothing set keep true/30s/1h; deps with WaitForMerge pointing at false and 10m/15s produce a poller whose fields read false/15s/10m; a zero PRTimeout with a set WaitForMerge keeps the 1h default.
7. Cut a patch release after merge (next tag after v0.38.3) so the host can bump.

## Acceptance

- PollerDeps exports WaitForMerge, PRPollInterval and PRTimeout, documented as sequential-mode settings.
- A GitHub poller built from deps with WaitForMerge false, PRPollInterval 15s and PRTimeout 10m has waitForMerge false, prPollInterval 15s and prTimeout 10m.
- A GitHub poller built from deps with none of the three set has waitForMerge true, prPollInterval 30s and prTimeout 1h.
- The GitLab adapter applies the same three fields.
- The sequential-mode log line carries wait_for_merge, pr_poll_interval and pr_timeout.
- `go test -race ./sdk/integrations/github/ -run TestNewPollerSequentialSettings` passes; paste the output into the PR body.
- `go test -race ./sdk/integrations/gitlab/ -run TestNewPollerSequentialSettings` passes; paste the output into the PR body.
- drop the WithSequentialConfig append in the GitHub adapter -> TestNewPollerSequentialSettings_AppliedToPoller fails
- pass the zero PRTimeout straight through instead of the 1h default -> TestNewPollerSequentialSettings_ZeroKeepsDefault fails

## Out of scope

- The overlap-guard hold on open PRs (#5897 side, separate SDK issue).
- Host-side wiring (qf-studio/pilot#5898 pilot leg, after this ships).

## Refs

- #147
- https://github.com/qf-studio/pilot/issues/5898

## Legs — pilot (held until the SDK tag exists)

### LEG P1 — repo: qf-studio/pilot — title: fix(github): wire wait_for_merge, poll_interval and pr_timeout into the SDK poller; banner prints the effective values; execution-modes docs match the poller
probe: present qf-studio/pilot pollerDeps.ExecutionMode = deps.Cfg.Orchestrator.Execution.Mode
probe: absent  qf-studio/pilot pollerDeps\.PRTimeout\s*=

## Context

Closes #5898 and #5897 on the pilot side. The daemon reads orchestrator.execution.wait_for_merge, poll_interval and pr_timeout in `cmd/pilot/main.go` (banner at the sequential-mode line, epic merge waiter), but `cmd/pilot/poller_github.go` passes only ExecutionMode and MaxConcurrent into the SDK PollerDeps, so the GitHub poller runs sequential mode on its own defaults (wait true, 30s, 1h). studio-sdk v0.38.4 (tag d2fe89a19) carries the three fields on PollerDeps (sdk#148, PR#150) and holds an overlapping issue while the older issue's PR is open, bounded by PRTimeout (sdk#149, PR#151). This leg bumps the SDK to v0.38.4 and wires the settings.

## Implementation

1. Bump github.com/qf-studio/studio-sdk in `go.mod` from v0.38.3 to v0.38.4; run go mod tidy and commit go.sum.
2. Factor one helper in `cmd/pilot/main.go` (or a small file next to it) that resolves the triple from the config with today's guards (durations only when greater than zero; wait as configured). Use it at the banner, at the epic merge waiter, and in `cmd/pilot/poller_github.go` where PollerDeps is built: set WaitForMerge (pointer), PRPollInterval and PRTimeout.
3. Banner: in sequential mode print the effective wait, interval and timeout from the same helper; when wait_for_merge is false print "sequential mode · not waiting for PR merge" instead of hiding the line.
4. Update the comment block above the PollerDeps execution fields in poller_github.go (it still says only mode is passed since #5207).
5. Docs `docs/content/features/execution-modes.mdx`: Auto Mode states that scope comes from file paths in the issue body (not title or labels), and that an overlapping issue waits while the older issue's PR is open, bounded by pr_timeout; Sequential Mode lists all three settings as honoured by the poller.
6. Test, table-driven in cmd/pilot: PollerDeps built from a config with the three set carries them; from a config with none set carries nil / 0 / 0 so the SDK defaults apply.

## Acceptance

- With mode sequential and pr_timeout 10m the daemon log line "Running in sequential mode" shows pr_timeout=10m0s.
- With wait_for_merge false the daemon dispatches the next issue right after the PR opens, and the banner says it is not waiting.
- `go test -race ./cmd/pilot/ -run TestGitHubPollerDepsSequentialSettings` passes; paste the output into the PR body.
- stop setting PRTimeout on the deps -> TestGitHubPollerDepsSequentialSettings_ConfiguredValuesCarried fails

## Out of scope

- Epic merge waiter semantics (it ignores wait_for_merge by design, GH-4234).
- Projects-list repos for the epic waiter.

## Refs

- #5898
- #5897
- https://github.com/qf-studio/studio-sdk/issues/147

## Refs

- S1 → https://github.com/qf-studio/studio-sdk/issues/148
- P1 → https://github.com/qf-studio/pilot/issues/5903
