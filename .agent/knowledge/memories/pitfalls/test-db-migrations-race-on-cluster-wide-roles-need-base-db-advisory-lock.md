---
name: test-db-migrations-race-on-cluster-wide-roles-need-base-db-advisory-lock
description: Per-package test databases (pilot-console PR#419) made migration 0014 run in ~10 databases at once; its ALTER ROLE <current_user> BYPASSRLS updates one cluster-wide pg_authid row, so concurrent applies fail with 'tuple concurrently updated' and leave the DB dirty at v14. Every test-time migration (package DBs AND scratch DBs, incl. up/down sequences) must hold one pg_advisory_lock on the BASE database — advisory lock keys are per-database.
type: pitfall
---

# Per-database test isolation still shares cluster-wide roles

**What happened (2026-10-20, pilot-console PR#419 head a47d0a75):** a fresh-server `go test -count=3 ./...` failed on round 2:
`testdb: migrate pilot_test_secrets: ... migration failed: tuple concurrently updated`, then `Dirty database version 14` for every later test in the package.

**Why:** migration 0014 runs `CREATE ROLE pilot_console_app` (catches only duplicate_object; a concurrent create raises unique_violation) and `ALTER ROLE <current_user> WITH BYPASSRLS` on every apply. Both touch cluster-wide `pg_authid` rows. Giving each package its own database removed the TRUNCATE race but made ~10 concurrent 0014 applies the normal case on a clean CI server. Revision 1 locked only the package-DB migrations; the scratch-DB tests (db up/down/up, RLS setup + down test, orgs per-test scratch DBs) still migrated unlocked and collided with the locked ones.

**Fix that shipped (PR#419 merged a0cde12af):** one exported `MigrateLocked(ctx, baseDSN, dsn, fn)` holding `pg_advisory_lock(502002)` on the base `DATABASE_URL` database; `MigratedDSN` and all scratch sites call it; up/down sequences run inside one closure under one hold. CI green 3/3 on fresh Postgres.

## Rules
- Advisory lock keys are scoped per database: to serialize across databases, take the lock on a database every caller shares (the base one).
- Any migration that touches roles/extensions is cluster-wide: serialize every test-time apply, not just the new ones.
- Verify on a FRESH server with -count>1; a reused server hides the CREATE ROLE half.
