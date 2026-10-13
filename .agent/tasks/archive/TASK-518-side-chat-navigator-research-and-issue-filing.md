# TASK-518: Side chat as a Navigator — agentic research turns + Pilot issue filing

**Status**: ✅ Legs 1 + 2a + 2b MERGED + REVIEWED (2a PR#5637 11:22Z, 2b PR#5639 11:50Z, both APPROVE-w-notes, all pins kill). **Leg 3 MERGED + REVIEWED 2026-10-11 → [#5640](https://github.com/qf-studio/pilot/issues/5640) → PR#5642 (7/7 pins kill; not in v2.280.0, next train). DAEMON SIDE COMPLETE (legs 1–3). **Leg 4 DISPATCHED 2026-10-12 → [console#387](https://github.com/qf-studio/pilot-console/issues/387) (TASK-524: relay `projectId`, unknown-project 400 → `unknown_project`, proxy `GET /api/v1/chat/projects`). PR#388 held by the console wire-contract gate → continuation [console#389](https://github.com/qf-studio/pilot-console/issues/389) (TASK-525). **Leg 5 MERGED + REVIEWED 2026-10-12: 5a [ui#223](https://github.com/qf-studio/pilot-console-ui/issues/223) → PR#225, 5b [ui#224](https://github.com/qf-studio/pilot-console-ui/issues/224) → PR#226, both APPROVE-w-notes, 8/8 pins kill. Leg 4 PR#388 reviewed APPROVE, hand-merged 09:47Z (c8d1b02ec).** ALL FIVE LEGS MERGED. Remaining: next daemon train carries leg 3 to tenants → founder prod smoke → archive. Product gap found on the way, FILED 2026-10-12: [#5643](https://github.com/qf-studio/pilot/issues/5643) (TASK-528, redrive any held PR on a new head) → [#5644](https://github.com/qf-studio/pilot/issues/5644) (TASK-529, rehydrate held PRs after restart). (project selector, progress line, confirmation card File/Discard, busy text).** Wire contract for legs 4/5: `projectId` = config project name (ProjectSummary.ID); projects route returns {projects:[{id,name,path,repo,default}]}; unknown id → 400 "unknown project: <id>". Leg 1 history: MERGED + REVIEWED 2026-10-09 — [#5632](https://github.com/qf-studio/pilot/issues/5632) → PR#5633 (c818cfa21), APPROVE-w-notes (6/6 pins kill, 13/13 tests). Founder confirmed all 3 defaults ("go"). **Leg 2 DISPATCHED 2026-10-11 as two issues: 2a [#5635](https://github.com/qf-studio/pilot/issues/5635) (TASK-520, comms handler path + card + callback) → 2b [#5636](https://github.com/qf-studio/pilot/issues/5636) (TASK-521, per-project IssueCreator wiring, blocked by #5635).** Finding 10-11: the console UI renders neither `confirmation` nor `progress` chat events and never posts callbacks, so leg 5 must add all three. Leg 2 must detect a session reset by `result.SessionID != turn.ResumeSessionID` (the Claude Code backend retries internally, so `SessionReset` never fires there).
**Created**: 2026-10-09
**Assignee**: Navigator (plan, review) · Pilot (legs 1–5) · founder (decisions, prod smoke)

---

## Context

**Problem**: The console side chat (TASK-463/464/469/514) works on prod since 2026-10-09, but it is the Slack-parity comms brain, not a Navigator. Research 2026-10-09 (navigator-research agent, 7-section map) found:

1. Read-only intents (question / research / chat) run `runner.Execute` with `LocalMode: true`, which builds the **bench prompt** (`internal/executor/prompt_builder.go:145,495`: "Phase 2: IMPLEMENT", "write code NOW", "never spend more than 2 tool calls reading") plus the executor header "do not ask to create a GitHub issue … implement directly" (`:38`). The persona contradicts the intent. No Navigator context, no memories.
2. Read-only is **prose only**. The session runs with `--dangerously-skip-permissions`, the full toolbox, in the shared project root (no worktree because `Branch == ""`). A chat turn can edit files.
3. The web `HandlerDeps` (`cmd/pilot/main.go:2785-2799`, `internal/pilot/pilot.go:828-849`) carries **no `IssueCreator`, no `Bot`, no `Classifier`**. `handleIssueIntake` (`internal/comms/issue_intake.go:103`) always answers "requires the bot module" / "requires GitHub". `commsIssueCreator` (`main.go:2914-2935`) is built only for the Telegram/Slack block.
4. Intent routing is regex (`intent.DetectIntent`); "research X, then file an issue" cannot be expressed. Each turn is a fresh `claude` process; no `--resume` (the backend supports `ResumeSessionID`, `backend.go:60`, but the chat never sets it). Conversation history is only the 500-char `convStore` used by the (absent) classifier.
5. No project selection on the wire: `chatMessageRequest` has no `projectId`; the active project is `/switch` text or `Projects[0]`. `issueCreator.resolveRepo` falls back to `repos[0]`.
6. Output arrives as one `SendChunked` after the run; the stream-json tool events are parsed by the runner but never reach the `WebMessenger`, so the user sees nothing for up to 3 min.
7. Navigator plugin files are **not available on tenant boxes** (`FindTemplatesPath` looks in `~/.claude/plugins/cache/navigator-marketplace`, `internal/executor/navigator.go:73`; the AMI does not install it). Anything "Navigator-like" must live in the daemon prompt, not in plugin skills/agents.

**Goal**: One chat turn = one agentic, read-only Claude Code session that behaves like `navigator-research` (Phase 0 `.agent/` + knowledge graph first, sampled reads, `file:line` citations) and, on request, authors a Pilot issue to the nav-pilot / onboarding-SOP contract, which the daemon files **after the user confirms in the chat**. Conversation context persists across turns via Claude session resume. Progress is visible while the turn runs.

**Platform scope**: `Platform == "web"` only. Telegram/Slack/Discord keep the current comms brain.

---

## Known Pitfalls & Patterns

- **PITFALL** (85%, `localmode-tasks-never-get-worktree-qdocs-in-root`): LocalMode/Q&A tasks run in the shared root and `CreateTaskDoc` writes untracked `q-<epoch>.md` into `<root>/.agent/tasks/`. → Leg 1 chat turns bypass `Execute`'s task-doc side effect entirely (new entry point, no `Task`), and the read-only allowlist makes the side effect impossible anyway.
- **PITFALL** (100%, mem-004): the Navigator integration in the executor prompt is the core value; `BuildPrompt()` must keep its "Start my Navigator session" prefix. → Leg 1 adds a **separate** `chat_prompt.go`; it does not touch `BuildPrompt`/`buildLocalModePrompt`. The chat prompt embeds the navigator-research method verbatim (Phase 0 → sample → cite) because the plugin is absent on tenants.
- **PATTERN** (100%, mem-038): bot dual-path — Responder for fast intents, executor for research/planning; Responder nil → executor path identical to before. → Web platform routes every non-command turn to the agentic path; the dual-path stays untouched for other platforms.
- **PITFALL** (95%, `base-presence-gate-false-positives-hold-then-silent-needs-human`): any backticked `x/y.ext` token in an issue body must exist on main or the dispatch gate holds 5 min then goes silent. → The issue-authoring contract in the chat prompt says: files to create are named in plain text, never backticked; only existing files may be backticked. Acceptance bullet pins this with a fixture.
- **PITFALL** (95%, `auto-preserved-wip-recover-by-cherry-pick-continuation`): size one-PR specs ~500 changed lines for the 1 h completion budget. → The issue contract tells the model to split work > ~500 lines into sequenced issues with `Blocked by: #N`.
- **PITFALL** (95%, `backend-timeout-finalization-on-expired-ctx-discards-committed-work`): backend timeout on an expired ctx discards work. → Chat turns are read-only, so nothing is lost; the turn timeout is 5 min and the final text is emitted even on `MaxTurns` cut-off (the backend returns the partial result).
- **PATTERN** (TASK-464/469, C14 idiom): the console proxies `POST /messages` and `GET /events` byte-faithfully and holds no chat state. → Leg 3 adds fields to the daemon wire first; leg 4 relays them verbatim; the UI (leg 5) is the only consumer.
- **LEARNING** (`file-pilot-issues-via-nav-pilot-skill-only`, recurrence 2): Pilot issues are filed by nav-pilot from a task doc, never by raw `gh issue create`. → This task's legs are dispatched via nav-pilot. The chat's own filing path goes through `github.CreatePilotIssue` (same title regex and repo allowlist Pilot already enforces).

---

## Acceptance Criteria

- [ ] A web chat turn runs `claude` with an **explicit read-only allowlist** (`Read, Grep, Glob, LS, Task, Bash(git log:*), Bash(git show:*), Bash(git diff:*), Bash(git blame:*), Bash(git ls-files:*), Bash(rg:*), Bash(ls:*)`), never with the executor's global `allowed_tools`; a test asserts the `--allowedTools` argv for a chat turn and asserts `Edit`/`Write`/`Bash(*)` are absent.
- [ ] The chat system prompt contains the Navigator research method (read `.agent/DEVELOPMENT-README.md` first if present; grep `.agent/knowledge/graph.json` and `.agent/knowledge/memories/` for the topic; sample, do not read everything; cite `path:line`) and contains neither "Phase 2: IMPLEMENT" nor "do not ask to create a GitHub issue"; a test pins all three strings.
- [ ] Second and later turns in one conversation pass `--resume <sessionId>` captured from the first turn's `init` event; on `ErrorTypeSessionNotFound` the turn retries without resume and the stored id is cleared; a test covers both.
- [ ] While a turn runs, the conversation's event stream receives `progress` events of the form `Reading internal/comms/handler.go` / `Grep "IssueCreator"` within 2 s of the tool call (one per tool-use event, deduplicated, max 1 per 500 ms).
- [ ] When the user asks to file / create / dispatch an issue, the final assistant text ends with one fenced block:
  ````
  ```pilot-issue
  title: feat(chat): …            # conventional-commit, CreatePilotIssue regex
  labels: [pilot]
  body: |
    ## Context … ## Scope … ## Acceptance Criteria … ## Out of scope … ## Refs
  ```
  ````
  The daemon strips the block from the text, emits a `confirmation` event (title + body preview, actions `file` / `discard`); nothing is filed before the `file` callback.
- [ ] On the `file` callback the daemon calls `IssueCreator.CreateIssue` for the **conversation's active project repo** with label `pilot`, posts the issue URL as a `text` event, and the issue body carries `Filed from Pilot Console chat <conversationId>` under `## Refs`. On `discard` nothing is created. A test covers both callbacks and a malformed block (→ `text` error, no `confirmation`).
- [ ] The web `HandlerDeps` receives an `IssueCreator` in **both** construction sites (polling `cmd/pilot/main.go` and gateway `internal/pilot/pilot.go`); a tenant with `adapters.github` configured can file from chat; a tenant without it gets a `text` event "GitHub is not configured for this project" instead of a silent no-op.
- [ ] `POST /api/v1/chat/messages` accepts optional `projectId`; the daemon sets the conversation's active project (and resets the resume session id); `GET /api/v1/chat/projects` lists `{id, name, path, repo}` for the tenant; unknown `projectId` → 400 with a typed error code.
- [ ] Console proxy relays `projectId` and the new `projects` route byte-faithfully (org-scoped, C14 idiom); UI shows a project selector when > 1 project, renders `progress` events as a single live line, and renders the `pilot-issue` confirmation card with File / Discard.
- [ ] A chat turn never creates `q-<epoch>.md` in `.agent/tasks/` and never records a task-doc side effect; a test runs a chat turn against a temp project and asserts the tree is unchanged.
- [ ] Prod smoke (founder): on a tenant, ask "how does the chat adapter enable its routes?" → answer cites `internal/gateway/server.go` lines; then "file a pilot issue to log the cause on 502" → card → File → issue URL opens, labeled `pilot`, picked up by the daemon.

---

## Implementation

### Leg 1 — `pilot`: chat-turn execution mode (runner + backend + prompt)
**Goal**: a dedicated, read-only, resumable execution entry point with progress forwarding.

**Tasks**:
- [ ] Add `ChatTurn{ConversationID, ProjectPath, Text, ResumeSessionID, MaxTurns, Timeout}` and `ChatTurnResult{Text, SessionID, Partial bool, ToolCalls int}` in a new file internal/executor/chat_turn.go (plain text name: file does not exist on main).
- [ ] `Runner.ExecuteChatTurn(ctx, ChatTurn, onProgress func(string))` → `backend.Execute(ExecuteOptions{Prompt, ProjectPath, ResumeSessionID, AllowedTools: ChatReadOnlyTools, MaxTurns, Model from config})`. Does **not** build a `Task`, does not call `Begin`/lifecycle, does not create a task doc, does not touch worktrees. Forwards each tool-use stream event to `onProgress` as `<Tool> <first arg>`; rate-limited.
- [ ] `ChatReadOnlyTools` constant (list in Acceptance). Per-call override only; `executionToolOptions()` untouched.
- [ ] New file internal/executor/chat_prompt.go: `BuildChatPrompt(projectPath, userText, hasNavigator bool)` — persona = Navigator research assistant; Phase 0 instructions; sampling + `path:line` citations; read-only statement; the **issue-authoring contract** (block format above, conventional-commit title, H2 sections Context / Scope / Acceptance Criteria / Out of scope / Refs, plain-text names for files to create, ≤ ~500 changed lines per issue, `Blocked by: #N` for sequences, each acceptance bullet names a test). On resumed turns only the user text is sent (the persona lives in the session).
- [ ] Session-not-found fallback already exists (`backend_claudecode.go:516-526`); surface `Partial` when `MaxTurns` ends the turn.
- [ ] Tests: argv allowlist pin; prompt string pins (3 strings); resume/no-resume; progress callback receives tool events; temp-project tree unchanged.

**Files**:
- `internal/executor/backend.go` — reuse `ExecuteOptions` (no change expected)
- `internal/executor/backend_claudecode.go` — tool-use event → progress hook (small)
- `internal/executor/runner.go` — `ExecuteChatTurn` (new method; keep out of `Execute`)
- `internal/executor/prompt_builder.go` — untouched (mem-004)

### Leg 2 — `pilot`: web handler agentic path + confirmed issue filing
**Goal**: every non-command web turn goes through `ExecuteChatTurn`; the `pilot-issue` block becomes a confirmation card; `file` callback creates the issue.

**Tasks**:
- [ ] In `comms.Handler.HandleMessage`: when `Platform == "web"` and the text is not a `/command`, call `handleChatTurn` instead of `detectIntent`. Other platforms unchanged.
- [ ] Per-conversation state on the handler: `sessionID` (resume), cleared on session-not-found and on project switch.
- [ ] Progress: `onProgress` → `WebMessenger` `progress` event (`internal/adapters/web/messenger.go`).
- [ ] Parse the trailing `pilot-issue` fenced block (YAML: `title`, `labels`, `body`); validate the title with the `CreatePilotIssue` regex; emit `confirmation` with actions `file` / `discard`; store the draft keyed by `callbackId` with a 30 min TTL.
- [ ] Callback `file` → `IssueCreator.CreateIssue(repo of active project, title, body + Refs line, labels ∪ {pilot})` → `text` event with URL. `discard` → `text` "Discarded". Missing creator → `text` "GitHub is not configured for this project".
- [ ] Wire `IssueCreator` into `HandlerDeps` at both construction sites; build it from the project's `adapters.github` the same way `commsIssueCreator` is built at `cmd/pilot/main.go:2914-2935` (extract a shared constructor; do not duplicate).
- [ ] Tests: web turn bypasses intent regex; block parse + confirmation event; `file`/`discard`/malformed; both wiring sites construct a creator when GitHub is configured.

**Files**:
- `internal/comms/handler.go` — routing + per-conversation session map
- `internal/comms/factory.go` — `HandlerDeps.IssueCreator`
- `internal/comms/issue_intake.go` — reuse `IssueDraft`; add block parser
- `internal/adapters/web/messenger.go` — progress emit (type exists at `:35`)
- `cmd/pilot/main.go`, `internal/pilot/pilot.go` — wiring

### Leg 3 — `pilot`: project selection on the chat wire
**Goal**: the console can target a project without `/switch` text.

**Tasks**:
- [ ] `chatMessageRequest.projectId` (optional) → `SetActiveProject` for the conversation; unknown id → 400 `unknown_project`.
- [ ] `GET /api/v1/chat/projects` → `[{id, name, path, repo}]` from `config.NewProjectSource`.
- [ ] Events carry `projectId` so the UI can show which project answered.
- [ ] Tests for both routes; contract section added to the chat API doc that TASK-463 produced.

**Files**: `internal/gateway/chat.go`, `internal/adapters/web/api.go`, `internal/comms/handler.go:901-924`.

### Leg 4 — `pilot-console`: proxy relay
**Goal**: C14 idiom — relay `projectId` and the `projects` route verbatim, org-scoped. Logs status + cause on upstream errors (console PR#386 pattern).

### Leg 5 — `pilot-console-ui`: project selector, live progress line, issue card
**Goal**: project `<select>` (hidden when 1 project); one live `progress` line under the composer that replaces itself; `confirmation` event rendered as a card with the issue title, a collapsed body preview, **File** / **Discard** buttons posting the existing callback shape (`isCallback`, `callbackId`, `actionId`); issue URL rendered as a link. Vitest specs for each.

**Sequence**: 1 → 2 → 3 (pilot, in order; 2 blocked by 1, 3 by 2) · 4 blocked by 3 · 5 blocked by 4. Release: legs 1–3 ride the daily train; the tenant daemons pick them up on the next AMI/self-upgrade.

---

## Out of Scope

- Telegram / Slack / Discord behaviour (keep the comms brain and the Responder dual-path).
- Installing the Navigator plugin on tenant AMIs (the method is embedded in the prompt; revisit if skills/hooks are wanted later).
- Write-capable chat turns ("fix it from chat"). Filing a Pilot issue is the write path.
- An MCP tool server for issue filing (considered; see decisions). Can replace the fenced-block contract later without a wire change.
- Persisting conversations across daemon restarts (in-memory buffer stays; the resume id is best-effort).
- Approvals in chat (stay on `/api/v1/approvals/{id}/decision`).

---

## Technical Decisions

| Decision | Options Considered | Chosen | Reasoning |
|----------|-------------------|--------|-----------|
| Turn model | (a) keep regex intent switch + fix prompts; (b) one agentic read-only session per turn | **(b)** | "Research, then file" needs a tool loop, not a classifier. The backend already supports allowlist + resume per call. |
| Read-only enforcement | prose; read-only worktree; `--allowedTools` allowlist | **allowlist** (shared root) | Enforced by Claude Code, zero FS cost, no worktree churn. Root is free because tickets use worktrees. |
| Issue filing path | model runs `gh issue create`; daemon MCP tool; fenced block + daemon confirm | **fenced block + confirm** | Keeps the confirm gate and credentials in the daemon; reuses `CreatePilotIssue` validation; no `gh` creds in the chat session; same approval idiom as Telegram intake. |
| Navigator method on tenants | depend on plugin in `~/.claude`; embed method in prompt | **embed** | Plugin is not on tenant AMIs; a prompt is versioned with the daemon. |
| Conversation memory | replay history in prompt; `--resume` | **`--resume`** with history-free fallback | Backend already captures `SessionID` (`backend_claudecode.go:1033`); fallback on eviction exists. |
| Project targeting | `/switch` text only; `projectId` on the wire | **both** | UI needs a selector; `/switch` stays for parity. |

---

## Verify

```bash
go build ./... && go test ./internal/executor/ ./internal/comms/ ./internal/adapters/web/ ./internal/gateway/ -run 'Chat|ChatTurn|PilotIssue' -count=1
# prod smoke: see last acceptance bullet (founder, tenant console)
```

---

## Done

- [ ] Legs 1–3 merged on pilot, reviewed post-merge, on a train release.
- [ ] Leg 4 merged on console (prod-0.1.x), leg 5 merged on console-ui (auto deploy).
- [ ] Prod smoke bullet passes on one tenant; the filed issue is picked up by the tenant daemon.
- [ ] This doc archived; `.agent/system/` chat architecture note updated (one paragraph: agentic turn, allowlist, block contract).

---

## Refs

- Research: navigator-research agent 2026-10-09 (daemon map; in-session).
- Prior: TASK-463 (gateway chat API), TASK-464 (console proxy), TASK-469 (latestSeq), TASK-514 (chat enablement).
- Contracts: `internal/adapters/github/issue_create.go` (`CreatePilotIssue`), `.agent/sops/onboarding/new-project-issue-authoring.md` (issue body shape).
- Pilot issues: leg 1 → [#5632](https://github.com/qf-studio/pilot/issues/5632) → PR#5633 merged + reviewed (TASK-519) · leg 2a → [#5635](https://github.com/qf-studio/pilot/issues/5635) → PR#5637 merged + reviewed (TASK-520; continuation #5638 / TASK-522) · leg 2b → [#5636](https://github.com/qf-studio/pilot/issues/5636) → PR#5639 merged + reviewed (TASK-521) · leg 3 → [#5640](https://github.com/qf-studio/pilot/issues/5640) → PR#5642 merged + reviewed (TASK-523) · leg 4 → [console#387](https://github.com/qf-studio/pilot-console/issues/387) (TASK-524) · leg 5a → [ui#223](https://github.com/qf-studio/pilot-console-ui/issues/223) (TASK-526) · leg 5b → [ui#224](https://github.com/qf-studio/pilot-console-ui/issues/224) (TASK-527)

---

## Notes

**Founder decisions needed before leg 1 dispatch** (defaults in bold; dispatch proceeds on the defaults if unanswered):
1. Confirm-before-file in chat: **yes** (card with File / Discard) vs file immediately.
2. Chat tool scope: **read-only allowlist** vs allow `Edit`/`Write` for "small fixes from chat".
3. Issue target when a tenant has several projects: **active project's repo + selector** vs always `repos[0]`.

---

**Last Updated**: 2026-10-09
