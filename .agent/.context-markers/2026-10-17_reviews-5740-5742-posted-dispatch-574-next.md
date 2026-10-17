# Context marker — 2026-10-17 ~14:00Z: PR#5740/#5742 reviewed, TASK-571/572 archived; next: dispatch TASK-574, review PR#5743

**Resume with**: `/nav-start-active`. Supersedes `2026-10-17_executor-fastfollows-reviewed-repick-loop-5741-queued.md`. The 10-16 marker's candidates still stand: GH-415 worktree-base question (`runner.go`, the `task.FromPR > 0` branch), auth-service unverified-email check, test member removal. Nav config sync is DONE (commit e409f5afa).

## ONE next action
**Dispatch TASK-574 to Pilot** (`.agent/tasks/TASK-574-bootstrap-callsite-test-and-attempt-guard-key.md`, nav-pilot skill, H1 as title, `--body-file`, labels `pilot` + `no-decompose`). Run the mechanical backticked-path probe first: every backticked path in the body must exist on `origin/main`; no git refs or home paths in prose. Then **review PR#5743** (GH-5741 / TASK-573, merged 13:35Z, self-close hand-off writes `superseded`) with the standard procedure and archive TASK-573.

## State (all verified; docs on origin/main at 88c3e0561 + this commit)
- **Reviewed 10-17:** PR#5740 (GH-5738, TASK-571) **APPROVE with notes** — 2/2 pins kill; notes: the "older commit was rewritten" assertion reads the pre-strip SHA (vacuous), `task_id`/`branch` substrings satisfied by either WARN, `for-each-ref` is the right detector. PR#5742 (GH-5739, TASK-572) **APPROVE with defects** — 2/3 pins kill; pin C (`runner.go:3949` passes `executionPath` twice) survives because the mirror subtest's lookup returns `false` and the auto-init gate at `:3944` short-circuits; `navBootstrapAttempted` keyed on `executionPath` = per task under worktree isolation. Both defects → TASK-574 (planned, unfiled).
- **Shipped, unreviewed:** PR#5743 (#5741, TASK-573) merged 13:35Z.
- **Archived:** TASK-571, TASK-572. Memories: `test-asserts-on-pre-rewrite-sha-is-vacuous`, `process-guard-keyed-on-execution-path-is-per-task-under-worktree-isolation` (indexed; `check-graph` OK, 743 nodes).
- **Box:** v2.288.0; #5736/#5737/#5740/#5742/#5743 ride the 10-17 14:00Z train. LIN-* rows are the founder's own queue.
- **Procedure (unchanged):** spec in /tmp/issue-<n>.md; background review agent in a detached worktree at the merge commit (build/vet/targeted/full package/lint + spec pins + a free mutation on the production call site); verify the agent's three anchors by reading the lines before posting; `gh pr review --comment` (request-changes refused on own PRs). Graph: `nodes` is `{concepts, tasks, memories}` maps, not flat — insert memories under `nodes.memories`, tasks under `nodes.tasks`, then `concept_index`, `edges`, `stats`.

## Not done
- TASK-574 dispatch; PR#5743 review; archive TASK-573.
- Slack approve-click gap issue (ask the founder which card was clicked first); infra re-pick backoff issue (memory only).
- 10-16 candidates (2)–(4) above.
