# fix(comms): continue PR #5637 — keep web operational queries on the old path and rewrite TestChatAPI_Composed for the chat-turn flow

**Status**: ✅ DONE 2026-10-11 — [#5638](https://github.com/qf-studio/pilot/issues/5638) picked 11:09Z, commits landed on pilot/GH-5635, PR#5637 green + merged 11:22Z; issue closed by hand (autopilot closer did not fire for a hand-filed fix issue). (CI-fix continuation of #5635 / PR#5637; labels `pilot` + `autopilot-fix` + `no-decompose`)
**Created**: 2026-10-11
**Repo**: qf-studio/pilot

## Context

PR #5637 (branch pilot/GH-5635, issue #5635) implements the web chat agentic path. Its CI test job failed in the gateway package:

```
chat_test.go:512: event type = "text", want confirmation
--- FAIL: TestChatAPI_Composed (0.11s)
FAIL	github.com/qf-studio/pilot/internal/gateway
```

TestChatAPI_Composed in `internal/gateway/chat_test.go` encodes the old web flow (task text leads to a confirmation event, then an execute callback leads to progress and result events). With PR #5637 every web text turn goes through ExecuteChatTurn, so the task-shaped text now yields a text event. The autopilot size guard refused to spawn its own fix issue (231 production additions, limit 200), so this issue is the continuation. Work on the existing branch pilot/GH-5635 and push to PR #5637; do not open a new PR.

## Implementation

Two changes on branch pilot/GH-5635.

1. In `internal/comms/handler.go`, the web routing added by PR #5637 must not capture operational queries. When msg.Platform equals "web" and intent.IsOperationalQuery(text) is true, keep the existing handleOperational path (for example "queue status"). Add TestWebChat_OperationalQueryKeepsOldPath to the branch file internal/comms/chat_turn_handler_test.go (exists on the PR branch, not on main): the web text "queue status" makes zero chat-turn backend calls and the messenger receives the operational reply text.

2. Rewrite TestChatAPI_Composed in `internal/gateway/chat_test.go`. Keep steps 1 (auth), 2 (operational query) and 4 (approval-shaped callback rejected with 400) as they are. Rewrite step 3: the task-shaped text "build the project" now yields a text event whose text equals the fake backend output. Rewrite step 5 as the pilot-issue flow: extend chatTestBackend so that, when the prompt contains "file an issue", it first calls opts.EventHandler with one EventTypeToolUse event (ToolName Read, ToolInput file_path README.md) and then returns an Output that ends with a valid pilot-issue block (title "feat(chat): composed test issue", labels pilot, body with the five H2 sections Context, Scope, Acceptance Criteria, Out of scope, Refs). Add a stub IssueCreator to the HandlerDeps in the test that records the call and returns the URL https://github.com/qf-studio/pilot/issues/1. Then assert, in order: a progress event whose TaskID is "chat-task-conv"; a confirmation event whose TaskID starts with "issue-" and whose MessageRef equals its TaskID; after an execute callback (202) a text event that contains that URL; and the stub recorded exactly one CreateIssue call whose labels contain pilot.

Touch only the three files named above. Keep the diff under 200 changed lines.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go test ./internal/gateway/ -run TestChatAPI_Composed -count=1` passes; paste the output into the PR body.
- `go test ./internal/gateway/ -count=1` passes; paste the output into the PR body.
- `go test ./internal/comms/ -count=1` passes; paste the output into the PR body.
- `go vet ./internal/comms/ ./internal/gateway/` passes; paste the output into the PR body.
- route a web operational query such as "queue status" into handleChatTurn -> TestWebChat_OperationalQueryKeepsOldPath fails
- make the stub IssueCreator return an error -> TestChatAPI_Composed fails
- The commits land on branch pilot/GH-5635 and PR #5637 turns green; no new PR is opened.

## Refs

- Pilot issue: https://github.com/qf-studio/pilot/issues/5638
- Source issue: https://github.com/qf-studio/pilot/issues/5635 (TASK-520, leg 2a of TASK-518)
- PR under repair: https://github.com/qf-studio/pilot/pull/5637
- Failing run: https://github.com/qf-studio/pilot/actions/runs/38131676382/job/114447117839

**Last Updated**: 2026-10-11

<!-- autopilot-meta branch:pilot/GH-5635 pr:5637 iteration:1 source:5635 sha:c29bbf79f23438b75e652eeb65a85f474dd81293 -->
