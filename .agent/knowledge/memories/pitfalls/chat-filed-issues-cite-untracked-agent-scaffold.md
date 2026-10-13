---
name: chat-filed-issues-cite-untracked-agent-scaffold
description: Chat-filed issues (TASK-518 card step) cite .agent/ paths the agent read on the tenant clone; .agent/ is a git-ignored Pilot scaffold there, so the base-presence gate holds the task ('prerequisite not on main') until a human edits the body. Fix layers: prompt rule + card-step rewrite of untracked refs (TASK-531); never loosen the dispatcher gate for it.
type: pitfall
---

# Chat-filed issues cite the untracked .agent scaffold and get held

**What happened (2026-10-13, first real tenant smoke):** the side-chat agent answered a code question on the tenant clone of `pilot-ship-test-go`, then drafted a Pilot issue whose Refs cited `.agent/DEVELOPMENT-README.md:39-50`. The file is real on the clone: Pilot scaffolds `.agent/` locally (`internal/executor/navigator.go`), git-ignored, never committed. The dispatcher's base-presence gate treats every backticked repo path as a prerequisite and held the task for 7 minutes with "referenced path .agent/DEVELOPMENT-README.md not found on default branch" (hold_count 1, 2). A manual `gh issue edit` that dropped the line released it on the next ~5 min cycle.

**Why it is structural:** `internal/executor/chat_prompt.go` tells the agent to read `.agent/DEVELOPMENT-README.md` first and to cite everything as path:line. The issue contract never forbids citing `.agent/`. The gate is correct (SOP Rule 3b class: untracked path).

**Fix (TASK-531):** a prompt rule (never backtick `.agent/`) plus a deterministic rewrite at the card step: extract referenced paths from the draft, check them against the default branch with the existing local-checkout probe, strip the backticks from the missing ones, tell the user, still present the card. Do NOT add `.agent/` to the dispatcher's ignore list: in the pilot repo itself `.agent/` is tracked on main, so the gate's verdict there is right.

**How to apply:** any new producer of issue bodies (chat, Telegram intake, epic decomposition) must validate backticked paths against the target repo's default branch before filing. Recovery for a held issue: edit the body; the gate re-reads it every cycle.
