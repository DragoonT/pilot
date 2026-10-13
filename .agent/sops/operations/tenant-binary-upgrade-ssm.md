# SOP: Upgrade a hosted tenant's Pilot binary over SSM

**When**: a release train tags a new daemon version and a tenant must run it. The founder box self-upgrades; tenants do NOT. The console reconciler only replaces instances on an AMI change (`RunAMIRollout`, no production caller) and holds no desired Pilot version. Until that gap closes, this is the only path.

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

## Product gap
Tracked as [pilot-console#390](https://github.com/qf-studio/pilot-console/issues/390): a per-tenant desired Pilot version plus a reconciler binary rollout (canary-first, like `RunAMIRollout`), so the train reaches tenants without an operator.
