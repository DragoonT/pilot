---
name: console-ci-shared-postgres-truncate-races-instances-e2e
description: pilot-console CI runs go test ./... against one Postgres service; fleet tests TRUNCATE instances while the instances E2E test runs in parallel, so TestProvisionDeprovisionRowTransitions_E2E can fail "fleet: not found" on an unrelated change — rerun first; a nearby "db down" ERROR is a fake-store path from another test, not the cause
type: pitfall
---

# Console CI: shared Postgres + parallel packages = E2E row vanishes

**What happened (2026-10-20, PR#417 head `94e2bea`):** a two-file change (json
tags + a unit test) turned the `test` job red: `--- FAIL:
TestProvisionDeprovisionRowTransitions_E2E … provision_e2e_test.go:117:
GetInstance after provision: fleet: not found`. The previous head passed the
same test. Re-run of the failed job: green. 0 failures in the last 30 `main`
runs — rare.

**Why:** `make test` = `go test ./...` (packages in parallel) and the CI job
has one `postgres:16-alpine` service with one `DATABASE_URL`.
`internal/fleet/reconciler_test.go` runs `TRUNCATE instances, instance_events
CASCADE`; `internal/instances/provision_e2e_test.go` inserts a row and reads
it back a moment later on the same DB. Timing decides.

**Decoy:** `ERROR instances: check requirements failed error="db down"` right
above the FAIL is a fake-store error-path unit test in the same package, not
the E2E failure.

## Rules
- Red `test` on console with that exact FAIL line and a diff that cannot
  touch it → `gh run rerun <id> --failed` before anything else.
- Autopilot's CI-fix size guard (200 production lines) refuses a fix issue on
  a PR this size and re-parks it `pilot-needs-human`; a green rerun on the
  same head does not revive it (redrive needs a new head) → manual merge.
- Durable fix (not filed): per-package schema/search_path, or `-p 1` for the
  DB-backed packages, in the console repo.
