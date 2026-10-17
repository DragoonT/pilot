# Pitfall: A once-per-process guard keyed on the execution path is per task under worktree isolation

## Summary
Executor worktree paths are pilot-worktree-<task>-<unixnano>, unique per task. Any process-wide map, dedupe or cooldown keyed on executionPath never matches twice under worktree isolation. Key such guards on task.ProjectPath (the registered clone). Config lookups via FindProjectByPath are exact-match and have the same requirement.

## Context
2026-10-17 post-merge review of PR #5742 (GH-5739): navBootstrapAttempted.LoadOrStore(executionPath) — documented as once per project per process — re-runs a paid bootstrap session on every task of a project whose bootstrap failed or stayed partial. Same class as the GH-5739 gate defect itself (lookup keyed on the worktree path).

## Details
Two paths flow through the runner: executionPath (the worktree when isolation is active; where files live and where the session runs) and task.ProjectPath (the registered clone the config knows). Anything that must be stable across tasks of the same project — enabled lookups, attempt guards, cooldowns, per-project counters — must use ProjectPath. Anything that touches files or spawns the session uses executionPath. PR #5742 fixed the lookup but kept the guard on executionPath and rewrote its comment to match the wrong key.

## Recommended Approach
When reviewing or writing code in internal/executor that takes a path: ask which of the two it is and whether the value must be stable across tasks. Grep for sync.Map/LoadOrStore/FindProjectByPath call sites that receive executionPath. Test with two distinct execution paths and one project path.

## Related
- TASK-572
- TASK-574
- `internal/executor/navigator_bootstrap.go`
- `internal/executor/runner.go`
- `internal/executor/worktree.go`

---
**Captured**: 2026-10-17
**Confidence**: 95%
**Concepts**: executor, worktree, testing
