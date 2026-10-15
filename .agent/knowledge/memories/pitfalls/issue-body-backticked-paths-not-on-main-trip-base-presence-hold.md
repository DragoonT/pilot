# Pitfall: Any backticked path that is not on the target repo's main holds the task 'prerequisite not on main' — new fixtures, branch-only files, test-fixture names, cross-repo docs

## Summary
Four dispatches on 2026-10-13/14 sat in 'Task held: prerequisite not on main' for 5–25 min each: a cross-repo .agent/ task doc (ui#233), src/stray.txt as a test fixture name (pilot#5688), five files that existed only on a closed PR branch (pilot#5690), a new testdata JSON to be created (console#409). The legacy gate treats every backticked path-like span as a prerequisite that must exist on main; the shadow classifier would have let 'to_be_created' through but is not authoritative. Fix is an issue-body edit; the next 5-min tick releases the hold.

## Context
Recurrence of SOP 3b across four issues in two days.

## Details
Four dispatches on 2026-10-13/14 sat in 'Task held: prerequisite not on main' for 5–25 min each: a cross-repo .agent/ task doc (ui#233), src/stray.txt as a test fixture name (pilot#5688), five files that existed only on a closed PR branch (pilot#5690), a new testdata JSON to be created (console#409). The legacy gate treats every backticked path-like span as a prerequisite that must exist on main; the shadow classifier would have let 'to_be_created' through but is not authoritative. Fix is an issue-body edit; the next 5-min tick releases the hold.

## Recommended Approach
Before gh issue create, extract backticked path-like tokens from the body and git cat-file -e origin/main:<path> for each in the TARGET repo; write non-existing paths in plain prose ('a new file testdata/x.json under internal/fleet'). Put this check in nav-pilot's pre-flight.

**Recurrence 2026-10-15 (5th):** console#411 (TASK-558) held 'prerequisite not on main' for ~8 min because the Context cited the daemon handler as a backticked pilot-repo path (`internal/gateway/dashboard.go`) in a console issue. The author knew the rule (marker process-correction line) and still skipped the check. The check is mechanical: extract backticked tokens matching `^[\w.-]+(/[\w.-]+)+$`, probe each with `gh api repos/<owner>/<repo>/contents/<path>?ref=main`, rewrite every miss in prose. Run it before `gh issue create`, every time, no exceptions.

## Related
- TASK-550
- TASK-551
- TASK-553
- TASK-554

---
**Captured**: 2026-10-15
**Confidence**: 95%
**Concepts**: dispatch, base-presence, issue-authoring, nav-pilot
