# SOP: Upgrade a hosted tenant's Pilot binary over SSM

**Status 2026-10-20: LEGACY PATH.** Since **v2.282.0** (pilot GH-5651 / PR#5654, 2026-10-13) the daemon self-upgrades headless and the console renders `upgrade.auto_hot_upgrade: true` for every tenant; the founder tenant hot-upgraded itself 2.288.1 → 2.289.0 on 2026-10-19 14:06Z. Use this SOP only for a tenant whose daemon is **older than v2.282.0** (one manual hop puts it on the train for good) or when self-upgrade is proven stuck (`journalctl -u pilot | grep -i upgrade` shows no "update available" for a day after a train).

**When (legacy)**: a tenant runs a daemon below v2.282.0, or self-upgrade is stuck, and it must run the current train. Root cause of the pre-v2.282.0 drift: the version checker and hot upgrader only started inside the dashboard branch of `cmd/pilot/main.go`, so headless tenants never checked.

**Precedent**: 2.245→2.247 (07-28), →2.249 (07-29), 2.259.3→2.271.1 (08-29), 2.276.1→2.281.0 (10-13, this SOP).

## Facts about a tenant instance
- Name tag `pilot-tenant-<org-uuid>`; find it with `aws ec2 describe-instances --filters Name=instance-state-name,Values=running` (profile `quantflow`, region `eu-central-1`).
- `pilot.service` runs `/opt/pilot/bin/pilot start --config /var/lib/pilot/config.yaml` as user `pilot`. On baked-AMI tenants `/opt/pilot/bin/pilot` is a symlink to `/usr/local/bin/pilot`; replace the symlink target. On S3-bootstrapped tenants `/opt/pilot/bin/pilot` is a real file; replace it and sync `/usr/local/bin/pilot`.
- `GITHUB_TOKEN` lives in `/run/pilot/env` (tmpfs, rewritten by `fetch-secrets.sh` at every start). Source it with `set -a; . /run/pilot/env; set +a`.
- `pilot --version` does not exist; use `pilot version`.
- Do NOT use `| head -1` under `set -o pipefail`: `pilot version` prints 3 lines and the SIGPIPE aborts the script with exit 141 before the install (hit 10-13).

## Procedure
1. Read-only preflight (SSM `AWS-RunShellScript`): `pilot version`, `pgrep -af claude` must be empty (no execution in flight), `grep -c GITHUB_TOKEN /run/pilot/env` = 1, `df -h /usr/local` has >1G free, `curl -s -o /dev/null -w %{http_code} https://api.github.com` = 200.
2. Confirm the restart with the founder (daemon down ~10 s, any running execution dies).
3. Run the script below via SSM. Pass it base64-encoded: `echo <b64> | base64 -d > /tmp/tenant-upgrade.sh && bash /tmp/tenant-upgrade.sh`.
4. Verify in the output: `pilot-linux-amd64.tar.gz: OK`, `after: Pilot <new>`, `inode_exe == inode_file`, `active`, and a healthy journal tail (poller + autopilot started).
5. Rerun the smoke the upgrade was for (e.g. the console side chat).

```bash
set -eu
VER=v2.281.0            # <- target tag
PREV=2.276.1            # <- current version, for the backup name
set -a; . /run/pilot/env; set +a
cd /tmp && rm -rf up && mkdir up && cd up
H="Authorization: Bearer ${GITHUB_TOKEN}"
curl -fsSL -H "$H" -o pilot-linux-amd64.tar.gz https://github.com/qf-studio/pilot/releases/download/$VER/pilot-linux-amd64.tar.gz
curl -fsSL -H "$H" -o checksums.txt https://github.com/qf-studio/pilot/releases/download/$VER/checksums.txt
grep ' pilot-linux-amd64.tar.gz$' checksums.txt | sha256sum -c -
tar -xzf pilot-linux-amd64.tar.gz pilot
./pilot version
echo "--- before: $(/usr/local/bin/pilot version), inode $(stat -c %i /usr/local/bin/pilot)"
cp -p /usr/local/bin/pilot /usr/local/bin/pilot.prev-$PREV
install -m 0755 pilot /usr/local/bin/pilot.new && mv -f /usr/local/bin/pilot.new /usr/local/bin/pilot
systemctl restart pilot
sleep 6
systemctl is-active pilot
PID=$(systemctl show pilot -p MainPID --value)
echo "pid=$PID exe=$(readlink -f /proc/$PID/exe) inode_exe=$(stat -L -c %i /proc/$PID/exe) inode_file=$(stat -c %i /usr/local/bin/pilot)"
echo "--- after: $(/usr/local/bin/pilot version)"
journalctl -u pilot --no-pager -n 15 | cut -c1-200
```

## Rollback
`mv -f /usr/local/bin/pilot.prev-<PREV> /usr/local/bin/pilot && systemctl restart pilot`, then `pilot version`.

## Product gap (re-scoped 2026-10-20)
- Rollout itself: **closed by the daemon** (GH-5651). No console-pushed binary rollout is planned (founder decision 2026-10-13).
- Visibility: [pilot-console#390](https://github.com/qf-studio/pilot-console/issues/390) — observed Pilot version per tenant from the daemon `/health` probe, `consolectl status` VERSION column, floor warning (`PILOT_CONSOLE_FLEET_MIN_PILOT_VERSION`). Dispatched 2026-10-20.
- **Open infra gap:** the reconciler's golden AMI (`ami-06825978577ce40d4`, bakes pilot 2.277.4) predates v2.282.0 and `PILOT_CONSOLE_FLEET_BINARY_S3_URI` is unset, so a newly provisioned tenant needs exactly one run of this SOP before it tracks the train. Fix = AMI refresh to the current release, filed as [infra#23](https://github.com/qf-studio/aws-infrastructure-pilot/issues/23) (memory `verify-issue-premise-against-live-fleet-before-dispatch`). **Handed to Nelya 2026-10-20 10:05 CEST** (`#infrastructure` thread `1791555910.941859`, ts `1792489082.804169`); the box does not poll that repo, so Pilot will not pick it.
