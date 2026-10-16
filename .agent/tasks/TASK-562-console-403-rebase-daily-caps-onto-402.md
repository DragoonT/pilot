# fix(allowance): rebase the daily caps branch (PR #408) onto the merged tickets-or-USD exhaustion (PR #407) and renumber its migration

**Status**: 🚀 Dispatched to Pilot 2026-10-16 → [console#415](https://github.com/qf-studio/pilot-console/issues/415) (continuation of console#403 / PR#408; autopilot-meta footer adopts pilot/GH-403)
**Created**: 2026-10-16
**Repo**: qf-studio/pilot-console

Blocked by: none

## Context

PR #408 (issue #403, daily platform-key ticket cap + daily chat-turn cap as plan data) conflicts with main since issue #402 merged as 058ad6d (exhaust on tickets or USD, whichever first). Autopilot's mechanical rebase refused because the conflict surface is three Go files, and held the PR with `needs-manual-rebase`. A trial merge on 2026-10-16 showed the three textual conflicts are mechanical, and one more blocker sits outside the conflict markers: both branches added a migration numbered 0029. Main has `internal/db/migrations/0029_org_allowance_state_meters.up.sql` from #402; the branch adds a second 0029 pair for the daily caps, and the embedded migration loader fails with `duplicate migration file: 0029_org_allowance_state_meters.down.sql`, which takes down every DB-gated test in `internal/fleet`, `internal/orgs`, `internal/instances`, `internal/proxy` and `internal/db`. With the three resolutions below and the daily-caps migration renumbered to 0030, `go build ./...`, `go vet` and the full test set of those packages pass against Postgres.

## Scope

- Adopt branch pilot/GH-403 (PR #408), rebase it onto origin/main and resolve the three conflicts so that BOTH behaviours survive:
  - `cmd/consolectl/billing.go`: keep main's single-argument call `formatUsageBlock(st)` (from #402) and add the branch's `fmt.Print(formatDailyLine(st))` right after it.
  - `internal/allowance/status.go`: keep the branch's new `Daily DailyUsage` field with its comment, and keep main's `Exhausted` comment that names `ExhaustedBy` (tickets or dollars, whichever first). Do not reintroduce the "dollars decide" wording.
  - `internal/fleet/allowanceenforce.go`: keep both imports, `errors` from the branch and `fmt` from main.
- Renumber the branch's daily-caps migration pair from 0029 to 0030 (both the up and the down file); the content does not change. Main's 0029 pair from #402 stays as it is.
- Keep every test from both PRs green; do not drop or skip a test to make the merge compile.
- Push the rebased branch to pilot/GH-403; do not open a second PR.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go vet ./internal/fleet/ ./internal/allowance/ ./cmd/consolectl/` passes; paste the output into the PR body.
- `DATABASE_URL` is set in CI; `go test ./internal/db/ -run 'TestMigrateUpDownUp' -count=1 -v` prints `--- PASS` for TestMigrateUpDownUp; paste the `--- PASS` line into the PR body. An `ok internal/db 0.0Xs` line alone is a skip and does not meet this acceptance.
- `go test ./internal/fleet/ -run 'TestAllowance' -count=1 -v` prints `--- PASS` for the four #402 meter tests (TestAllowanceExhaustedByTicketsBeforeDollars, TestAllowanceExhaustedByDollarsBeforeTickets, TestAllowanceChatTurnsRaiseDollarsNotTickets, TestAllowanceWarnsOncePerMeter); paste the `--- PASS` lines into the PR body.
- `go test ./internal/fleet/ -run 'TestDailyTicketCap' -count=1 -v` prints `--- PASS` for all seven #403 daily-cap tests; paste the `--- PASS` lines into the PR body.
- `go test ./cmd/consolectl/ ./internal/allowance/ -run 'Daily' -count=1 -v` prints `--- PASS` for TestFormatDailyLine, TestParseBillingSetAllowanceDailyCapArgs, TestStatusDaily and TestCountDaily; paste the lines into the PR body.
- The migrations directory contains exactly one pair numbered 0029 (org_allowance_state_meters) and exactly one pair numbered 0030 (daily_caps).
- Pin: restore the daily-caps migration number to 0029 -> TestMigrateUpDownUp fails with `duplicate migration file`.
- Pin: drop the `formatDailyLine` print from the billing status command -> TestFormatDailyLine or the consolectl status test that asserts the daily line fails.

## Out of scope

- Any behaviour change beyond the merge of the two PRs.
- console#404 (org invites, PR #406, wire-contract check failing) — separate hold.

## Refs

- PR #408 (held, needs-manual-rebase), PR #407 (merged 058ad6d), issues #403 and #402; parent plan [TASK-546](TASK-546-pricing-v3-honest-allowance-overage-packs.md)
- `cmd/consolectl/billing.go`, `internal/allowance/status.go`, `internal/fleet/allowanceenforce.go`, `internal/fleet/allowanceenforce_meters_test.go`, `internal/db/migrations/0029_org_allowance_state_meters.up.sql`

<!-- autopilot-meta branch:pilot/GH-403 pr:408 iteration:1 source:403 sha:812088957bf307dc499cd8e74a32fc0e35dda210 -->
- Continuation issue: https://github.com/qf-studio/pilot-console/issues/415
