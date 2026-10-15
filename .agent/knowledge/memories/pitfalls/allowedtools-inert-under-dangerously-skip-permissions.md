# Pitfall: --allowedTools enforces nothing under --dangerously-skip-permissions; use --disallowedTools or a PreToolUse guard via --settings

## Summary
Every Pilot claude spawn passes --dangerously-skip-permissions, so --allowedTools is only an auto-approve list: Write(.agent/**) did not stop a write to ./outside.txt in a live CLI probe (2026-10-14). The chat 'read-only' tool list and the bootstrap allowlist were prompt-level only; unit tests passed because the fake backend re-implemented the rule. What holds under skip-permissions: --disallowedTools (deny list) and a PreToolUse hook passed with --settings that exits 2 (hooks fire regardless of permission mode). Fixed by TASK-551 (PR#5692: per-run settings file + write-guard.sh + git sweep after bootstrap) and TASK-555 (PR#5696: guard portable, no realpath -m).

## Context
Post-merge review of PR#5683 (TASK-549 Navigator bootstrap) with three live probes of the local claude CLI.

## Details
Every Pilot claude spawn passes --dangerously-skip-permissions, so --allowedTools is only an auto-approve list: Write(.agent/**) did not stop a write to ./outside.txt in a live CLI probe (2026-10-14). The chat 'read-only' tool list and the bootstrap allowlist were prompt-level only; unit tests passed because the fake backend re-implemented the rule. What holds under skip-permissions: --disallowedTools (deny list) and a PreToolUse hook passed with --settings that exits 2 (hooks fire regardless of permission mode). Fixed by TASK-551 (PR#5692: per-run settings file + write-guard.sh + git sweep after bootstrap) and TASK-555 (PR#5696: guard portable, no realpath -m).

## Recommended Approach
Never claim a tool restriction from --allowedTools in a spec; prove it with a real CLI probe or a fake-CLI argv test (TestChatTurn_DeniesWriteToolsOnTheCLI pattern). Restrict with --disallowedTools or a PreToolUse guard; keep allowedTools only for token cost.

## Related
- TASK-549
- TASK-551
- TASK-555
- `internal/executor/backend_claudecode.go`
- `internal/executor/write_boundary.go`
- `internal/executor/chat_turn.go`

---
**Captured**: 2026-10-15
**Confidence**: 95%
**Concepts**: executor, claude-code, permissions, security, chat, navigator-bootstrap
