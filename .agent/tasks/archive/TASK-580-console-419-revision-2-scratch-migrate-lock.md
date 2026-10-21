# fix(test): PR #419 revision 2 — run every scratch-database migration under the base-DB advisory lock, mixed regression test, honest evidence

**Status**: ✅ MERGED 2026-10-20 17:37Z via PR #419 (a0cde12af). Review APPROVE on e48cf440: all four scratch sites under MigrateLocked; CI `test` green 3/3 on fresh Postgres (4m28s / 4m39s / 4m07s), no `tuple concurrently updated`. console#421 closed completed 10-21. Archived. Prior: 🚀 Dispatched to Pilot 2026-10-20 as [console#421](https://github.com/qf-studio/pilot-console/issues/421) → qf-studio/pilot-console, labels pilot + no-decompose, continues branch pilot/GH-418 (PR #419, held as draft).
**Task ID**: TASK-580 · **Parent**: GH-418 (console), revision 1 = GH-420 (TASK-578) · **Owner**: Navigator plans, Pilot executes

## Context

Revision 2 of PR #419 (GH-418, per-package Postgres database for DB-backed tests). Continue on the PR's existing branch pilot/GH-418; do not open a new PR. The Navigator review of head a47d0a75 is posted on the PR as a comment.

Revision 1 (GH-420) added the testdb package under internal/ on the branch. Its `MigratedDSN` runs the first migration of each package database while it holds `pg_advisory_lock(502002)` on the base database. The `MustDSN` helper wraps it, and every package opener uses it. That part is correct. Keep it.

## Problem

A local run of `go test -count=3 ./...` against a fresh `postgres:16-alpine` server failed on the second round:

```
postgres_e2e_test.go:53: testdb.MustDSN("secrets"): testdb: migrate pilot_test_secrets: db: apply migrations: migration failed: tuple concurrently updated (column 0) in line 1: ...
postgres_e2e_test.go:76: testdb.MustDSN("secrets"): testdb: migrate pilot_test_secrets: db: apply migrations: Dirty database version 14. Fix and force version.
```

Migration `internal/db/migrations/0014_row_level_security.up.sql` runs `ALTER ROLE <current_user> WITH BYPASSRLS` on every apply. That statement updates one cluster-wide `pg_authid` row. The base-DB lock serializes only the `MigratedDSN` callers. The scratch-database tests still apply the migrations with no lock, in parallel with the locked callers, so two applies of 0014 can overlap and one fails. The failed apply leaves the database dirty at version 14, and every later test in that package fails too.

The unlocked migration sites on the branch are:

1. `internal/db/migrate_test.go`: `TestMigrateUpDownUp` runs Up, Down and Up on a scratch database.
2. `internal/db/rls_test.go`: `setupRLSScratchDB` runs `Migrate` on a scratch database (used by four RLS tests).
3. `internal/db/rls_test.go`: `TestRLS_DownMigrationRemovesPoliciesCleanly` runs `Migrate`, then `runMigrateDownTo(scratchDSN, 13)`.
4. `internal/orgs/store_e2e_test.go`: `newTestStore` creates a scratch database per test and runs `db.Migrate` on it (about 30 tests).

`createScratchDatabase` in `internal/fleet/lock_test.go` does not migrate, so it is not a site.

## Task

**1. Export the locked migrate step.** In the testdb package, export a function such as `MigrateLocked(ctx context.Context, baseDSN, dsn string, migrate MigrateFunc) error`. It takes the same base-DB lock (key 502002) as `MigratedDSN`, runs `migrate(ctx, dsn)`, and releases the lock. Make `MigratedDSN` call it, so there is one lock path. Keep the key, the per-name cache, and the no-cache-on-failure behaviour.

