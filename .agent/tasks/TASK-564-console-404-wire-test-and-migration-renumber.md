# fix(orgs): unblock the org invites PR (#406) — raw-body wire-contract test for the members payload, migration renumbered past main, merge main

**Status**: 🚀 Dispatched to Pilot 2026-10-16 → [console#416](https://github.com/qf-studio/pilot-console/issues/416) (continuation of console#404 / PR#406; autopilot-meta footer adopts pilot/GH-404; merge not rebase so the push fast-forwards on the old runner)
**Created**: 2026-10-16
**Repo**: qf-studio/pilot-console

Blocked by: none

## Context

PR #406 (issue #404, invite / accept / remove org members, +1312/−15) has been held since 2026-10-14 11:10Z: `lint` and `test` pass, but `Check Wire-Contract Tests` fails, and autopilot could not read the job log, so it parked the PR for manual review. Reproduced locally on the branch with `make check-wire-contract-tests`: `internal/orgs/handlers.go` gained six json-tagged fields on the members entry of the org response (`user_subject`, `email`, `role`, `status`, `invite_id`, `expires_at`) and no test in the package asserts on the raw response body with `strings.Contains` (the rule in `scripts/check-wire-contract-tests.sh`, incident ui PR#113). The invite tests on the branch decode into structs and read `rec.Body.String()` only in failure messages. A second blocker sits outside the check: the branch's migration pair is numbered 0028, and main has carried `internal/db/migrations/0028_ticket_ledger.up.sql` since 10-14 (plus 0029 and 0030 since), so the embedded loader fails with `duplicate migration file` once main is merged. A trial on 2026-10-16 showed origin/main merges into the branch with no textual conflict; with the migration renumbered to 0031, `go build ./...`, `go vet` and `go test ./internal/orgs/ ./internal/db/ ./internal/config/` pass against Postgres, and only the wire-contract check still fails.

## Scope

- Adopt branch pilot/GH-404 (PR #406). Start from its current head (`git checkout -B pilot/GH-404 origin/pilot/GH-404`), then **merge** origin/main into it — do not rebase. The old head 690ab5ae1 must stay an ancestor of what is pushed, so the push fast-forwards.
- Renumber the branch's org-invites migration pair from 0028 to 0031 (up and down; content unchanged). Main's 0028 (ticket ledger), 0029 and 0030 stay as they are.
- Add a raw-body wire-contract test in `internal/orgs/handlers_test.go` (same package as the DTO), in the shape of `TestHandleListAppliedSpecVersionJSON` in `internal/instances/handlers_test.go`: create an org, invite one email as the owner, call `GET /api/v1/org`, and assert with `strings.Contains` on `rec.Body.String()` that the members array carries the owner entry with `"role":"owner"` and `"status":"active"`, and the pending invite entry with `"status":"invited"`, `"role":"member"`, the `"email"`, a non-empty `"invite_id"` and an `"expires_at"`. Name it TestHandleGetOrgMembersWireJSON.
- `make check-wire-contract-tests` passes on the merged branch. Do not loosen or edit the script.
- Keep every invite test green; do not drop or skip one.
- Push to pilot/GH-404; do not open a second PR.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go vet ./internal/orgs/` passes; paste the output into the PR body.
- `make check-wire-contract-tests` exits 0 and its output has no `CI CHECK FAILED` line; paste the output into the PR body.
- `DATABASE_URL` is set in CI; `go test ./internal/db/ -run 'TestMigrateUpDownUp' -count=1 -v` prints `--- PASS`; paste the line into the PR body. An `ok internal/db 0.0Xs` line alone is a skip and does not meet this acceptance.
- `go test ./internal/orgs/ -run 'TestInvite' -count=1 -v` prints `--- PASS` for TestInviteStore_e2e, TestInviteAcceptFlow_createsMemberRow, TestInviteCreate_memberGets403, TestInviteAccept_expiredIs410RevokedIs404, TestInviteAccept_differentVerifiedEmailIs403, TestInviteAccept_callerAlreadyInAnOrgIs409, TestInviteCreate_conflictsAndValidation, TestInviteCreate_sendFailureRevokesInvite and TestInviteCreate_disabledWithoutMailer; paste the lines into the PR body.
- `go test ./internal/orgs/ -run 'TestHandleGetOrgMembersWireJSON' -count=1 -v` prints `--- PASS`; paste the line into the PR body.
- The migrations directory contains exactly one pair numbered 0028 (ticket_ledger) and exactly one pair numbered 0031 (org_invites).
- Pin: remove the `strings.Contains` assertions from TestHandleGetOrgMembersWireJSON -> `make check-wire-contract-tests` fails on `internal/orgs/handlers.go`.
- Pin: restore the org-invites migration number to 0028 -> TestMigrateUpDownUp fails with `duplicate migration file`.

## Out of scope

- Any behaviour change to the invite endpoints beyond the merge.
- The console-ui Members page (ui#231, already merged against this contract).

## Refs

- PR #406 (held: wire-contract check failing), issue #404; parent plan [TASK-546](TASK-546-pricing-v3-honest-allowance-overage-packs.md)
- `internal/orgs/handlers.go`, `internal/orgs/handlers_test.go`, `scripts/check-wire-contract-tests.sh`, `internal/instances/handlers_test.go`, `internal/db/migrations/0028_ticket_ledger.up.sql`

<!-- autopilot-meta branch:pilot/GH-404 pr:406 iteration:1 source:404 sha:690ab5ae13700ffaf248147a26ee2f048b473a14 -->
- Continuation issue: https://github.com/qf-studio/pilot-console/issues/416
