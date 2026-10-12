# feat(chat): render the pilot-issue confirmation card with File / Discard, send callbacks, and autolink URLs in replies

**Status**: 🚀 Dispatched to Pilot 2026-10-12 → [ui#224](https://github.com/qf-studio/pilot-console-ui/issues/224), blocked by ui#223 (leg 5b of TASK-518; repo qf-studio/pilot-console-ui; labels `pilot` + `no-decompose`)
**Created**: 2026-10-12
**Repo**: qf-studio/pilot-console-ui

Blocked by: #223

## Context

When the user asks the side chat to file an issue, the daemon (pilot PR #5637) answers with a confirmation event: type confirmation, text "File Pilot issue: <title>" followed by a blank line, up to 400 characters of the drafted body and optionally " (<project>)", taskId "issue-" plus eight hex characters, messageRef equal to taskId. Nothing is filed until the client posts a callback to POST /api/v1/chat/messages with isCallback true, callbackId equal to the taskId and actionId file (or discard). The daemon then answers with a text event "Filed https://github.com/<owner>/<repo>/issues/<n>" or "Issue draft discarded." Task-style confirmations (taskId without the issue- prefix) take actionId execute or cancel.

After the previous issue the UI keeps confirmation events in the transcript as plain text, the adapter has no callback method, and assistant text renders URLs as plain text. This issue renders the card, sends the callbacks, and autolinks URLs.

## Implementation

Adapter:

- In `src/lib/api/types.ts` add sendChatCallback(conversationId, callbackId, actionId): Promise<ChatSendResult> to ConsoleAdapter. Implement it in `src/lib/api/httpAdapter.ts` (POST with isCallback true, callbackId, actionId, and projectId when a project is selected is NOT needed here; callbacks carry no projectId) through translateChatError, and in `src/lib/api/mockAdapter.ts` (actionId file queues a text event "Filed https://github.com/qf-studio/pilot/issues/1"; discard queues "Issue draft discarded.").

Store (`src/stores/chat.ts`):

- Add decideCard(callbackId, actionId): sets a per-card pending flag (cardPending map keyed by callbackId), calls sendChatCallback, advances the cursor like send(), and clears the flag when the next non-progress event arrives or on error (rethrow for the inline error).
- ChatMessage gains optional taskId and messageRef copied from the event so the component can key the card.

ChatWindow (`src/design-system/components/ChatWindow.vue`):

- Render an assistant message whose type is confirmation as a card instead of a text line: a bordered panel with the first line of text as the title (strip the "File Pilot issue: " prefix into a small "Pilot issue" label above the title), the remainder as a collapsed preview (max four lines, "Show more" toggles the full text), and two buttons. When taskId starts with issue-: File (actionId file) and Discard (actionId discard). Otherwise: Execute (actionId execute) and Cancel (actionId cancel). Buttons disable and the card shows "Sending…" while cardPending is set for that callbackId; after the decision resolves the buttons stay disabled and the card shows "Decided" so a card cannot be sent twice from this transcript.
- Autolink: extend parseSegments so https URLs in assistant text render as anchors (target blank, rel noopener) with the URL as the label; keep the bold lead-in behaviour. User bubbles stay plain.

Specs:

- `src/design-system/components/__tests__/ChatWindow.spec.ts`: "renders a confirmation event as a card with File and Discard for an issue- taskId"; "renders Execute and Cancel for a non-issue taskId"; "clicking File calls chat.decideCard with the taskId and actionId file"; "the card disables its buttons while pending and after a decision"; "autolinks https URLs in assistant text and not in user bubbles".
- `src/stores/__tests__/chat.spec.ts`: "decideCard posts the callback and advances the cursor from the returned seq"; "decideCard clears the pending flag when the next text event arrives"; "decideCard rethrows on failure and clears the pending flag".

Do not change ChatPanel.vue, ChatOverlay.vue or approvals. Keep the diff under 450 changed lines.

## Acceptance

- `make build` passes; paste the output into the PR body.
- `make test` passes; paste the output into the PR body.
- `make lint` passes; paste the output into the PR body.
- send actionId execute instead of file for an issue- card -> the spec named "clicking File calls chat.decideCard with the taskId and actionId file" fails
- render confirmation events as plain text -> the spec named "renders a confirmation event as a card with File and Discard for an issue- taskId" fails
- keep the buttons enabled after a decision -> the spec named "the card disables its buttons while pending and after a decision" fails
- post the callback without isCallback true -> the spec named "decideCard posts the callback and advances the cursor from the returned seq" fails
- Manual check on the mock stack: ask "file an issue", the card renders, File turns it into "Filed https://github.com/qf-studio/pilot/issues/1" with a clickable link.

## Refs

- Pilot issue: https://github.com/qf-studio/pilot-console-ui/issues/224
- Plan: TASK-518 in the pilot repo (.agent/tasks/TASK-518-side-chat-navigator-research-and-issue-filing.md), leg 5b of 5
- Daemon card contract: https://github.com/qf-studio/pilot/pull/5637 (presentIssueCard and handleIssueCardDecision in pilot internal/comms/chat_turn_handler.go)
- Callback shape: pilot internal/adapters/web/api.go DispatchRequest (isCallback, callbackId, actionId); approvals never route through chat (actionId approve and reject are rejected with 400)
- UI today: `src/stores/chat.ts`, `src/design-system/components/ChatWindow.vue`, `src/lib/api/httpAdapter.ts`, `src/lib/api/mockAdapter.ts`, `src/lib/api/types.ts`

**Last Updated**: 2026-10-12
