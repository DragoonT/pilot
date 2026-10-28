## Post-merge review — APPROVE with defects

Scope vs #244:
✓ `src/views/ChatView.vue` restyled: "Research" title (15px), question at 60% (`text-ds-text/60`), `SectionHeader` "Navigator research" with count in the action slot, one `ListRow` per sub-agent (id / title / meta = duration only / `Chip variant="done"`), report via markdown-it (`src/lib/reportMarkdown.ts`, `html:false`). Route `/chat` unchanged (`src/router/index.ts`).
✓ Composer: `ResearchComposer.vue` — placeholder `Ask your pilot…`, two `Pill` mode buttons (uppercase via the U1 Pill), Enter submits.
✓ Dashboard: composer mounted at the bottom of the main column in `DashboardView.vue`; `askPilot` pushes `{ name: 'chat', query: { q, mode } }`; ChatView consumes `?q&mode`, clears the query, starts the turn.
✓ Context column: `Read N docs · M memories` / `Created K memories`, `—` when no event carries the counts; no judge name / version.
✓ No `Create tickets` action.
✓ Unit tests: sub-agent rows with DONE chips and `12 m` meta from a fixture stream; markdown report (`h2`, `strong`); dashboard input navigates with the question in the query.
✓ Test asserts no `token` / `$` in the sub-agent tree.
✗ PR body: build/test/lint pasted (939 tests, CI green) but no line names the adapter, and the missing event fields are not listed in the body (only in the `ChatEvent` docblock as "ASSUMED wire contract").
Tests: 6 in `ChatView.spec.ts` + 1 in `DashboardView.spec.ts` = 7.

### D1 — Mobile Chat tab lost confirmation cards
`/chat` was the mobile chat surface (`MobileTabBar.vue` → `{ name: 'chat' }`) rendered by `ChatWindow`, which turns `confirmation` events into cards with the approve/decline callback (`taskId` / `messageRef`). The new ChatView renders only the run's last `text` event. On a phone an issue-draft confirmation is now unreachable (the Operator panel is desktop-only). Render `confirmation` events in ChatView (reuse ChatWindow's card) or keep `ChatWindow` on narrow viewports.

### D2 — Sub-agent tree and Context panel bind to events nothing emits
The daemon's web messenger (`internal/adapters/web/messenger.go`) emits only `text`, `confirmation`, `progress`, `result`; its `Event` struct has `taskId`, `phase`, `progress`, `prUrl`, `success`, `messageRef` — no `durationMs`, `docsRead`, `memoriesRead`, `memoriesCreated`, no `subagent` / `context` type. The console relays the body verbatim (`chatapi/handlers.go handleEvents`), and `mockAdapter` emits only `progress` / `confirmation` / `text`. On both adapters the tree never renders and Context shows `— / —`. The degrade is honest (as the spec allowed) but the PR body should have named the gap, and the daemon leg must be filed so the page is not a permanent placeholder.

### D3 — `mode` never leaves the console
`ChatMode` (`research` | `docs`) is new in this PR; there were no "existing chat modes" in the UI, the console, or the daemon. `httpAdapter.sendChatMessage` posts `mode`, but the console's `sendMessageRequest` (`chatapi/handlers.go`) has no `mode` field, so it is dropped before the daemon. The RESEARCH / DOCS pills are cosmetic today. Either forward `mode` through the console to a daemon that acts on it, or hide the pills until it exists.

### Notes (no action)
- N1 markdown-it with `html:false` plus a test that `<img onerror>` is escaped — good. `linkify` links have no `target` / `rel`; fine for same-tab.
- N2 Type sizes are literals (`text-[15px]`, `text-[13px]`) rather than `text-ds-row` / `text-ds-context`; consistent with U1's own primitives (`SectionHeader`, `Pill` use literals too), so not a drift from U1.
- N3 Context aside is `hidden lg:block`; below 1024px the panel disappears. Matches the 1440px design; no mobile mock.
- N4 `send()` option building (`Object.keys(options).length > 0 ? … : …`) keeps the old no-arg call shape for existing adapter tests. OK.

