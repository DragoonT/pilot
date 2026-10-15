# Context marker — 2026-10-15 ~13:05Z: ticket ledger proven end to end, TASK-558 archived

**Resume with**: `/nav-start-active`. Supersedes `2026-10-15_before-compact-v2286-released.md` for this track. A parallel session owns TASK-557 (Linear state write-back, PR#5702 merged, fast-follow #5703) — see its marker `2026-10-15_linear-state-writeback-pr5702-awaiting-approval.md`; do not touch its docs.

## ONE next action
**Founder: give the founder tenant a key source.** Org `425f9f99` (EC2 `i-0289111000cebcee9`) has the 09-25 SSM layout (`ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, `PILOT_GATEWAY_TOKEN` only). Add `/tenants/425f9f99-4491-4044-9038-f50b0b0a3a5b/PILOT_ANTHROPIC_KEY_SOURCE` (+ the `_PLATFORM`/`_OWN` pair) or re-push its config, then one chat turn must show `key_source` ≠ `unknown` in `ticket_ledger`. Until then the meter counts $0 for this org.

## State
- **Ledger:** console prod-0.1.33 (reconciler td 46, 11:59Z). `ticket_ledger` org 425f9f99 = 4 execution (GH-3/5/7/9) + 1 chat_turn (12:51:57Z, est 16.613 c / reported 16.719 c). No 400 since the deploy. Testica (b79d7a56) 503 = stopped exhaustion-test box, expected.
- **TASK-558** archived: console#411 → PR#412 (b94d831c1), review APPROVE-w-notes posted on the PR (dead `since != ""` guard in fetchLedgerPage; long doc-comment line). Pin run by reviewer: both tests fail `ledger: unexpected status 400`.
- **How to read the console DB** (no psql, ECS exec off): SSM `AWS-RunShellScript` on a `pilot-fleet-instance` (e.g. `i-0620c15f34deb8669`), take `DATABASE_URL` from `docker inspect` of the reconciler container, run `docker run --rm --network host postgres:16-alpine psql "$URL" -c ...`. Read-only SELECTs only; never echo the URL.
- **How to read the tenant daemon:** config `/var/lib/pilot/config.yaml`, DB `/var/lib/pilot/home/.pilot/data/pilot.db` (python3 sqlite3, no sqlite3 CLI), token `PILOT_GATEWAY_TOKEN` in `/run/pilot/env`, route `http://127.0.0.1:9090/api/v1/executions/usage?since=...`.
- **Side observation (not filed):** the tenant side chat answered from a checkout on `pilot/GH-5`, not main.
- **Open elsewhere:** console#403 (PR#408 needs-manual-rebase) + console#404 (PR#406 pilot-needs-human) — TASK-546 session. Nav config v7.8.0 behind plugin v8.4.2; `deep_research.enabled` flip unstaged. Paddle payout settings; landing/legal (other session).
- **Process:** base-presence hold recurrence #5 today — run the backticked-path probe against the TARGET repo's main before every `gh issue create` (memory updated). Chat probe that files nothing: "What is the default branch of this repo?".
