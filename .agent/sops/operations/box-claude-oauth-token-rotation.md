# SOP: rotate the founder box's Claude Code OAuth token (and re-login locally)

**Scope:** founder box `i-0e0c1ca34e7b561f9` (eu-central-1). The Pilot daemon authenticates its `claude` subprocesses with a long-lived `CLAUDE_CODE_OAUTH_TOKEN` exported on line 6 of `/home/ec2-user/start-pilot.sh` (last rotated 2026-10-02). Hosted tenants are **not** affected: their `/run/pilot/env` carries `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, `PILOT_GATEWAY_TOKEN` only (platform pool keys, TASK-502).

**Why a plain hot upgrade does not rotate it:** the self-upgrade re-execs the binary with the same environment. A new token needs the daemon to be started again from `start-pilot.sh`.

**Rule:** the token value never enters a chat session, a commit, or a log. It moves laptop → SSM SecureString → box shell → file. Print nothing but its first 6 characters when verifying.

## Signals that it expired (from memories `mem-171`, `shared-oauth-session-strands-second-machine`)
- Executions die ~5 min in with `Backend execution failed error=unknown: exit status 1`, clean init in stdout, **empty stderr**, zero tokens; classifiers `signal: killed` at their deadline.
- `claude --print "say OK"` on the box hangs; the interactive TUI still looks fine (not evidence).
- The real `401 authentication_error` is only in `~/.pilot/recordings/*/stream.json`.

## Procedure (≈10 min, pick a quiet window: queue empty, no train in `releasing`)

1. **Laptop — mint a new long-lived token** (interactive browser flow; the operator does this, not an agent):
   ```bash
   claude setup-token
   ```
   Copy the printed `sk-ant-oat01-…` token to the clipboard. Do not paste it anywhere else.
2. **Laptop — store it in SSM** (value from the clipboard, never typed; leading space keeps it out of history):
   ```bash
    aws ssm put-parameter --profile quantflow --region eu-central-1 \
      --name /pilot/CLAUDE_CODE_OAUTH_TOKEN --type SecureString --overwrite --value "$(pbpaste)"
   ```
   Check: `aws ssm describe-parameters --profile quantflow --region eu-central-1 --parameter-filters "Key=Name,Values=/pilot/CLAUDE_CODE_OAUTH_TOKEN" --query 'Parameters[].LastModifiedDate'` shows now.
3. **Box — swap the token into `start-pilot.sh` and verify headless auth** (via SSM `AWS-RunShellScript`; the value stays inside the box shell):
   ```bash
   NEW=$(aws ssm get-parameter --region eu-central-1 --name /pilot/CLAUDE_CODE_OAUTH_TOKEN --with-decryption --query Parameter.Value --output text)
   [ -n "$NEW" ] || { echo "empty param"; exit 1; }
   cp -p /home/ec2-user/start-pilot.sh /home/ec2-user/start-pilot.sh.bak-$(date -u +%Y%m%d%H%M)
   sed -i -E "s|^export CLAUDE_CODE_OAUTH_TOKEN=.*|export CLAUDE_CODE_OAUTH_TOKEN=${NEW}|" /home/ec2-user/start-pilot.sh
   chown ec2-user:ec2-user /home/ec2-user/start-pilot.sh; chmod 700 /home/ec2-user/start-pilot.sh
   # headless probe with the NEW token — this is the path the daemon uses
   sudo -u ec2-user -i env CLAUDE_CODE_OAUTH_TOKEN="$NEW" timeout 90 claude --print "say OK" | head -c 80; echo
   echo "token prefix now in file: $(grep -oE 'OAUTH_TOKEN=.{0,12}' /home/ec2-user/start-pilot.sh)"
   ```
   The probe must print `OK` within seconds. If it hangs, the token is bad; the old file is in the `.bak-*` copy.
4. **Box — (same window) update the CLI**, it lags the tenants (box 2.1.104 vs tenant 2.1.220 on 2026-10-14):
   ```bash
   npm i -g @anthropic-ai/claude-code@latest && claude --version
   ```
5. **Box — restart the daemon from the script.** Drain first: `~/bin/pilot-board` shows no `running` row AND the daemon log has no `Processing task` / `Starting task execution` line in the last 60 s (2026-10-14: a restart 24 s after a tick that had just released three held tasks cut two of them mid-start; both re-picked themselves within 3 min, but it cost two failed rows). Count workers with `pgrep -x claude` + `pgrep -f claude-code/cli.js`; a `bash -c source …/.claude/shell-snapshots/…` process is a stale snapshot shell, not a worker:
   ```bash
   sudo -u ec2-user -i tmux send-keys -t pilot C-c; sleep 15
   sudo -u ec2-user -i tmux kill-session -t pilot || true
   sudo -u ec2-user -i tmux new-session -d -s pilot /home/ec2-user/start-pilot.sh
   ```
6. **Verify:** `~/bin/pilot-board` shows the daemon up with the current version; the process env carries the new prefix:
   `tr '\0' '\n' < /proc/$(pgrep -o -x pilot)/environ | grep -oE '^CLAUDE_CODE_OAUTH_TOKEN=.{0,12}'`. Let the next ticket run to completion.
7. **Laptop — re-login the interactive CLI** (separate credential, Keychain-backed): run `claude`, then `/login`. `claude auth status` must show `loggedIn: true`.

## Done log
- 2026-10-14 15:02–15:11Z: token minted locally → SSM v3 → start-pilot.sh swapped (backup `.bak-202610141505`), headless probe OK, CLI 2.1.104 → 2.1.299, daemon restarted 15:08:34Z (pid 2155961) with the new prefix in its env; first executions under the new token: GH-5688 15:10Z, GH-409 15:11Z.

## Do not
- Do not copy `~/.claude/.credentials.json` between machines (one OAuth session on two hosts strands one of them — memory `shared-oauth-session-strands-second-machine`).
- Do not rely on the SSM parameter as a live credential for tenants (memory `oauth-ssm-params-rot-live-credentials-source-of-truth`); here it is only the transport for the box.
- Do not restart while a train is in `releasing` or a task is `running`.
