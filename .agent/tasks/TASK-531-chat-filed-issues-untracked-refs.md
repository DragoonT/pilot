# fix(comms): chat-filed issues must not cite untracked paths (base-presence hold)

**Status**: ✅ REVIEWED 2026-10-13 — [#5650](https://github.com/qf-studio/pilot/issues/5650) → PR#5653 (38b993a4e, +194/-0, autopilot-merged 11:13Z), review **APPROVE** (3/3 pins kill; full comms suite ok). Notes-only: the card-step probe fetches origin once per draft (own cache, not the runner's baseRefCache) and fails open on a fetch collision with the executor.
**Created**: 2026-10-13
**Repo**: qf-studio/pilot

Blocked by: none

## Context

Side-chat smoke on a tenant, 2026-10-13: the chat-drafted issue cited `.agent/DEVELOPMENT-README.md` in backticks. On tenant clones the .agent directory is an untracked Pilot scaffold written by `internal/executor/navigator.go`, so the dispatcher's base-presence gate held the task for 7 minutes ("Task held: prerequisite not on main") until a human edited the body. The chat prompt itself tells the agent to read the .agent index (`internal/executor/chat_prompt.go`) and its issue contract never forbids citing it.

Fix at two layers: a prompt rule (cheap, reduces incidence) and a deterministic post-draft rewrite at the card step (catches every untracked reference, not only .agent). Do NOT add a dispatcher-side .agent ignore prefix: in Pilot's own repo the .agent directory is tracked on main, so the extractor's verdict there is correct, and a global loosening of a safety gate for one producer's habit is the wrong seam.

## Scope

- `internal/executor/chat_prompt.go`, the issue contract: add one rule, "Never backtick anything under .agent/ (Pilot scaffold, untracked on most repos); cite only paths tracked on the default branch."
- `internal/executor/base_presence.go`: add an exported PathsMissingOnDefaultBranch(ctx, dir string, paths []string) ([]string, error). It builds the local checkout probe for dir and calls FileExistsOnDefaultBranch per path. Any lookup error returns (nil, err) so callers fail open. Wrap ctx in a 20 second timeout.
- `internal/executor/dependency_detector.go`: add an exported UnquoteReferencedPaths(body string, paths []string) string that strips the backticks from every span whose line-ref-stripped form is in paths. Reuse the existing backtick span and line-ref regexes.
- `internal/comms/chat_turn_handler.go`, handleChatTurn, in the default case before presentIssueCard: run executor.ExtractReferencedPaths on the draft body. If non-empty, call a new Handler func field missingPathsOnBase (defaulted in NewHandler to executor.PathsMissingOnDefaultBranch, overridable in tests) with the active project path. On missing references: rewrite the body with UnquoteReferencedPaths, send one text line "N reference(s) not on the default branch were rewritten as plain text: ..." and still present the card. On a probe error: log a warning and present the card unchanged. Rewrite rather than reject, because a reject costs another model turn that may repeat the mistake, while the user still gets the card and can discard it.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go vet ./internal/comms/ ./internal/executor/` passes; paste the output into the PR body.
- `go test ./internal/comms/ -run TestWebChat_IssueCard -count=1` passes; paste the output into the PR body. Adds TestWebChat_IssueCardUntrackedRefsRewrittenToPlainText (the newWebChat backend output cites one tracked and one untracked path; the fake seam reports the untracked one; the pending card body keeps the tracked backticks and drops the other) and TestWebChat_IssueCardProbeErrorFailsOpen (the seam returns an error; the body is unchanged; the card is still presented). The existing TestWebChat_IssueBlockPresentsCard stays green.
- `go test ./internal/executor/ -run TestPathsMissingOnDefaultBranch -count=1` passes; paste the output into the PR body. Uses the newForgeProject fixture: a tracked file is reported present, a path under .agent is reported missing, and a fetch failure returns an error rather than a path list.
- `go test ./internal/executor/ -run TestChatPrompt -count=1` passes; paste the output into the PR body. Adds TestChatPrompt_ForbidsAgentDirRefs.
- delete the .agent sentence from the chat issue contract -> TestChatPrompt_ForbidsAgentDirRefs fails
- skip the UnquoteReferencedPaths rewrite in handleChatTurn -> TestWebChat_IssueCardUntrackedRefsRewrittenToPlainText fails
- return the input paths instead of the error on probe failure in PathsMissingOnDefaultBranch -> TestPathsMissingOnDefaultBranch_FetchFailureIsError fails

## Out of scope

- The dispatcher-side ignore prefix list and the Jev base-presence classifier.
- Telegram and Slack issue intake paths.
- Rewriting paths that belong to another repository.

## Refs

- `internal/executor/chat_prompt.go` (issue contract), `internal/comms/chat_turn_handler.go` (handleChatTurn, presentIssueCard)
- `internal/executor/base_presence.go` (local checkout probe, FileExistsOnDefaultBranch), `internal/executor/dependency_detector.go` (ExtractReferencedPaths)
- `internal/executor/navigator.go` (the .agent scaffold writer)
- Test fixtures: `internal/comms/chat_turn_handler_test.go` (newWebChat), `internal/executor/base_presence_gh5601_test.go` (newForgeProject)
- SOP: `.agent/sops/onboarding/new-project-issue-authoring.md` Rule 3b
- Pilot issue: https://github.com/qf-studio/pilot/issues/5650
