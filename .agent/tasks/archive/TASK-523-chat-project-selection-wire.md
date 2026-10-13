# feat(chat): project selection on the chat wire, a projects route, a per-conversation turn lock and a fence-safe issue body

**Status**: ✅ MERGED + REVIEWED 2026-10-11 — [#5640](https://github.com/qf-studio/pilot/issues/5640) → PR#5642 merged 15:14Z (2226a3264, +493/-2, 14 files); post-merge review **APPROVE-w-notes** (7/7 pins kill). Not in v2.280.0 (cut 14:55Z) → rides the next train. Deviation kept: session dropped only when the project path changes. (leg 3 of TASK-518; labels `pilot` + `no-decompose`)
**Created**: 2026-10-11
**Repo**: qf-studio/pilot

## Context

Since PR #5637 and PR #5639 every web chat turn is a read-only agentic turn (ExecuteChatTurn) and a confirmed pilot-issue card files into the active project's repo. Three gaps remain on the daemon wire before the console can expose this.

1. The console cannot choose a project. The POST body in `internal/gateway/chat.go` (chatMessageRequest) has conversationId, text, isCallback, callbackId, actionId and sender, but no project. The active project is only reachable through the "/switch" text command and otherwise defaults to the first project. A multi-repo tenant therefore always researches and files against the first repo. There is also no route that lists the projects a tenant has.
2. Two quick messages in one conversation start two concurrent ExecuteChatTurn calls with the same resume session, because `internal/adapters/web/api.go` runs HandleMessage in a goroutine per message and `internal/comms/handler.go` has no per-conversation turn lock (post-merge review note on PR #5637).
3. The pilot-issue block parser in `internal/comms/pilot_issue_block.go` ends the block at the first line that is exactly three backticks, so an issue body that contains its own fenced code snippet truncates the YAML and the card is never shown. The chat prompt in `internal/executor/chat_prompt.go` does not forbid fences inside the body.

The console proxy (pilot-console) relays the chat routes byte-faithfully and holds no chat state, so the wire change lands here first; the proxy relay and the UI are the next two issues.

## Implementation

Project on the wire:

- In `internal/comms/project.go`, add the field Repo string to ProjectInfo (the GitHub "owner/name" when the project has a github block, else empty). In `internal/config/projects.go`, populate it from ProjectConfig.GitHub when both owner and repo are set.
- In `internal/comms/handler.go`, add an exported method ActiveProject(contextID string) *ProjectInfo that returns the ProjectInfo for the conversation's active path (via h.projects.GetProjectByPath; nil when no project source). Keep getActiveProjectPath as is.
- In `internal/adapters/web/api.go`: add ProjectID string to DispatchRequest; add the error variable ErrUnknownProject. In Dispatch, when req.ProjectID is non-empty, call a.handler.SetActiveProject(contextID, req.ProjectID) before the message is dispatched; when it returns an error, return ErrUnknownProject wrapped with the id. Add a method Projects() []ProjectSummary on API that lists the handler's project source (a new exported type ProjectSummary with fields ID, Name, Path, Repo and Default, JSON tags id, name, path, repo, default; ID equals the config project name; Default is true for the project source's default project). Add a method ActiveProjectID(conversationID string) string on API that returns the active project's name for the conversation.
- In `internal/gateway/chat.go`: add ProjectID string with JSON tag projectId (omitempty) to chatMessageRequest and pass it through; map ErrUnknownProject to HTTP 400 with the body text "unknown project: " plus the id. Add ProjectID string with JSON tag projectId (omitempty) to chatMessageResponse and chatEventsResponse, filled from ActiveProjectID. Add the route GET /api/v1/chat/projects served by a new handler that writes {"projects":[...]} from Projects(); 405 for other methods; same bearer auth as the other chat routes; registered in `internal/gateway/server.go` next to the two existing chat routes, under the same nil-ChatAPI gate. Extend the ChatAPI interface in `internal/gateway/chat.go` with Projects and ActiveProjectID.

Turn lock:

- In `internal/comms/handler.go`, add chatTurnBusy map[string]bool under h.mu. In handleChatTurn (file `internal/comms/chat_turn_handler.go`), set the flag before calling ExecuteChatTurn and clear it with defer. When the flag is already set, send the text "A turn is already running for this conversation. Wait for it to finish." and return without calling the runner. Card decisions and operational queries are not blocked by the flag.

Fence-safe issue body:

- In `internal/executor/chat_prompt.go`, add one bullet to the issue-authoring contract: "Inside body, never use triple-backtick fences; use four-space indented code or tilde fences (~~~) instead." Add TestChatPrompt_ForbidsFencesInBody in `internal/executor/chat_turn_test.go` asserting the prompt contains "never use triple-backtick fences".

Tests:

- `internal/adapters/web/api_test.go`: TestDispatch_ProjectIDSetsActiveProject (a known id reaches SetActiveProject and the message dispatches), TestDispatch_UnknownProjectRejected (ErrUnknownProject, no message dispatched), TestAPI_ProjectsListsSource (two projects, the default flagged, repo filled for the one with a github block).
- `internal/gateway/chat_test.go`: TestChatProjectsRoute (401 without bearer; 200 with the JSON list; 405 on POST) and, in TestChatAPI_Composed, one new step: POST with an unknown projectId returns 400 whose body starts with "unknown project:", and the events response carries projectId for the conversation.
- `internal/comms/chat_turn_handler_test.go`: TestWebChat_TurnLockRejectsConcurrentTurn (a fake backend that blocks until released; a second web message in the same context receives the busy text and the backend sees one call; after release a third message runs), TestWebChat_TurnLockClearedAfterTurn, TestHandler_ActiveProjectReturnsInfo.
- `internal/pilot/chat_gateway_wiring_test.go`: extend the existing route test to also GET /api/v1/chat/projects and expect 200.
- A new file internal/config/projects_repo_test.go (plain name, does not exist on main): TestProjectSource_RepoFromGitHubBlock.

Do not change `internal/adapters/web/messenger.go`, `internal/executor/chat_turn.go`, `cmd/pilot/main.go` or `internal/pilot/pilot.go`. Keep the diff under 500 changed lines.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go test ./internal/adapters/web/ -count=1` passes; paste the output into the PR body.
- `go test ./internal/gateway/ -count=1` passes; paste the output into the PR body.
- `go test ./internal/comms/ -count=1` passes; paste the output into the PR body.
- `go test ./internal/pilot/ -count=1` passes; paste the output into the PR body.
- `go test ./internal/config/ -count=1` passes; paste the output into the PR body.
- `go test ./internal/executor/ -run TestChatPrompt -count=1` passes; paste the output into the PR body.
- `go vet ./internal/adapters/web/ ./internal/gateway/ ./internal/comms/ ./internal/config/` passes; paste the output into the PR body.
- ignore req.ProjectID in Dispatch -> TestDispatch_ProjectIDSetsActiveProject fails
- return nil instead of ErrUnknownProject for an unknown id -> TestDispatch_UnknownProjectRejected fails
- leave Repo empty in the project source -> TestProjectSource_RepoFromGitHubBlock fails
- skip the busy check in handleChatTurn -> TestWebChat_TurnLockRejectsConcurrentTurn fails
- never clear chatTurnBusy -> TestWebChat_TurnLockClearedAfterTurn fails
- register the projects route without the bearer middleware -> TestChatProjectsRoute fails
- delete the fence bullet from the chat prompt -> TestChatPrompt_ForbidsFencesInBody fails
- The PR touches no file under cmd and does not change `internal/adapters/web/messenger.go`.

## Refs

- Pilot issue: https://github.com/qf-studio/pilot/issues/5640
- Plan: TASK-518 in this repo (.agent/tasks/TASK-518-side-chat-navigator-research-and-issue-filing.md), leg 3 of 5
- Leg 2a: https://github.com/qf-studio/pilot/pull/5637 (handler path, card, callback) — review notes 1 and 2 are the turn lock and the fence fix
- Leg 2b: https://github.com/qf-studio/pilot/pull/5639 (per-project IssueCreator)
- Wire today: `internal/gateway/chat.go`, `internal/gateway/server.go`, `internal/adapters/web/api.go`
- Project source: `internal/config/projects.go`, `internal/comms/project.go`, `internal/config/config.go` (ProjectConfig, ProjectGitHubConfig)
- Composed test: `internal/gateway/chat_test.go`; gateway wiring test: `internal/pilot/chat_gateway_wiring_test.go`

**Last Updated**: 2026-10-11
