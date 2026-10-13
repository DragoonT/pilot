# chore(bootstrap): make the pilot binary writable by the pilot user and render upgrade.auto_hot_upgrade: true

**Status**: ✅ REVIEWED 2026-10-13 — [#399](https://github.com/qf-studio/pilot-console/issues/399) → PR#400 (142e2058c, +67/-24, autopilot-merged 12:45Z), review **APPROVE** (2/2 pins kill; full fleet suite ok; rendered scripts pass bash -n and shellcheck). Deployed in console prod-0.1.29 (13:05Z). Tenant i-0289111000cebcee9: binary converted to a pilot-owned real file 12:33Z, swapped to v2.282.0 by SSM 12:36Z. **Operator step done 15:5xZ**: flag flipped directly on the tenant config over SSM (backup kept next to the file) and the daemon restarted; it booted clean on v2.282.0 with auto_hot_upgrade true (invariant relaxed by PR#5654). The next console config push converges to the same render. **Proof pending**: the headless checker logs only when a newer release exists → verify on the next tag (v2.283.0 after TASK-539/540 merge) that the tenant self-upgrades with no SSM swap.
**Created**: 2026-10-13
**Repo**: qf-studio/pilot-console

Blocked by: none for the code. Operator order: every tenant daemon must run Pilot v2.282.0 or newer BEFORE the config push that carries this change restarts it (a daemon older than v2.282.0 fails boot on AssertHostedInvariants when auto_hot_upgrade is true under PILOT_HOSTED=1). The only tenant today was swapped to v2.282.0 by hand on 2026-10-13.

## Context

Tenant daemons never self-upgrade today for two console-side reasons: `internal/fleet/configrender.go` renders upgrade.auto_hot_upgrade: false into every tenant config, and the baked-AMI branch of `internal/fleet/bootstrap.sh.tmpl` leaves the ExecStart path as a symlink to the root-owned baked binary, so the daemon's writability preflight (checkBinaryWritable in the pilot repo) fails for user pilot. Pilot v2.282.0 runs the upgrade pipeline headless, verifies release checksums and no longer rejects auto_hot_upgrade under PILOT_HOSTED=1 (pilot#5651, pilot#5652). A failed upgrade attempt re-tries and alerts every 5 minutes, so the binary must be writable before the flag flips.

## Scope

- `internal/fleet/bootstrap.sh.tmpl`, baked-AMI branch: replace the symlink statement with a copy. Install the baked binary as a real file owned by pilot at the ExecStart path (install -o pilot -g pilot -m 0755 /usr/local/bin/pilot /opt/pilot/bin/pilot) and chown the directory to pilot. Keep the -x guard on the source and the "do not overwrite an existing real executable on re-run" rule from the PR#147 review (copy only when the path is absent or is a symlink).
- `internal/fleet/bootstrap.sh.tmpl`, S3 bridge branch: add -o pilot -g pilot to the existing install so the file and its directory are owned by pilot.
- `internal/fleet/configrender.go`: render upgrade.auto_hot_upgrade: true. Flip the expectation in `internal/fleet/configrender_test.go` (both the map assertion and the golden YAML).
- Bootstrap unit test: add TestRenderBootstrapBakedBinaryInstalledAsPilotOwnedFile next to the existing RenderBootstrap tests in `internal/fleet/bootstrap_test.go` so the rendered script contains the install line with the pilot owner in both branches and no ln -sf to the baked binary.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go vet ./internal/fleet/` passes; paste the output into the PR body.
- `go test ./internal/fleet/ -run TestRenderTenantConfig -count=1` passes; paste the output into the PR body.
- `go test ./internal/fleet/ -run TestRenderBootstrap -count=1` passes; paste the output into the PR body.
- render auto_hot_upgrade false again -> TestRenderTenantConfig fails
- restore the ln -sf symlink statement in the baked-AMI branch -> TestRenderBootstrapBakedBinaryInstalledAsPilotOwnedFile fails

## Out of scope

- Console-driven version rollout (pilot-console#390).
- Any change to the daemon's upgrade pipeline (pilot repo).
- Migrating existing tenants automatically; the one-off SSM pass is an operator step (done for the founder tenant on 2026-10-13).

## Refs

- `internal/fleet/bootstrap.sh.tmpl` (S3 bridge and baked-AMI install branches, the pilot.service unit)
- `internal/fleet/configrender.go`, `internal/fleet/configrender_test.go`, `internal/fleet/bootstrap_test.go` (RenderBootstrap tests)
- Daemon side: pilot PR#5654 (headless self-upgrade, invariant relaxed), pilot PR#5655 (checksum verification), both in v2.282.0
- Pilot issue: https://github.com/qf-studio/pilot-console/issues/399
