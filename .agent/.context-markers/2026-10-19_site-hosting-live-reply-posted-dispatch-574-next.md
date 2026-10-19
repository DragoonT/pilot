# Context marker — 2026-10-19 ~09:10Z: pilotcloud.dev hosting live, reply to Nelya posted; next: dispatch TASK-574, review PR#5743

**Resume with**: `/nav-start-active`. Supersedes `2026-10-17_reviews-5740-5742-posted-dispatch-574-next.md` (its state block still holds). The 10-16 candidates still stand: GH-415 worktree-base question (`runner.go`, the `task.FromPR > 0` branch), auth-service unverified-email check, test member removal.

## ONE next action
**Dispatch TASK-574 to Pilot** (`.agent/tasks/TASK-574-bootstrap-callsite-test-and-attempt-guard-key.md`, nav-pilot skill, H1 as title, `--body-file`, labels `pilot` + `no-decompose`). Run the mechanical backticked-path probe first: every backticked path in the body must exist on `origin/main`; no git refs or home paths in prose. Then **review PR#5743** (GH-5741 / TASK-573, merged 10-17 13:35Z) with the standard procedure and archive TASK-573.

## State (all verified; docs on origin/main)
- **Release:** v2.288.1 cut 10-17 14:00Z (PR#5744 docs sync). Box self-upgrade not re-verified — `~/bin/pilot-board`.
- **Reviews 10-17:** PR#5740 APPROVE-w-notes, PR#5742 APPROVE-w-defects → TASK-574 (planned, unfiled). PR#5743 unreviewed. TASK-571/572 archived.
- **pilotcloud.dev (TASK-515):** site merged on `pilotcloud-site` main (PR#4–#11; CI builds only, no deploy workflow). **I1 delivered by Nelya 10-17 23:41 CEST** in #infrastructure thread `1791555910.941859`: bucket `pilot-fleet-s3-site`, distribution `E39M9CANDXR187`, WAF, 404 mapping, runner rights. **Founder 10-19: Nelya writes the deploy workflow.** Reply POSTED 10-19 10:51 CEST (ts `1792402284.706689`): hosting confirmed, workflow asked with sync facts, docs move **option A** accepted, slot her pick, asked whether the 301 keeps the path. Waiting on her: workflow PR + slot. Ours afterwards: docs base URL (4 files under `docs/`, README, ~30 refs), `docsUrl` in the site; then Paddle resubmit + U1 console footer links.
- **Slack from Code sessions:** connector present but off per session → `session_connectors_status` + `set_session_connector_enabled` (memory `ccd-slack-connector-off-by-default-enable-per-session`). Double-post rule holds: read the thread, POSTED line first, send, stamp ts.
- **Linear MCP here = a client workspace**, not Pilot's. PI-* keys unreachable.
- **Procedure (unchanged):** review agent in a detached worktree at the merge commit; verify three anchors by reading lines; `gh pr review --comment`. Graph `nodes` = `{concepts, tasks, memories}` maps. Markers dir is gitignored → `git add -f`. Pre-push hook is slow → push in the background with a long timeout; check `merge-base --is-ancestor origin/main HEAD` first, the autopilot moves main often.

## Not done
- TASK-574 dispatch; PR#5743 review; archive TASK-573.
- **Operator: rotate the laptop config's Slack bot+app, Telegram bot and Discord bot tokens** (printed into a session transcript 10-19).
- Slack approve-click gap issue (ask which card was clicked); infra re-pick backoff issue (memory only).
