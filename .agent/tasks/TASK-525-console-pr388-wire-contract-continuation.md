# fix(chatapi): continue PR #388 — add the raw-body wire-contract test for the projectId field

**Status**: ✅ DONE 2026-10-12 — [console#389](https://github.com/qf-studio/pilot-console/issues/389) pushed 17ad4dd33 to pilot/GH-387; all five checks on PR#388 green (wire gate passes). Issue still open with pilot-in-progress (hand-close after the PR merges). (CI-fix continuation of console#387 / PR#388; repo qf-studio/pilot-console; labels `pilot` + `autopilot-fix` + `no-decompose`)
**Created**: 2026-10-12
**Repo**: qf-studio/pilot-console

## Context

PR #388 (branch pilot/GH-387, issue #387) relays projectId through the chat proxy and adds the projects route. The test and lint jobs pass. The job "Check Wire-Contract Tests" fails:

```
CI CHECK FAILED: handler/DTO struct change missing a raw-body
wire-contract test
internal/chatapi/handlers.go (fields: projectId )
```

The gate in `scripts/check-wire-contract-tests.sh` requires that, when a json-tagged field is added to a handler or DTO struct, a test in the same package captures the raw response body with Body.String() and asserts on it with strings.Contains naming the field, inside one test function. The new tests in PR #388 assert through the fake gateway's recorded request and a bytes comparison, which the gate does not count. Autopilot held the PR because it could not classify the failure. Work on the existing branch pilot/GH-387 and push to PR #388; do not open a new PR.

## Implementation

One change on branch pilot/GH-387, in `internal/chatapi/handlers_test.go`:

- Add TestHandleSendMessage_ProjectIDJSON. Script the fake gateway so SendMessage returns the raw JSON {"conversationId":"c1","seq":7,"projectId":"console"}. POST a body with conversationId c1, text hi and projectId console through newTestMux with a running instance. Read rec.Body.String() into a variable, then assert with strings.Contains that the raw body contains the exact substring "projectId":"console" and that the recorded chat.SendMessageRequest has ProjectID console. Assert the status is 202.
- Add TestHandleProjects_ProjectIDJSON. Script the fake gateway's Projects to return {"projects":[{"id":"console","name":"console","path":"/var/lib/pilot/repos/console","repo":"qf-studio/pilot-console","default":true}]}. GET /api/v1/chat/projects, read rec.Body.String(), and assert with strings.Contains that it contains "id":"console" and "default":true.

Run the gate locally with make check-wire-contract-tests before pushing; it diffs the working tree against origin/main. Touch only that one test file. Keep the diff under 80 changed lines.

## Acceptance

- `make check-wire-contract-tests` passes; paste the output into the PR body.
- `go test ./internal/chatapi/ -count=1` passes; paste the output into the PR body.
- `go vet ./internal/chatapi/` passes; paste the output into the PR body.
- make the fake gateway return a body without the projectId key -> TestHandleSendMessage_ProjectIDJSON fails
- make the fake gateway's Projects return an empty list -> TestHandleProjects_ProjectIDJSON fails
- The commits land on branch pilot/GH-387, every check on PR #388 is green, and no new PR is opened.

## Refs

- Pilot issue: https://github.com/qf-studio/pilot-console/issues/389
- Source issue: https://github.com/qf-studio/pilot-console/issues/387 (TASK-524, leg 4 of TASK-518)
- PR under repair: https://github.com/qf-studio/pilot-console/pull/388
- Failing run: https://github.com/qf-studio/pilot-console/actions/runs/38218936643/job/114710224086
- Gate: `scripts/check-wire-contract-tests.sh`; canonical example TestHandleListAppliedSpecVersionJSON in `internal/instances/handlers_test.go`

**Last Updated**: 2026-10-12

<!-- autopilot-meta branch:pilot/GH-387 pr:388 iteration:1 source:387 sha:8e4ea548b499b55d2ed3f260dbea1ecc9aad2a95 -->
