# feat(chatapi): relay projectId, surface the daemon's unknown-project 400, and proxy GET /api/v1/chat/projects

**Status**: 🔁 CONTINUATION 2026-10-12 — [console#387](https://github.com/qf-studio/pilot-console/issues/387) → PR#388 (+401/-8) held by autopilot: the console wire-contract gate wants a raw-body strings.Contains test for the new `projectId` field (spec gap, memory `console-wire-contract-gate-needs-raw-body-strings-contains-test`). Continuation [console#389](https://github.com/qf-studio/pilot-console/issues/389) (TASK-525) adds the two JSON tests on the PR branch. (leg 4 of TASK-518; repo qf-studio/pilot-console; labels `pilot` + `no-decompose`)
**Created**: 2026-10-12
**Repo**: qf-studio/pilot-console

## Context

The daemon's chat gateway (pilot PR #5642, merged 2026-10-11) added project selection to the operator chat wire. POST /api/v1/chat/messages now accepts an optional projectId (the daemon config project name); an unknown id answers 400 with the plain-text body "unknown project: <id>". The POST 202 body and the events 200 body now carry projectId for the conversation. A new GET /api/v1/chat/projects answers {"projects":[{"id","name","path","repo","default"}]} behind the same bearer token.

The console proxy does not relay any of this. `internal/chatapi/handlers.go` decodes the POST body into sendMessageRequest, which has no projectId, so the field is dropped before `internal/chat/client.go` builds the upstream request. mapGatewayError maps every non-404 upstream status to 502 "chat request failed", so a 400 from the daemon reaches the UI as a gateway failure. There is no projects route. The Gateway interface in `internal/chatapi/routes.go` has SendMessage and Events only.

This issue keeps the C14 idiom: the console holds no chat state and relays daemon bodies verbatim. The UI (pilot-console-ui) consumes the new field and route in the next issue.

## Implementation

In `internal/chat/client.go`:

- Add ProjectID string with JSON tag projectId, omitempty, to SendMessageRequest.
- Add Body string to StatusError: the upstream response body, trimmed, cut to 512 bytes. Set it in do when the status is outside 2xx. Error() keeps its current text.
- Add Projects(ctx, orgID string, inst fleet.Instance) (json.RawMessage, error) that calls do with GET and the path chat/projects and no body.

In `internal/chatapi/routes.go`:

- Add Projects to the Gateway interface with the same signature.
- Register GET /api/v1/chat/projects with authenticate only (no CSRF guard, it is a GET) pointing at a new handleProjects.

In `internal/chatapi/handlers.go`:

- Add ProjectID string with JSON tag projectId to sendMessageRequest and pass it into chat.SendMessageRequest. valid() is unchanged; an empty projectId is allowed.
- Add handleProjects: same disabled, principal, org (404 when none), instance (409 instance_not_running when not running) sequence as handleEvents, then h.gateway.Projects and writeRawJSON with status 200.
- Extend mapGatewayError: when the StatusError code is 400 and the body starts with "unknown project:", answer 400 with writeJSONErrorCode, message equal to the daemon body text, code unknown_project. Any other upstream 400 answers 400 with the message "chat request rejected" and code bad_request, without the upstream body. The existing 404 to 409 chat_not_enabled and the 502 fallback stay. The warn log line keeps org, conversation, status, daemon_status and error.

Tests, in `internal/chatapi/handlers_test.go` using the existing fakeOrgStore, fakeInstances, fakeGateway, fakeAuthenticate and newTestMux helpers (extend fakeGateway with a Projects method and a recorded last SendMessageRequest):

- TestHandleSendMessage_RelaysProjectID: a POST with projectId "console" reaches the fake gateway's SendMessageRequest with ProjectID "console".
- TestHandleSendMessage_UnknownProject400: the fake gateway returns a StatusError with Code 400 and Body "unknown project: nope"; the response is 400, code unknown_project, message "unknown project: nope".
- TestHandleSendMessage_OtherUpstream400DoesNotLeak: StatusError 400 with Body "invalid JSON body" answers 400, code bad_request, and the body does not contain "invalid JSON body".
- TestHandleProjects_Success: GET returns 200 and the fake gateway's raw JSON byte for byte (use a body with an unknown extra field to prove verbatim relay).
- TestHandleProjects_Unauthenticated401, TestHandleProjects_NoOrg404, TestHandleProjects_InstanceNotRunning409, TestHandleProjects_ChatDisabled409 (gateway StatusError 404 maps to 409 chat_not_enabled), TestHandleProjects_UpstreamFailure502, TestHandleProjects_Disabled503.

Tests in `internal/chat/client_test.go` using the existing httptest daemon pattern:

- TestProjectsSuccess: the client issues GET /api/v1/chat/projects with the bearer token and returns the body verbatim.
- TestSendMessageRelaysProjectID: the upstream request body contains "projectId":"console" when set and no projectId key when empty.
- TestStatusErrorCarriesBody: a 400 upstream with body "unknown project: x" yields a StatusError with Code 400 and Body "unknown project: x".

Do not change `internal/fleet/configrender.go` or anything outside internal/chat and internal/chatapi. Keep the diff under 400 changed lines.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go test ./internal/chatapi/ -count=1` passes; paste the output into the PR body.
- `go test ./internal/chat/ -count=1` passes; paste the output into the PR body.
- `go vet ./internal/chatapi/ ./internal/chat/` passes; paste the output into the PR body.
- drop ProjectID from the chat.SendMessageRequest built in handleSendMessage -> TestHandleSendMessage_RelaysProjectID fails
- map an upstream 400 to 502 as before -> TestHandleSendMessage_UnknownProject400 fails
- relay the upstream 400 body for every 400 -> TestHandleSendMessage_OtherUpstream400DoesNotLeak fails
- register the projects route without authenticate -> TestHandleProjects_Unauthenticated401 fails
- return the projects body through a re-encode instead of writeRawJSON -> TestHandleProjects_Success fails
- stop setting Body on StatusError in do -> TestStatusErrorCarriesBody fails
- The PR touches only files under internal/chat and internal/chatapi.

## Refs

- Pilot issue: https://github.com/qf-studio/pilot-console/issues/387
- Plan: TASK-518 in the pilot repo (.agent/tasks/TASK-518-side-chat-navigator-research-and-issue-filing.md), leg 4 of 5
- Daemon wire (merged): https://github.com/qf-studio/pilot/pull/5642 — the daemon files are pilot internal/gateway/chat.go and pilot internal/adapters/web/api.go (ProjectSummary)
- Daemon legs 1 and 2: https://github.com/qf-studio/pilot/pull/5633, https://github.com/qf-studio/pilot/pull/5637, https://github.com/qf-studio/pilot/pull/5639
- Console proxy today: `internal/chatapi/handlers.go`, `internal/chatapi/routes.go`, `internal/chat/client.go`
- Prior console chat legs: console PR#117 (TASK-464), console PR#385 and PR#386 (TASK-514)

**Last Updated**: 2026-10-12
