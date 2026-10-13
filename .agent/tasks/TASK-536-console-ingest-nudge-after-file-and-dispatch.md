# feat(syncingest): nudge the ingest worker after a chat File callback and after dispatch

**Status**: 📋 Planned 2026-10-13
**Created**: 2026-10-13
**Repo**: qf-studio/pilot-console

Blocked by: pilot-console#391 (TASK-534, shared worker.go); independent of TASK-535

## Context

Ingest is ticker-only (Run in `internal/syncingest/worker.go`, 60 second default) and the UI polls every 30 seconds, so a chat-filed or dispatched card appears up to 90 seconds late. The worker handle is dropped in `main.go` right after startSyncIngest, and the Deps of `internal/chatapi/routes.go` and `internal/boardapi/routes.go` have no ingest seam. The daemon answers the chat File callback with 202 before the issue exists (the "Filed" text arrives later through the events relay), so the chat nudge must be delayed and repeated.

## Scope

- `internal/syncingest/worker.go`: add Config.NudgeDebounce (default 2 seconds), a buffered nudges channel of org ids (capacity 64) and a lastNudge map. Nudge(orgID) is non-blocking (select with a default that drops) and debounced per org. Run gains a select case that calls nudgeOrg: list all connections, keep the ones whose OrgID matches and that are not terminated, then call the existing dispatch so reserveSlot, releaseSlot and the wait group still apply.
- `internal/chatapi/routes.go`: add an IngestNudger interface with Nudge(orgID) and a nil-legal Deps.Nudger. In `internal/chatapi/handlers.go` handleSendMessage, after a successful relay, when the request is a callback with action id file, schedule a nudge with time.AfterFunc at each delay in a package-level fileNudgeDelays slice (3 seconds and 15 seconds; zeroed in tests). The relay stays byte-faithful.
- `internal/boardapi/routes.go`: the same interface and Deps.Nudger. In `internal/boardapi/dispatch.go` call Nudge immediately after journalActivity in both the linked branch and dispatchUnlinked.
- `main.go`: keep the worker returned by startSyncIngest, pass it to registerBoard and registerChat, and set Deps.Nudger only when the worker is non-nil (a nil pointer stored in the interface would be a non-nil interface).

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go vet ./...` passes; paste the output into the PR body.
- `go test ./internal/syncingest/ -run TestWorker_Nudge -count=1` passes; paste the output into the PR body.
- `go test ./internal/chatapi/ -run TestHandleSendMessage -count=1` passes; paste the output into the PR body.
- `go test ./internal/boardapi/ -run TestHandleDispatch -count=1` passes; paste the output into the PR body.
- remove the nudges select case from Run -> TestWorker_NudgeRunsDispatchForThatOrgOnly fails
- remove the lastNudge debounce check from Nudge -> TestWorker_NudgeDebouncesSameOrgWithinWindow fails
- call processConnection directly instead of dispatch in nudgeOrg -> TestWorker_NudgeSkipsConnectionAlreadyInFlight fails
- drop the action id file guard in handleSendMessage -> TestHandleSendMessage_FileCallbackSchedulesTwoNudges fails
- remove the Nudge call from dispatchUnlinked -> TestHandleDispatch_UnlinkedHappyPathNudgesIngest fails

## Out of scope

- Webhooks, a nudge on the chat events relay, a distributed lease (the single-replica assumption stays), env wiring for NudgeDebounce, and the UI refresh (pilot-console-ui).

## Refs

- `internal/syncingest/worker.go`, `internal/syncingest/worker_test.go` (reserveSlot and releaseSlot tests)
- `internal/chatapi/routes.go`, `internal/chatapi/handlers.go`, `internal/chatapi/handlers_test.go`
- `internal/boardapi/routes.go`, `internal/boardapi/dispatch.go`, `internal/boardapi/dispatch_test.go`
- `main.go` (startSyncIngest, registerBoard, registerChat)
