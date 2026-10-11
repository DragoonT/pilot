# feat(comms): route web chat turns through ExecuteChatTurn with progress events and a confirmed pilot-issue card

**Status**: 🚀 Dispatched to Pilot 2026-10-11 → [#5635](https://github.com/qf-studio/pilot/issues/5635) (leg 2a of TASK-518; labels `pilot` + `no-decompose`)
**Created**: 2026-10-11
**Repo**: qf-studio/pilot

## Context

PR #5633 added ExecuteChatTurn in `internal/executor/chat_turn.go`: a read-only, resumable Claude Code turn with a Navigator research prompt, tool-use progress lines, and an issue-authoring contract that ends the reply with one fenced block whose info string is pilot-issue. Nothing calls it yet. The web chat still goes through `internal/comms/handler.go` HandleMessage, which runs detectIntent and the LocalMode executor paths, so a console chat turn still gets the bench prompt and full write tools.

This issue makes every non-command web turn an agentic chat turn, forwards progress to the conversation, and turns the pilot-issue block into a confirmation card that the user must accept before the daemon files the issue through the existing IssueCreator interface in `internal/comms/issue_intake.go`. Only Platform "web" changes. Telegram, Slack and Discord keep the current comms brain. The IssueCreator wiring from per-project config is the next issue; this issue only consumes HandlerDeps.IssueCreator, which already exists in `internal/comms/factory.go`.

Facts to rely on. The web adapter builds IncomingMessage with Platform "web" and ContextID "web:" plus the conversation id (`internal/adapters/web/api.go`). The WebMessenger (`internal/adapters/web/messenger.go`) already has SendConfirmation, SendProgress, SendChunked and SendText; SendConfirmation appends a confirmation event with TaskID and MessageRef equal to the taskID argument. The handler keeps per-conversation maps activeProject, pendingTasks and pendingIssues under h.mu (`internal/comms/handler.go`). Callback actions reaching HandleMessage are execute, confirm, yes, cancel and no. The Claude Code backend retries without resume internally on session-not-found, so ChatTurnResult.SessionReset never fires there; detect a reset by a changed SessionID. The conventional-commit title regex lives in `internal/adapters/github/issue_create.go`; comms cannot import that package (adapters/github imports comms), so comms carries its own copy of the regex text.

## Implementation

In `internal/comms/handler.go`:

- Add two per-conversation maps under h.mu: chatSessions (contextID to Claude session id) and pendingIssueCards (contextID to a pendingIssueCard value with fields Draft IssueDraft, CardID string, ProjectPath string, CreatedAt time.Time). Initialize them in the constructor. Clear the chatSessions entry in SetActiveProject.
- In HandleMessage, after the rate limit check and before the callback switch, add the web routing: when msg.Platform equals "web" and msg.IsCallback is true and a pendingIssueCard exists for the context, route execute, confirm, yes and file to handleIssueCardDecision with confirmed true, and cancel, no and discard with confirmed false, then return. When msg.Platform equals "web", msg.IsCallback is false, and the text is a yes or no shortcut while a pendingIssueCard exists, route the same way. When msg.Platform equals "web", the text does not start with a slash, and it is not a confirmation shortcut, call handleChatTurn and return. Everything else keeps the current flow.
- Add handleChatTurn(ctx, contextID, threadID, text). It resolves the project path with getActiveProjectPath, reads the resume id from chatSessions, and calls h.runner.ExecuteChatTurn with ChatTurn fields ConversationID equal to contextID, ProjectPath, Text and ResumeSessionID. The onProgress callback calls h.messenger.SendProgress with messageRef empty, taskID equal to "chat-" plus the contextID without the "web:" prefix, phase "research", progress 0 and detail equal to the line. After the turn: store result.SessionID in chatSessions when non-empty; if the runner is nil send the text "Chat is not available: no runner configured" and return; on error send "Chat turn failed: " plus the error text and return. Split the reply with extractPilotIssueBlock (below). Send the remaining text with SendChunked, prefix empty. When result.Partial is true, append the line "(Stopped early: turn limit or timeout.)" to the text. When a block was present, call presentIssueCard.
- Add presentIssueCard(ctx, contextID, threadID, draft IssueDraft, projectPath). When h.issueCreator is nil, send the text "GitHub is not configured for this project, so the issue cannot be filed. Here is the draft:" followed by the title and body, and return. Otherwise build CardID as "issue-" plus eight hex characters from crypto/rand, store the pendingIssueCard (replacing any older one), and call SendConfirmation with taskID equal to CardID, desc equal to "File Pilot issue: " plus the title, a blank line, and the first 400 characters of the body, and project equal to the project name from h.projects.GetProjectByPath when known.
- Add handleIssueCardDecision(ctx, contextID, threadID, confirmed bool). Pop the pendingIssueCard under h.mu. When none exists send "No pending issue card." and return. When confirmed is false send "Issue draft discarded." and return. When the card is older than 30 minutes send "Issue card expired. Ask again to draft it." and return. Otherwise append the Refs line (below) to the body, ensure the label pilot is present, call h.issueCreator.CreateIssue(ctx, card.ProjectPath, draft), and send "Filed " plus the URL on success or "Issue filing failed: " plus the error on failure.
- The Refs line: when the body contains an H2 heading "## Refs", append a bullet "- Filed from Pilot Console chat " plus the conversation id (contextID without the "web:" prefix) at the end of the body; otherwise append a new "## Refs" section with that bullet.

In a new file internal/comms/pilot_issue_block.go (plain name, file does not exist on main):

- Function extractPilotIssueBlock(reply string) (text string, draft IssueDraft, found bool, err error). It finds the last fenced block whose opening fence is three backticks followed by pilot-issue, parses the block body as YAML with gopkg.in/yaml.v3 into keys title (string), labels (list of strings) and body (string), and returns the reply with the block removed and trailing whitespace trimmed. When no block exists, found is false and err is nil. When the block exists but the YAML is invalid, title is empty, body is empty, or the title does not match the conventional-commit regex copied from `internal/adapters/github/issue_create.go`, found is true and err describes the problem; handleChatTurn then sends "The issue draft was not valid: " plus the error and does not present a card. The label pilot is added when missing.

In `internal/comms/handler.go` HandleMessage the existing text shortcut branch for yes and no must not run before the pendingIssueCard check for web, otherwise a yes with no pending task answers "No pending task to confirm."

Tests in a new file internal/comms/chat_turn_handler_test.go (plain name) using the existing mockMessenger from `internal/comms/commands_test.go` and mockIssueCreator from `internal/comms/issue_intake_test.go`, plus a fake executor backend (copy the chatFakeBackend shape from `internal/executor/chat_turn_test.go` or build the runner with executor.NewRunnerWithBackend and a local fake):

- TestWebChat_PlainTextRunsChatTurn: a web message "where is the router?" produces exactly one backend call whose AllowedTools equals executor.ChatReadOnlyTools, and the mockMessenger receives one SendChunked with the backend output.
- TestWebChat_NonWebPlatformUnchanged: the same text with Platform "telegram" makes zero backend calls through ExecuteChatTurn (it follows the old intent path).
- TestWebChat_SlashCommandBypassesChatTurn: "/status" on web makes zero chat-turn backend calls.
- TestWebChat_SecondTurnResumes: two web messages in one context; the second backend call carries ResumeSessionID "sess-1".
- TestWebChat_SessionIdChangeIsStored: the fake backend returns SessionID "sess-2" on the second call while the handler sent "sess-1"; a third message carries "sess-2".
- TestWebChat_ProgressForwarded: the fake backend emits a Read tool_use event; the mockMessenger receives one SendProgress whose detail starts with "Read ".
- TestWebChat_IssueBlockPresentsCard: a reply that ends with a valid pilot-issue block yields one SendChunked whose text does not contain "pilot-issue" and one SendConfirmation whose taskID starts with "issue-" and whose desc contains the title; no CreateIssue call.
- TestWebChat_FileCallbackCreatesIssue: after the card, a web callback with ActionID "file" calls mockIssueCreator.CreateIssue once with the active project path, a body that ends with the Refs bullet, and labels containing "pilot"; the messenger receives a text that contains the returned URL.
- TestWebChat_DiscardCallbackCreatesNothing: ActionID "discard" sends "Issue draft discarded." and CreateIssue is never called.
- TestWebChat_YesTextConfirmsCard: the text "yes" after a card files the issue.
- TestWebChat_MalformedBlockSendsError: a block with a title "add stuff" (not conventional-commit) produces a text that starts with "The issue draft was not valid" and no SendConfirmation.
- TestWebChat_NoIssueCreatorShowsDraft: with IssueCreator nil, a valid block produces the "GitHub is not configured" text and no SendConfirmation.
- TestWebChat_PartialAppendsNote: when the fake backend marks the turn partial via an error_max_turns result event, the SendChunked text ends with "(Stopped early: turn limit or timeout.)".
- TestExtractPilotIssueBlock covers: no block; valid block; block with missing body; title without type prefix; labels without pilot get pilot appended.

Do not change `internal/gateway/chat.go`, `internal/adapters/web/api.go`, `internal/adapters/web/messenger.go`, `cmd/pilot/main.go`, `internal/pilot/pilot.go`, or anything under internal/executor. Keep the diff under 500 changed lines.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go test ./internal/comms/ -run TestWebChat -count=1` passes; paste the output into the PR body.
- `go test ./internal/comms/ -run TestExtractPilotIssueBlock -count=1` passes; paste the output into the PR body.
- `go test ./internal/comms/ -count=1` passes; paste the output into the PR body.
- `go vet ./internal/comms/` passes; paste the output into the PR body.
- route web text through detectIntent instead of handleChatTurn -> TestWebChat_PlainTextRunsChatTurn fails
- drop the Platform check so telegram text also calls handleChatTurn -> TestWebChat_NonWebPlatformUnchanged fails
- stop storing result.SessionID in chatSessions -> TestWebChat_SecondTurnResumes fails
- call CreateIssue inside presentIssueCard before the callback -> TestWebChat_IssueBlockPresentsCard fails
- skip the Refs bullet append in handleIssueCardDecision -> TestWebChat_FileCallbackCreatesIssue fails
- treat discard as confirmed -> TestWebChat_DiscardCallbackCreatesNothing fails
- accept any title in extractPilotIssueBlock -> TestWebChat_MalformedBlockSendsError fails
- The PR touches no file under internal/executor, internal/gateway, internal/adapters or cmd.

## Refs

- Pilot issue: https://github.com/qf-studio/pilot/issues/5635
- Plan: TASK-518 in this repo (.agent/tasks/TASK-518-side-chat-navigator-research-and-issue-filing.md), leg 2a of 5
- Leg 1 (merged): https://github.com/qf-studio/pilot/pull/5633 — ExecuteChatTurn, ChatReadOnlyTools, BuildChatPrompt in `internal/executor/chat_turn.go` and `internal/executor/chat_prompt.go`
- Handler: `internal/comms/handler.go` (HandleMessage, handleConfirmation, getActiveProjectPath, SetActiveProject)
- Issue intake types: `internal/comms/issue_intake.go` (IssueDraft, IssueCreator)
- Web adapter: `internal/adapters/web/api.go`, `internal/adapters/web/messenger.go`
- Title regex: `internal/adapters/github/issue_create.go`
- Prior chat work: TASK-463, TASK-464, TASK-469, TASK-514

**Last Updated**: 2026-10-11
