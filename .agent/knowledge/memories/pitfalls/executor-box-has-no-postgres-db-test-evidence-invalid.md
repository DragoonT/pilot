---
name: executor-box-has-no-postgres-db-test-evidence-invalid
description: The Pilot executor environment on the founder box has no Postgres: DB-backed test evidence pasted into PR bodies is a failing run (dial unix /tmp/.s.PGSQL.5432) under a passes-style heading, and revisions do not rewrite the PR body. For DB-test PRs, evidence = CI reruns (each gets a fresh Postgres service) or a reviewer's local fresh-server run.
type: pitfall
---

# Executor has no Postgres — DB-test evidence in Pilot PRs is not evidence

**Seen 2026-10-20 (pilot-console PR#419, GH-418/420/421):** the PR body's "Evidence" for `go test -count=3 ./...` showed `--- FAIL ... dial unix /tmp/.s.PGSQL.5432: connect: no such file or directory` for every DB package. The heading itself said FAILS. Two revisions later the body still carried the first pass's block — revisions do not regenerate it.

## Rules
- Do not accept a DB-test acceptance criterion as met from the PR body.
- Evidence path: `gh run rerun <run> --job <test-job-id>` 2–3 times on the same head (fresh `postgres:16-alpine` service each time), or a local fresh container on a random port (`-p 127.0.0.1::5432`; a fixed port can hit another container).
- Write DB-test issue bodies so the executor states "not run locally (no Postgres)" instead of pasting a failing run.

Related: evidence-runner-pastes-nonzero-exit-under-passes-bullet.
