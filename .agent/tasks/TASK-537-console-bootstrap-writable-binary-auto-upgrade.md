# chore(bootstrap): make the pilot binary writable by the pilot user and render upgrade.auto_hot_upgrade: true

**Status**: 📋 Planned 2026-10-13
**Created**: 2026-10-13
**Repo**: qf-studio/pilot-console

Blocked by: pilot TASK-532 and TASK-533 released on a train (a daemon older than that fails boot with auto_hot_upgrade true under PILOT_HOSTED=1)

## Context

Tenant daemons never self-upgrade today for two reasons on the console side: `internal/fleet/configrender.go` renders upgrade.auto_hot_upgrade: false into every tenant config, and `internal/fleet/bootstrap.sh.tmpl` leaves the symlink target of the pilot binary root-owned, which makes the daemon's checkBinaryWritable preflight fail. Once the daemon runs the upgrade pipeline headless and verifies checksums (pilot TASK-532, TASK-533), flip both.

## Scope

- `internal/fleet/bootstrap.sh.tmpl`: in both the S3 and the baked-AMI branch install the binary as a real file owned by the pilot user at the service's ExecStart path (replace the symlink with a copy), so the daemon can write its backup and the new binary next to it.
- `internal/fleet/configrender.go`: render upgrade.auto_hot_upgrade: true; flip the expectation in `internal/fleet/configrender_test.go`.
- Existing tenants: a one-off SSM step (copy the binary into place and chown) per the pilot repo SOP tenant-binary-upgrade-ssm; documented in the PR body, not automated here.

## Acceptance

- To be written when TASK-532 and TASK-533 are merged and the minimum daemon version is known.

## Out of scope

- Console-driven version rollout (pilot-console#390).

## Refs

- `internal/fleet/bootstrap.sh.tmpl`, `internal/fleet/configrender.go`, `internal/fleet/configrender_test.go`
