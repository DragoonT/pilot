# feat(chat): wire a per-project IssueCreator into the web chat handler in both daemon modes

**Status**: ✅ MERGED + REVIEWED 2026-10-11 — [#5636](https://github.com/qf-studio/pilot/issues/5636) → PR#5639 merged 11:50Z (7087bac38, +234/-32); post-merge review **APPROVE-w-notes** (3/3 pins kill). Was blocked by #5635 (leg 2b of TASK-518; labels `pilot` + `no-decompose`)
**Created**: 2026-10-11
**Repo**: qf-studio/pilot

Blocked by: #5635

## Context

The web chat handler is built at two sites: polling mode in `cmd/pilot/main.go` (the block that logs "Chat API enabled in polling mode") and gateway mode in `internal/pilot/pilot.go` (the block that logs "Chat API initialized for gateway mode"). Neither passes IssueCreator in HandlerDeps, so the chat can never file an issue. The Telegram and Slack block in `cmd/pilot/main.go` builds commsIssueCreator from adapters.github.repo only, with a single IssueCreatorEntry, so a daemon with several projects always files into the first repo.

Tenant configs rendered by the console carry one entry per repo under projects, each with a github block that has owner and repo and a path under /var/lib/pilot/repos (pilot-console, file internal/fleet/configrender.go in that repo). The daemon config type for that block is ProjectGitHubConfig in `internal/config/config.go`. The GitHub issue creator in `internal/adapters/github/issue_creator.go` already accepts one IssueCreatorEntry per project path and resolves by exact path match before it falls back to the first entry.

## Implementation

- In `cmd/pilot/main.go`, extract the commsIssueCreator construction into a function buildCommsIssueCreator(cfg) that returns comms.IssueCreator. It returns nil when GitHub is disabled or no token resolves. It builds the entry list as follows: one IssueCreatorEntry per cfg.Projects item whose github block has both owner and repo, with ProjectPath equal to the project path; then, when adapters.github.repo is set and no project entry already covers adapters.github.project_path, one entry for it (owner and repo split from adapters.github.repo, ProjectPath equal to adapters.github.project_path). The Telegram and Slack block uses this function instead of the inline code, with no behaviour change for a single-repo config.
- Pass the result as IssueCreator in the polling-mode web HandlerDeps in `cmd/pilot/main.go`.
- Add an option WithChatIssueCreator(ic comms.IssueCreator) in `internal/pilot/pilot.go` that stores the creator on the Pilot struct, and pass it as IssueCreator in the gateway-mode web HandlerDeps. In `cmd/pilot/main.go`, pass pilot.WithChatIssueCreator(buildCommsIssueCreator(cfg)) next to the existing WithChatHandler option.
- Log one Info line at each site when the creator is nil: "Chat issue filing disabled: GitHub not configured".

Tests:

- In a new file cmd/pilot/comms_issue_creator_test.go (plain name): TestBuildCommsIssueCreator_PerProjectEntries builds a config with two projects that have github owner and repo and no adapters.github.repo, and asserts a non-nil creator whose CreateIssue, run against an httptest GitHub server, posts to the second project's owner and repo when given the second project's path. TestBuildCommsIssueCreator_NilWithoutGitHub asserts nil when adapters.github is disabled. TestBuildCommsIssueCreator_AdapterRepoFallback asserts that with only adapters.github.repo set, the single entry has the adapter's owner and repo. Use testutil.FakeGitHubToken or the string "test-github-token" for the token; never a realistic token.
- In a new file internal/pilot/chat_issue_creator_test.go (plain name): TestWithChatIssueCreator_ReachesHandlerDeps asserts the option stores the creator and that the gateway-mode construction passes it (expose a small accessor or inspect via the handler's behaviour with a mock creator).

Keep the diff under 250 changed lines. Do not change `internal/comms/handler.go` or anything under internal/adapters.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go test ./cmd/pilot/ -run TestBuildCommsIssueCreator -count=1` passes; paste the output into the PR body.
- `go test ./internal/pilot/ -run TestWithChatIssueCreator -count=1` passes; paste the output into the PR body.
- `go vet ./cmd/pilot/ ./internal/pilot/` passes; paste the output into the PR body.
- drop the per-project loop and keep only the adapters.github.repo entry -> TestBuildCommsIssueCreator_PerProjectEntries fails
- return a creator even when adapters.github is disabled -> TestBuildCommsIssueCreator_NilWithoutGitHub fails
- ignore the option and leave IssueCreator nil in the gateway-mode HandlerDeps -> TestWithChatIssueCreator_ReachesHandlerDeps fails
- The Telegram and Slack block in `cmd/pilot/main.go` no longer contains an inline github.NewIssueCreator call; it calls buildCommsIssueCreator.

## Refs

- Pilot issue: https://github.com/qf-studio/pilot/issues/5636
- Plan: TASK-518 in this repo (.agent/tasks/TASK-518-side-chat-navigator-research-and-issue-filing.md), leg 2b of 5
- Leg 2a: https://github.com/qf-studio/pilot/issues/5635
- Leg 1 (merged): https://github.com/qf-studio/pilot/pull/5633
- Creator: `internal/adapters/github/issue_creator.go` (NewIssueCreator, IssueCreatorEntry, resolveRepo)
- Config: `internal/config/config.go` (ProjectGitHubConfig)
- Construction sites: `cmd/pilot/main.go`, `internal/pilot/pilot.go`
- Token constants: `internal/testutil/tokens.go`

**Last Updated**: 2026-10-11
