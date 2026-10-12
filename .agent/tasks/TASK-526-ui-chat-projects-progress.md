# feat(chat): project selector, projectId on send, live progress line and typed events in the side chat

**Status**: 🚀 Dispatched to Pilot 2026-10-12 → [ui#223](https://github.com/qf-studio/pilot-console-ui/issues/223) (leg 5a of TASK-518; repo qf-studio/pilot-console-ui; labels `pilot` + `no-decompose`)
**Created**: 2026-10-12
**Repo**: qf-studio/pilot-console-ui

## Context

The daemon side chat is now a Navigator (pilot PR #5633, #5637, #5639, #5642): every web turn is a read-only agentic research turn that resumes the conversation, streams progress events while it reads the repo, and can draft a Pilot issue that the user confirms in chat. The console proxy relays the new wire (console PR #388): POST /api/v1/chat/messages accepts an optional projectId (the daemon project name) and answers 400 with code unknown_project for a bad id; the POST and events responses carry projectId; a new GET /api/v1/chat/projects returns {"projects":[{"id","name","path","repo","default"}]}.

The UI knows none of this. `src/lib/api/types.ts` ChatEvent has seq, type, text and occurredAt only, so taskId, messageRef, phase, progress, prUrl and success are dropped by toChatEvent in `src/lib/api/httpAdapter.ts`. `src/stores/chat.ts` turns every polled event into an assistant transcript line, so a progress event ("Read internal/comms/handler.go") would render as a chat reply. There is no project selector and no way to send projectId. The busy reply ("A turn is already running for this conversation. Wait for it to finish.") is a plain text event and renders fine today.

This issue adds the wire fields, the projects list, the selector and the progress line. The confirmation card (File / Discard) is the next issue; this issue must keep confirmation events in the transcript as plain text so nothing is lost before that lands.

## Implementation

Wire and adapters:

- In `src/lib/api/types.ts`: extend ChatEvent with optional taskId, messageRef, phase, progress (number), prUrl and success (boolean). Add ChatProject {id, name, path, repo, default: boolean} and ChatProjectsResult {projects: ChatProject[]}. Add projectId (optional string) to ChatEventsResult and ChatSendResult. Add ChatSendOptions {projectId?: string}. Change the ConsoleAdapter signature to sendChatMessage(conversationId, text, options?: ChatSendOptions) and add listChatProjects(): Promise<ChatProjectsResult>.
- In `src/lib/api/httpAdapter.ts`: extend WireChatEvent and toChatEvent with the six optional fields (pass through when present, omit when absent); map projectId on both responses; send projectId in the POST body only when options.projectId is set; implement listChatProjects against GET /api/v1/chat/projects through the same translateChatError path; translate a 400 whose body code is unknown_project into a ChatError with code unknown_project (extend the ChatError code union in `src/lib/api/errors.ts`).
- In `src/lib/api/mockAdapter.ts`: same signatures; listChatProjects returns two projects (the first default) and sendChatMessage records the projectId it was given; the mock reply stream emits one progress event ("Read README.md", taskId "chat-conv") before its text reply so the progress line is visible on the mock stack.
- Fixtures: add src/lib/api/__tests__/fixtures/chat-projects.json (plain name, new) with two projects, and extend `src/lib/api/__tests__/fixtures/chat-events.json` with one progress event carrying taskId and phase and one text event after it.

Store (`src/stores/chat.ts`):

- Add projects (ChatProject[]), selectedProjectId (string or null, persisted in localStorage under the key pilot.chat.projectId.<orgId>, defaulting to the project flagged default), projectsLoaded, and loadProjects() called from startPolling once per session; a ChatError or ApiError leaves projects empty without throwing.
- send() passes {projectId: selectedProjectId} when set. On a ChatError with code unknown_project: clear selectedProjectId, reload projects, and rethrow so the composer shows the inline error.
- Add progressLine (string or null). In poll(): events with type progress update progressLine and are not appended to messages; any event of another type clears progressLine and is appended as today. send() clears progressLine. reset() clears all new state.
- Keep confirmation events as transcript entries with their type preserved (the next issue renders them).

ChatWindow (`src/design-system/components/ChatWindow.vue`):

- Project selector in the header row, between the title and the collapse control: a native select bound to chat.selectedProjectId listing chat.projects by name; hidden when chat.projects has fewer than two entries; disabled while chat.isSending.
- Progress line: under the transcript, in place of the "Working on it" pulse row when chat.progressLine is set: the pulse dot plus the progress text in a mono span, single line, truncated with an ellipsis. When progressLine is null the existing pulse row behaviour stays.
- Composer placeholder while a turn is in flight stays as today.

Specs (vitest, Testing Library, same harness as the existing specs):

- `src/stores/__tests__/chat.spec.ts`: "send() passes the selected projectId to the adapter"; "send() omits projectId when none is selected"; "poll() routes progress events to progressLine and keeps them out of the transcript"; "a text event after progress clears progressLine"; "an unknown_project ChatError clears the selection and reloads projects"; "loadProjects defaults the selection to the project flagged default".
- `src/design-system/components/__tests__/ChatWindow.spec.ts`: "renders the project selector when two projects are loaded and hides it with one"; "changing the selector updates chat.selectedProjectId"; "renders the progress line instead of the pulse row when progressLine is set".
- `src/lib/api/__tests__/httpAdapter.spec.ts`: "listChatProjects maps the projects fixture"; "sendChatMessage sends projectId only when provided"; "toChatEvent keeps taskId, messageRef, phase and progress".

Do not touch ChatPanel.vue, ChatOverlay.vue or the approvals surfaces. Keep the diff under 500 changed lines.

## Acceptance

- `make build` passes; paste the output into the PR body.
- `make test` passes; paste the output into the PR body.
- `make lint` passes; paste the output into the PR body.
- drop projectId from the POST body in sendChatMessage -> the spec named "sendChatMessage sends projectId only when provided" fails
- append progress events to messages in poll() -> the spec named "poll() routes progress events to progressLine and keeps them out of the transcript" fails
- render the selector regardless of the project count -> the spec named "renders the project selector when two projects are loaded and hides it with one" fails
- keep the selection on an unknown_project error -> the spec named "an unknown_project ChatError clears the selection and reloads projects" fails
- The mock adapter and the http adapter expose identical ConsoleAdapter signatures (vue-tsc passes under make lint).

## Refs

- Pilot issue: https://github.com/qf-studio/pilot-console-ui/issues/223
- Plan: TASK-518 in the pilot repo (.agent/tasks/TASK-518-side-chat-navigator-research-and-issue-filing.md), leg 5a of 5
- Daemon wire: https://github.com/qf-studio/pilot/pull/5642 (projectId, projects route) and https://github.com/qf-studio/pilot/pull/5637 (progress and confirmation events; busy text)
- Console relay: https://github.com/qf-studio/pilot-console/pull/388
- UI today: `src/stores/chat.ts`, `src/design-system/components/ChatWindow.vue`, `src/lib/api/httpAdapter.ts`, `src/lib/api/mockAdapter.ts`, `src/lib/api/types.ts`, `src/lib/api/errors.ts`
- Prior UI chat legs: ui PR#109 (TASK-466 docs), ui PR#222 (TASK-514 cursor reset + inline send error)

**Last Updated**: 2026-10-12
