# feat(executor): read-only chat-turn execution mode with session resume, progress events and a Navigator chat prompt

**Status**: ✅ MERGED + REVIEWED 2026-10-09 — [#5632](https://github.com/qf-studio/pilot/issues/5632) → PR#5633 merged by autopilot 15:17Z (c818cfa21, +657/-0, three new files). Post-merge review **APPROVE-w-notes** on the PR: all 6 mutation pins run by the reviewer and kill; 13/13 tests. Notes: `SessionReset` is dead on the Claude Code backend (internal retry) → leg 2 detects reset by `SessionID` change; max-turns = substring on raw result line.
**Created**: 2026-10-09
**Repo**: qf-studio/pilot

## Context

The console side chat sends every web turn through `comms.Handler`, which runs read-only intents (question, research, chat) via `runner.Execute` with `LocalMode: true`. That path builds the bench prompt in `internal/executor/prompt_builder.go` ("Phase 2: IMPLEMENT", "write code NOW", "never spend more than 2 tool calls on reading") and prepends the executor header that says "do not ask to create a GitHub issue". The session gets the full toolbox with `--dangerously-skip-permissions` in the shared project root, so a chat turn can edit files. Each turn is a fresh process: the backend supports `ResumeSessionID` (`internal/executor/backend.go`) but the chat never sets it. Tool events are parsed in `internal/executor/backend_claudecode.go` but never reach the chat, so the user sees nothing for up to three minutes.

This issue adds a dedicated execution entry point for chat turns. It does not change `Execute`, `BuildPrompt`, `buildLocalModePrompt`, the comms handler, or any wire format. The handler wiring is the next issue. The Navigator plugin is not installed on tenant boxes, so the research method must live in the prompt text, not in plugin skills.

## Implementation

Create a new file internal/executor/chat_turn.go (plain name, file does not exist on main) with:

- Type ChatTurn with fields ConversationID string, ProjectPath string, Text string, ResumeSessionID string, MaxTurns int (default 40 when zero), Timeout time.Duration (default 5 minutes when zero).
- Type ChatTurnResult with fields Text string, SessionID string, Partial bool (true when the backend stopped on MaxTurns or the timeout), SessionReset bool (true when the backend reported session-not-found and the turn ran without resume), ToolCalls int.
- Exported variable ChatReadOnlyTools, a string slice with exactly these entries in this order: Read, Grep, Glob, LS, Task, Bash(git log:*), Bash(git show:*), Bash(git diff:*), Bash(git blame:*), Bash(git ls-files:*), Bash(rg:*), Bash(ls:*). No Edit, no Write, no MultiEdit, no NotebookEdit, no unscoped Bash.
- Method ExecuteChatTurn on Runner with signature (ctx context.Context, turn ChatTurn, onProgress func(message string)) (ChatTurnResult, error). It must:
  - Build the prompt with BuildChatPrompt (below) when ResumeSessionID is empty, and send only the user text when ResumeSessionID is set (the persona lives in the resumed session).
  - Call the backend through the backendExecute chokepoint in `internal/executor/backend_execute_guard.go`, never `r.backend.Execute` directly. Pass ExecuteOptions with Prompt, ProjectPath = turn.ProjectPath, ResumeSessionID, AllowedTools = ChatReadOnlyTools, MaxTurns, Model from the runner config, and an EventHandler.
  - Not construct a Task, not call the execution lifecycle, not create a task doc, not create a branch or worktree, not run quality gates, not create a PR. The chokepoint's worktree expectation does not apply because there is no Task; document this in the guard if it needs a new call site.
  - Forward each EventTypeToolUse backend event to onProgress as one line: tool name, a space, then the first argument. First argument by tool: Read uses file_path, Grep uses pattern, Glob uses pattern, Bash uses command cut to 80 characters, Task uses description, LS uses path, otherwise empty. Drop a line identical to the previous one. Deliver at most one line per 500 ms; the last pending line wins.
  - Capture SessionID from the result. When the backend returns ErrorTypeSessionNotFound for a resumed turn, the existing fallback in `internal/executor/backend_claudecode.go` retries without resume; set SessionReset true in that case.
  - Apply the timeout with a derived context; on timeout or MaxTurns return the text collected so far with Partial true and a nil error.
- Function BuildChatPrompt(projectPath string, userText string) string in a new file internal/executor/chat_prompt.go (plain name, file does not exist on main). The prompt must contain, in this order:
  1. A persona line: "You are the Navigator research assistant for this repository. You answer questions about the code and you draft Pilot issues. You never edit files."
  2. The research method: first read .agent/DEVELOPMENT-README.md when it exists and treat it as the index; then grep .agent/knowledge/graph.json and the files under .agent/knowledge/memories for the topic and cite matching memories instead of re-deriving them; then sample representative files instead of reading everything; cite every claim as a path and line number in the form path:line; keep answers under 300 words unless the user asks for depth.
  3. The read-only statement: "Your tools are read-only. Do not attempt Edit, Write or any command that changes the tree."
  4. The issue-authoring contract, used only when the user asks to file, create, open or dispatch an issue or ticket. The reply must end with exactly one fenced block whose info string is pilot-issue and whose body is YAML with keys title, labels and body. The title is a conventional-commit title that matches the regex in `internal/adapters/github/issue_create.go`. labels is a list that contains pilot. body is a markdown string with H2 sections Context, Scope, Acceptance Criteria, Out of scope and Refs. Files that do not exist yet are written in plain text, never in backticks; only files that exist on the default branch may be backticked. Every acceptance bullet names a test. Work above about 500 changed lines is split into several issues with a "Blocked by: #N" line. The assistant never states that the issue was filed; the daemon files it after the user confirms.
  5. The user text, after a separator line.
  The prompt must not contain the strings "Phase 2: IMPLEMENT", "write code NOW", or "do not ask to create a GitHub issue".

Tests in a new file internal/executor/chat_turn_test.go (plain name) using a fake Backend that records the ExecuteOptions it received and replays scripted BackendEvents:

- TestChatTurn_AllowlistExcludesWriteTools asserts the recorded AllowedTools equals ChatReadOnlyTools and contains none of Edit, Write, MultiEdit, NotebookEdit or a bare Bash entry.
- TestChatTurn_ResumePassedToBackend asserts ResumeSessionID reaches ExecuteOptions on a second turn and the Prompt equals the user text only.
- TestChatTurn_FirstTurnUsesChatPrompt asserts the first turn's Prompt contains the persona line and the user text.
- TestChatTurn_ProgressForwardsToolUse replays Read, Grep and Bash tool_use events and asserts the three progress lines "Read internal/comms/handler.go", "Grep IssueCreator" and "Bash git log --oneline -5" arrive in order, and that a repeated identical event produces no extra line.
- TestChatTurn_SessionNotFoundResets asserts SessionReset is true when the fake backend first returns ErrorTypeSessionNotFound and then succeeds.
- TestChatTurn_TimeoutReturnsPartial asserts Partial is true and the error is nil when the fake backend blocks past a 50 ms timeout.
- TestChatTurn_NoTaskSideEffects runs a turn against a temp project directory with an empty .agent/tasks folder and asserts the directory is unchanged afterwards.
- TestChatPrompt_ContainsNavigatorMethod asserts BuildChatPrompt output contains ".agent/DEVELOPMENT-README.md", "graph.json" and "path:line".
- TestChatPrompt_ExcludesExecutorPersona asserts the output does not contain "Phase 2: IMPLEMENT", "write code NOW" or "do not ask to create a GitHub issue".
- TestChatPrompt_IssueContract asserts the output contains "pilot-issue", "Blocked by: #N" and "never in backticks".

Do not change `internal/executor/prompt_builder.go`, `internal/executor/runner.go` beyond adding the method, `internal/comms/handler.go`, `internal/gateway/chat.go`, or any config schema. Keep the diff under 500 changed lines.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go test ./internal/executor/ -run TestChatTurn -count=1` passes; paste the output into the PR body.
- `go test ./internal/executor/ -run TestChatPrompt -count=1` passes; paste the output into the PR body.
- `go vet ./internal/executor/` passes; paste the output into the PR body.
- add the entry Edit to ChatReadOnlyTools -> TestChatTurn_AllowlistExcludesWriteTools fails
- clear ResumeSessionID before calling the backend chokepoint -> TestChatTurn_ResumePassedToBackend fails
- delete the ".agent/DEVELOPMENT-README.md" sentence from BuildChatPrompt -> TestChatPrompt_ContainsNavigatorMethod fails
- append the string "Phase 2: IMPLEMENT" to BuildChatPrompt -> TestChatPrompt_ExcludesExecutorPersona fails
- stop forwarding EventTypeToolUse events to onProgress -> TestChatTurn_ProgressForwardsToolUse fails
- stop setting SessionReset after the session-not-found fallback -> TestChatTurn_SessionNotFoundResets fails
- The new method calls the backend only through the chokepoint in `internal/executor/backend_execute_guard.go`; a grep for "r.backend.Execute(" in the new file returns nothing.
- The PR touches no file under internal/comms, internal/gateway or internal/adapters.

## Refs

- Pilot issue: https://github.com/qf-studio/pilot/issues/5632
- PR: https://github.com/qf-studio/pilot/pull/5633 (merged, reviewed APPROVE-w-notes)

- Plan: TASK-518 in this repo (.agent/tasks/TASK-518-side-chat-navigator-research-and-issue-filing.md), leg 1 of 5
- Backend options: `internal/executor/backend.go` (ExecuteOptions: ResumeSessionID, AllowedTools, MaxTurns, EventHandler)
- Tool-use event shape: `internal/executor/backend_claudecode.go` (EventTypeToolUse with ToolName and ToolInput)
- Session-not-found fallback: `internal/executor/backend_claudecode.go` (GH-2377)
- Title regex: `internal/adapters/github/issue_create.go`
- Prior chat work: TASK-463, TASK-464, TASK-469, TASK-514

**Last Updated**: 2026-10-09
