---
name: executor-box-has-no-postgres-db-test-evidence-invalid
description: CORRECTED 2026-10-22 — the founder box HAS a shared Postgres (pilot-console-pg, the daemon runs with DATABASE_URL and the quality gate uses it); only the executor's in-session shell lacks DATABASE_URL, so DB-backed evidence pasted into PR bodies is still a failing run (dial unix /tmp/.s.PGSQL.5432). The gate's real hazard is the SHARED per-package test databases (pilot_test_<pkg>) that sibling worktrees on different bases drive to different schema versions.
type: pitfall
---

# Executor box: shared Postgres, env-scrubbed session — two different hazards

**Correction (2026-10-22, nav-research on the day's failures):** the earlier wording "the executor box has no Postgres" was wrong and was repeated in four reviews. Facts:

- The daemon process has `DATABASE_URL`; a shared Postgres (`pilot-console-pg`, :5432) is up on the box; the console quality gate (`make test`, required) runs against it and passes (GH-424 gate 11:20Z, GH-422 gate 12:02Z).
- The Claude Code session the executor spawns does NOT have `DATABASE_URL` (env scrub). So the "Evidence" block the session pastes into the PR body (`go test ./...` → `dial unix /tmp/.s.PGSQL.5432`) is still a failing run under a passes-style heading. That part of the old rule stands.
- The gate hazard: `internal/testdb/testdb.go` names databases `pilot_test_<pkg>` and reuses them. GH-424's gate applied migration 0033 to them; GH-423's worktree (older base) then failed three gates with `no migration found for version 33`, auto-preserved and stalled. Fix: per-run prefix (`PILOT_CONSOLE_TESTDB_PREFIX`, console#428) + box gate command.

## Rules
- Do not accept a DB-test acceptance criterion as met from the PR body; CI reruns (fresh `postgres:16-alpine`) or a reviewer's fresh-server run are the evidence.
- When a console gate fails on `no migration found for version N`, check which sibling task last migrated the shared test DBs before blaming the PR.
- Do not write "the box has no Postgres" anywhere again; say "the executor session has no DATABASE_URL".

Related: evidence-runner-pastes-nonzero-exit-under-passes-bullet, mem-267.
