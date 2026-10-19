# Learning: task_to_graph.py rewrites graph.json with \u escapes; re-dump with ensure_ascii=False before commit

## Summary
The nav-task graph sync (task_to_graph.py --action add) writes graph.json with ensure_ascii=True, so every em dash and arrow becomes a \u escape: about 500 lines of churn for one task node. Re-dump with json.dumps(indent=2, ensure_ascii=False) plus a trailing newline; the diff shrinks to the new node and edges.

## Context
TASK-576 doc commit faf719c8d, 2026-10-19.

## Details
The nav-task graph sync (task_to_graph.py --action add) writes graph.json with ensure_ascii=True, so every em dash and arrow becomes a \u escape: about 500 lines of churn for one task node. Re-dump with json.dumps(indent=2, ensure_ascii=False) plus a trailing newline; the diff shrinks to the new node and edges.

## Recommended Approach
After any Navigator graph script, check git diff --stat on graph.json; re-encode if the diff is far larger than the change.

## Related
- TASK-576

---
**Captured**: 2026-10-19
**Confidence**: 95%
**Concepts**: knowledge

## Correction (2026-10-19, same day)
The pre-commit knowledge-graph step also rewrites graph.json with `\u` escapes when a commit adds memories (commit 61a7bb46c: 633 changed lines, all encoding). Re-encoding by hand only holds until the next such commit. The escaped and UTF-8 forms are the same JSON; accept the churn, or fix the encoding in the hook / graph scripts (ensure_ascii=False) in the navigator repo.
