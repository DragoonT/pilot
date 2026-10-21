---
name: nav-task-id-generator-ignores-archive-returns-used-id
description: Navigator's nav-task task_id_generator.py (task_id_source: local) scans only .agent/tasks/, not .agent/tasks/archive/; right after TASK-577 was archived it returned TASK-577 again. Before using a generated ID, check the max ID across tasks/ and tasks/archive/.
type: pitfall
---

# nav-task ID generator reuses archived IDs

**Seen 2026-10-20:** TASK-577 was archived in the morning hygiene commit; the next `task_id_generator.py --json` returned `{"id": "TASK-577"}`. Used TASK-578 by hand.

## Rule
- `ls .agent/tasks .agent/tasks/archive | grep -o '^TASK-[0-9]*' | sort -t- -k2 -n | tail -1` and take +1.
- Navigator-side fix: the generator should scan the archive too (not filed).
