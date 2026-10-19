# Context marker — 2026-10-19 ~11:30Z: executor fast-follow track CLOSED (574 + 575 merged + reviewed); next: Nelya's deploy workflow, then docs base URL

**Resume with**: `/nav-start-active`. Supersedes `2026-10-19_574-dispatched-5743-reviewed-await-nelya-workflow.md` (its pilotcloud.dev + procedure blocks still hold). The 10-16 candidates still stand: GH-415 worktree-base question (`runner.go`, the `task.FromPR > 0` branch), auth-service unverified-email check, test member removal.

## ONE next action
**Check the #infrastructure thread `1791555910.941859` for Nelya's site deploy-workflow PR + slot.** After her merge: docs base URL (4 files under `docs/`, README, ~30 refs), `docsUrl` in the site, Paddle resubmit, U1 console footer links. No Pilot issue of ours is open; the queue is empty.

## State (verified 11:30Z)
- **Box:** daemon v2.288.1, queue empty. Today 4 runs completed 09:28→10:57Z, zero failures: GH-5716 → PR#5746 (09:57Z) · GH-5699 → PR#5748 (10:11Z) · GH-5745 → PR#5750 (10:38Z) · GH-5747 → PR#5751 (11:09Z). Founder: #5746/#5748 reviewed elsewhere — do not re-review.
- **PR#5743 (TASK-573)** reviewed APPROVE-w-notes → TASK-575. **PR#5750 (TASK-574)** reviewed APPROVE-w-notes: runner subtest's "≥2 lookups" is satisfied by the copy-back lookup too (harden with `backend.callCount() == 2`); no follow-up. **PR#5751 (TASK-575)** reviewed APPROVE-w-notes: both store calls, early return narrowed to `pilot-superseded`; closed+no-overlap now gets the mismatch comment (judged correct); stale "Leaving this issue open" wording at `owner_death.go:291`/`:309`; StageFailed CAS rejection logs at ERROR (GH-4423) on every hand-off — carve-out only if it shows in alerting. TASK-573/574/575 archived; graph nodes updated.
- **Next release train** carries #5746 #5748 #5750 #5751 (v2.288.2 or v2.289.0). Live proof for GH-5741/5747: the next CI-red PR on the box must produce a fix issue and no `dispatch re-pick … task is not done` line for the original.
- **Procedure (unchanged):** review agent in a detached worktree at the merge commit (or the PR head when pre-merge — diff the squash against it afterwards); three anchors by reading lines; `gh pr review --comment`. Markers dir gitignored → `git add -f`. **Push can be silently rejected when the autopilot moves main** — always `git fetch && git status -sb` after a push, rebase, push again. A `for … in` loop variable named `path` clobbers `PATH` in zsh.

## Not done
- **Operator: rotate the laptop config's Slack bot+app, Telegram bot and Discord bot tokens** (printed into a session transcript 10-19).
- Slack approve-click gap issue; infra re-pick backoff issue (memory only).
- README line 168 still says PR#5713 "review pending" (stale since 10-16, harmless).