**2. Use it at all four sites above.**
- The base DSN is always the raw `DATABASE_URL` value, the same base that `MustDSN` uses. Do not pass a package or scratch DSN as the base, because the lock must be on the one database every test binary shares.
- For the up/down sequences (sites 1 and 3), hold the lock around the whole sequence. Pass one closure as the `MigrateFunc` that does Up, Down and Up (site 1), or Migrate then `runMigrateDownTo` (site 3). The down migration of 0014 also touches roles.
- Site 2: wrap the `Migrate` call in `setupRLSScratchDB`.
- Site 4: wrap the `db.Migrate` call in `newTestStore`. Keep the per-test scratch database.

**3. Mixed regression test.** In the testdb package tests, add a test that starts at least 8 goroutines on one server. Half of them call `MigratedDSN` with fresh unique names. The other half each create a fresh scratch database and call `MigrateLocked` on it. All of them use the real `db.Migrate` from `internal/db`, so migration 0014 runs. Assert that every call succeeds and that no database ends up dirty. Repeat the round 3 times inside the test with new names each round. Drop every database the test created in `t.Cleanup` with `DROP DATABASE ... WITH (FORCE)`.

**4. Honest evidence in the PR body.** Replace the current "Evidence" section.
- The executor environment has no Postgres: the pasted run failed with `dial unix /tmp/.s.PGSQL.5432: connect: no such file or directory`. Do not paste a failed or skipped run as evidence.
- If a real Postgres is available, paste the summary of `go test -count=3 ./...` against it.
- If no Postgres is available, write one line that says the local run was not possible and why. Then name the CI `test` job run for the new head as the evidence, with its duration.
- Navigator reruns `-count=3` against a fresh server during review.

## Tests

- The new mixed regression test passes.
- Existing suites in `internal/db`, `internal/orgs` and the testdb package stay green.
- `TestRLS_*` and `TestMigrateUpDownUp` keep their assertions unchanged. Only the migrate calls get wrapped.

## Acceptance

- [ ] No test applies migrations to a real database outside the base-DB lock. `git grep -n 'Migrate(\|m.Up()\|m.Down()\|runMigrateDownTo(' -- '*_test.go'` shows only calls inside a `MigrateLocked` closure, or calls on a database already fully migrated by `MustDSN` (those are no-ops).
- [ ] `MigratedDSN` and the scratch sites share one exported lock function and one key (502002).
- [ ] The mixed regression test runs 3 rounds of at least 8 concurrent migrations and passes.
- [ ] The PR body's evidence section contains only runs that actually ran.
- [ ] CI `test` job green on the new head. Report its duration; the main baseline is 3m20s to 3m57s.
- [ ] No production code changes. Migration 0014 is unchanged.

## Verify

- `docker compose up -d postgres` then `DATABASE_URL=postgres://postgres:postgres@localhost:5432/postgres?sslmode=disable go test -count=3 ./...`
- `go vet ./...`

## Known Pitfalls & Patterns

- **PITFALL** (memory console-ci-shared-postgres-truncate-races-instances-e2e): the original cross-package flake. This revision closes the last migration race that the per-package fix made likely.
- **PITFALL** (memory evidence-runner-pastes-nonzero-exit-under-passes-bullet): revision 1 pasted a failing run as evidence. Item 4 forbids that.
- **PITFALL** (memory issue-body-backticked-paths-not-on-main-trip-base-presence-hold): the testdb package exists only on the PR branch, so this body names it in prose. Every backticked path exists on console main.

## Out of Scope

- Production code and migration files.
- `go test -p 1` and any change to `make test` or the CI workflow.
- Test logic changes beyond wrapping migrate calls and the new regression test.

## Refs

- Pilot issue: https://github.com/qf-studio/pilot-console/issues/421
- PR #419 (pilot/GH-418). Navigator review of a47d0a75, 2026-10-20: REQUEST CHANGES, local `-count=3` repro of `tuple concurrently updated`.
- GH-420 (revision 1, TASK-578). Parent issue #418.

**Last Updated**: 2026-10-20

<!-- autopilot-meta branch:pilot/GH-418 pr:419 iteration:2 -->
