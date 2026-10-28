# TASK-615: TestChatAPI_Composed returns while the runner still writes into its TempDir — flaky "directory not empty" that closed PR#5921

**Status**: 🚀 DISPATCHED 2026-10-28 → pilot#5923 (`pilot`+`no-decompose`). The flake cost one autopilot cycle today (PR#5921 closed, vague fix issue #5922 declined at pre-flight, hand recovery). Same test failed on main on 2026-10-26 19:34Z.
**Spec refs**: `internal/gateway/chat_test.go` TestChatAPI_Composed (~line 476); CI run 40732926612 (job test, "TempDir RemoveAll cleanup: unlinkat /tmp/TestChatAPI_Composed…: directory not empty").
**Origin**: queue check 2026-10-28 17:18Z.

## Why
- The test builds a real executor Runner over a fake backend, starts the gateway in a goroutine, sleeps 100 ms, posts a question and reads events, then returns. The question is executed by the Runner in the background against projectDir = t.TempDir(). The Runner keeps writing there (recordings, task files, Navigator copy-back) after the test function returns, so testing's TempDir cleanup races it and fails the package.
- A flake in one package fails the whole `test` job; autopilot classifies it as code, closes the PR and files a fix issue the pre-flight judge declines as vague. Each occurrence costs ~45 minutes of hand recovery.

## Legs — pilot (daemon)

### LEG F1 — repo: qf-studio/pilot — title: test(gateway): TestChatAPI_Composed waits for the background task to finish before the TempDir cleanup runs
probe: present qf-studio/pilot func TestChatAPI_Composed\(
probe: present qf-studio/pilot NewRunnerWithBackend\(

## Context

TestChatAPI_Composed in `internal/gateway/chat_test.go` creates a Runner with NewRunnerWithBackend over a fake chat backend, starts the gateway server in a goroutine, sleeps 100 ms, posts a question and asserts on the events it reads back. The question's task runs on the Runner in the background with projectDir set to t.TempDir(). The test returns while that task still runs, so the Runner keeps writing into the directory (recordings, task bookkeeping, Navigator copy-back) and the testing package's TempDir cleanup fails with "TempDir RemoveAll cleanup: unlinkat … directory not empty". It failed CI on PR#5921 (2026-10-28) and on main (2026-10-26). The failure is in cleanup, not in the assertions, so it looks like a product failure to autopilot, which closed the PR and filed a fix issue.

## Implementation

1. Make the test own the task's lifetime: have the fake backend signal completion (a channel closed when Execute returns), and after the assertions wait on that signal with a bounded timeout before returning; also cancel the server context and wait for Start to return via a done channel instead of leaving the goroutine to the process. Register these waits with t.Cleanup so they run before TempDir's cleanup (cleanups run last-in-first-out, so register after t.TempDir()).
2. Replace the 100 ms sleep with a readiness wait on the server's listener (poll the health route or use a ready channel if the server exposes one), bounded by the test context.
3. Apply the same pattern to any sibling test in the file that starts the server and runs a task against a TempDir (grep for NewRunnerWithBackend in the gateway tests).
4. Run the test with -count=20 under -race locally and paste the output.

## Acceptance

- `go test -race ./internal/gateway/ -run TestChatAPI_Composed -count=20` passes; paste the output into the PR body.
- `go test -race ./internal/gateway/ -run TestChatAPI_Composed_RunnerDoneBeforeCleanup` passes; paste the output into the PR body.
- remove the wait on the backend's done channel -> TestChatAPI_Composed_RunnerDoneBeforeCleanup fails

## Out of scope

- Autopilot's CI-failure classifier (a flake still reads as code; separate task).
- The chat API behaviour under test.

## Refs

- https://github.com/qf-studio/pilot/pull/5921
- https://github.com/qf-studio/pilot/issues/5922

## Refs

- F1 → https://github.com/qf-studio/pilot/issues/5923
