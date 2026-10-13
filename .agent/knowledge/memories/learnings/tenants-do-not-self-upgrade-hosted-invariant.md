---
name: tenants-do-not-self-upgrade-hosted-invariant
description: Hosted tenants never pick up a release train: the self-upgrade pipeline runs only in TUI dashboard mode, AssertHostedInvariants forbids auto_hot_upgrade under PILOT_HOSTED=1 (S0.7 'control plane redeploys'), the console renders auto_hot_upgrade: false, the tenant binary dir is root-owned, and the console reconciler's RunAMIRollout has no caller. Until TASK-532/533/537 ship, upgrade tenants by the SSM swap SOP.
type: learning
---

# Tenants do not self-upgrade; the founder box does

**Found 2026-10-13:** the founder tenant `i-0289111000cebcee9` ran Pilot 2.276.1 (bootstrapped 09-25) while the train had tagged v2.281.0. The console side chat therefore hit the legacy question/intake path ("Issue intake requires the bot module to be enabled") although every TASK-518 leg was released. A manual SSM binary swap fixed it (`.agent/sops/operations/tenant-binary-upgrade-ssm.md`).

**Five independent reasons, all verified:**
1. `cmd/pilot/main.go` starts the version checker and hot upgrader only inside `if dashboardMode && program != nil`. The founder box runs the TUI in tmux, so it self-upgrades; tenants run under systemd without `--dashboard`.
2. `internal/config/config.go` `AssertHostedInvariants` fails boot when `PILOT_HOSTED=1` and `upgrade.auto_hot_upgrade: true` (S0.7 decision: "hosted instances are redeployed by the control plane").
3. `pilot-console/internal/fleet/configrender.go` renders `auto_hot_upgrade: false` into every tenant config.
4. The tenant's `/opt/pilot/bin/pilot` is a symlink to root-owned `/usr/local/bin/pilot`; the daemon's `checkBinaryWritable` preflight would fail for user `pilot`.
5. The control plane does not redeploy: `RunAMIRollout` in the console reconciler has no production caller, and no desired-version column exists (pilot-console#390).

**Decision (founder, 10-13):** daemon self-upgrade is the tenant path. TASK-532 (headless wiring + relax the invariant), TASK-533 (sha256 verification against checksums.txt — the upgrader has none today), TASK-537 (console bootstrap chown + render true). CI never deploys: the tag workflows only publish assets, GHCR and docs.

**Resolved 2026-10-13 evening:** PR#5654 (headless pipeline, invariant relaxed), PR#5655 (sha256), console PR#400 (pilot-owned binary, render true) shipped; v2.283.0 was picked up by the tenant 27 s after publication with no operator step. From now on tenants track the train.

**How to apply (historical):** after a train, do not assume tenants moved. Check `pilot version` on the tenant (SSM; `pilot --version` does not exist) before any tenant smoke of a new feature.
