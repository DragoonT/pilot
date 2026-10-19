# Context marker — 2026-10-19 ~09:55Z: TASK-574 dispatched (#5745), PR#5743 reviewed APPROVE-w-notes, TASK-573 archived; next: Nelya's deploy workflow PR, then docs base URL

**Resume with**: `/nav-start-active`. Supersedes `2026-10-19_site-hosting-live-reply-posted-dispatch-574-next.md` (its pilotcloud.dev + procedure blocks still hold). The 10-16 candidates still stand: GH-415 worktree-base question (`runner.go`, the `task.FromPR > 0` branch), auth-service unverified-email check, test member removal.

## ONE next action
**Watch #5745 (TASK-574)** on the box — queued 09:38Z behind GH-5716 (running since 09:28Z) and GH-5699. When its PR lands, review it with the standard procedure. In parallel, check the #infrastructure thread `1791555910.941859` for Nelya's deploy-workflow PR + slot; after her merge: docs base URL (4 files under `docs/`, README, ~30 refs), `docsUrl` in the site, Paddle resubmit, U1 console footer links.

## State (verified 09:39Z)
- **Box:** daemon v2.288.1 (self-upgrade now verified), uptime 4d18h, 1 proc. Queue: GH-5716 running · GH-5699 queued · GH-5745 queued.
- **TASK-574 → #5745** filed 09:38Z (`pilot` + `no-decompose`); path probe clean (6 paths on origin/main; the one MISS was a Go subtest name).
- **PR#5743 (TASK-573) reviewed APPROVE-w-notes, posted 10-19.** Option A (supersede at both self-close sites), 6 new tests, 3 pins hold, demotion ordering safe (CAS excludes `superseded`; `ReclassifyCompletionAsFailed` matches only `completed`), memoryStore fallback is a real fix (evalStore only wired with learning on). Notes → **TASK-575 → #5747**: (1) closed original keeps `pilot`/`pilot-in-progress` labels — `owner_death.go:243-248` returns on `closed` before the label strip, doc comment at `:67` stale; (2) supersede on a still-`running` row is a silent no-op (`controller.go:10899`, GH-4499 shape) — the re-pick loop is still open on that path; add a Warn on zero rows. TASK-573 archived; graph node updated.
- **Open pilot issues older than this track:** #5716 (approval handler default-repo only, running now), #5699 (epic sub-issues ignore default_branch).
- **Docs:** README P1 row + Recent updated for 574/573; `tasks/archive/TASK-573…` is the path now. Line 168 still says PR#5713 "review pending" — stale since 10-16, harmless.

## Not done
- ~~Follow-up for the PR#5743 notes~~ → TASK-575 → #5747 dispatched 10-19 ~10:05Z (queued behind GH-5716/5699/5745). Review its PR with the standard procedure when it lands.
- **Operator: rotate the laptop config's Slack bot+app, Telegram bot and Discord bot tokens** (printed into a session transcript 10-19).
- Slack approve-click gap issue; infra re-pick backoff issue (memory only).
