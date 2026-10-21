# fix(test): PR #419 revision — serialize first per-package migration under a base-DB advisory lock, route remaining openers, one shared testdb helper

**Status**: ✅ MERGED 2026-10-20 17:37Z via PR #419 (a0cde12af) after revision 2 (TASK-580); console#420 closed completed 10-21. Archived. Prior: 🚀 Dispatched to Pilot 2026-10-20 as [console#420](https://github.com/qf-studio/pilot-console/issues/420) → qf-studio/pilot-console, labels pilot + no-decompose, continues branch pilot/GH-418 (PR #419, held as draft).
**Task ID**: TASK-578 · **Parent**: GH-418 (console) · **Owner**: Navigator plans, Pilot executes

## Context

Revision of PR #419 (GH-418, per-package Postgres database for DB-backed tests). The Navigator review is posted on the PR as a comment and asks for changes. The PR is a draft so autopilot cannot merge it before this revision. Continue on the PR's existing branch pilot/GH-418; do not open a new PR. There are two required items and one cleanup.

CI is green on head 849c08cb. The approach is correct: the fleet TRUNCATE of instances and the instances E2E test now run in different databases.

## Task

**1. Required: serialize the first migration of each package database.**

Each DB-backed package now migrates a fresh database at the same moment in CI, so migration `internal/db/migrations/0014_row_level_security.up.sql` runs in about 10 databases concurrently. That migration touches cluster-wide objects:

- `CREATE ROLE pilot_console_app` catches only `duplicate_object`. A concurrent CREATE ROLE with the same name can fail with `unique_violation` (SQLSTATE 23505 on pg_authid_rolname_index) instead, and that error is not caught.
- `ALTER ROLE <current_user> WITH BYPASSRLS` updates the same pg_authid row from every database. Concurrent updates can fail with "tuple concurrently updated".

Fix in the testdb package that this branch adds under internal/ (the file with the DSN function):

- Add a function that returns a package DSN with all migrations applied. It creates the package database (existing logic), then runs the project's migrate step against the package DSN while it holds `pg_advisory_lock` on an admin connection to the **base** database. Release the lock after the migrate step. Advisory lock keys are scoped per database, so the lock must be taken on the base database, not on the package database. Pick a fixed key and document it in a comment next to the 502001 key used in `internal/orgs/platform_keys_e2e_test.go`; the two must differ.
- Run the create-and-migrate step once per process per database name (for example a mutex-guarded map or `sync.Once` keyed by name). Later opens find every version applied, so 0014 does not run again in that database.
- The per-package open helpers keep calling their store's own open/migrate path as today. It becomes a no-op because the versions are already applied.
- Do not change migration 0014 or any other production code.

**2. Required: route the remaining openers through the package database.**

These openers still read `DATABASE_URL` directly and use the shared database:

- `internal/orgs/store_e2e_test.go` (`newTestStore`, used by every orgs E2E file, including `internal/orgs/platform_keys_e2e_test.go`). Use the name `orgs`.
- `internal/fleet/provisioner_e2e_test.go`, `internal/fleet/reconciler_e2e_test.go`, `internal/fleet/configpush_e2e_test.go` (two openers in the last one). Use the name `fleet`, the same database as the other fleet tests.
- `internal/db/rls_cleanup_test.go`. Use the name `db`. This file checks a cluster-wide role attribute in TestMain; keep that check's meaning unchanged.

Find any other direct opener with `git grep -n 'Getenv("DATABASE_URL")' -- '*_test.go'`. The only exceptions are tests that set `DATABASE_URL` as a config value (`internal/config/config_test.go`, the cmd/consolectl tests that point it at an unreachable host) and the scratch-database helpers that create and drop their own databases.

**3. Cleanup: one helper, not nine copies.**

The branch has nine byte-identical `packageDSN` helpers in per-package testdsn test files. Replace them with one exported helper in the testdb package, for example `MustDSN(t testing.TB, base, pkg string) string`, which calls the item-1 function and fails the test on error. Delete the nine copies and call the shared helper from every opener, including the ones from item 2.

## Tests

- In the testdb package test: start N goroutines (N at least 8) that each call the item-1 function with a different fresh database name, and assert that all succeed. Drop the created databases in `t.Cleanup`. This is the regression test for item 1.
- Keep the existing distinct-names and repeat-call test.
- Existing suites in every touched package stay green.

## Acceptance

- [ ] Every opener that connects to a real database through `DATABASE_URL` goes through the shared testdb helper, except the listed exceptions. `git grep -n 'Getenv("DATABASE_URL")' -- 'internal/*_test.go'` shows only lines that pass the value to that helper, the config tests, or the scratch-database helpers.
- [ ] The first migration of each package database runs under an advisory lock held on the base database, proven by the concurrent test above.
- [ ] No `packageDSN` copies remain.
- [ ] `go test -count=3 ./...` against the local docker-compose Postgres passes three times in a row. Paste the summary output in the PR body.
- [ ] CI `test` job green. Report its duration in the PR body; the main baseline is 3m20s to 3m57s.
- [ ] No production code changes.

## Verify

- `docker compose up -d postgres` then `DATABASE_URL=postgres://postgres:postgres@localhost:5432/postgres?sslmode=disable go test -count=3 ./...`
- `go vet ./...`

## Known Pitfalls & Patterns

- **PITFALL** (memory console-ci-shared-postgres-truncate-races-instances-e2e): the original flake. A red test job with the "fleet: not found" line is a cross-package race; rerun first. This revision must not add a new race of the same class, which is why item 1 exists.
- **PITFALL** (memory issue-body-backticked-paths-not-on-main-trip-base-presence-hold): files that exist only on the PR branch are named in prose here (the testdb package, the per-package testdsn test files). Every backticked path in this body exists on console main.
- **PATTERN**: cross-package serialization with a Postgres advisory lock already exists for platform_keys (key 502001). Item 1 reuses the pattern on the base database.

## Out of Scope

- Any production code, including migration 0014.
- `go test -p 1` (serializes the suite; fallback only).
- The scratch-database helpers that create and drop their own databases (db, fleet lock, orgs). Their concurrent 0014 runs predate this PR.

## Technical Decisions

| Decision | Options | Chosen | Reasoning |
|---|---|---|---|
| Role-setup race | change 0014 · pre-create role in the helper · lock around first migrate | lock on the base DB around the first migrate, once per name | No production change; covers both CREATE ROLE and ALTER ROLE; later opens are no-ops |
| Lock scope | package DB · base DB | base DB | Advisory lock keys are per database |
| Helper shape | per-package copies · one exported helper | one `MustDSN`-style helper in the testdb package | DRY; nine identical copies today |

## Refs

- Pilot issue: https://github.com/qf-studio/pilot-console/issues/420
- PR #419 (pilot/GH-418), Navigator review comment 2026-10-20 (REQUEST CHANGES as a comment; author account = reviewer).
- Issue #418 (parent). Verification run 2026-10-20 (nav-research): platform_keys deletes already locked by 502001; db rls tests use scratch DBs; about 83 call sites of resetFleetTables.

**Last Updated**: 2026-10-20

<!-- autopilot-meta branch:pilot/GH-418 pr:419 iteration:1 -->
