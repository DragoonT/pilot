# feat(dashboard): group the queue panel by project — at most 3 projects × 3 tickets, run time + age on finished rows

**Status**: ✅ MERGED 2026-10-20 16:36Z via [PR#5785](https://github.com/qf-studio/pilot/pull/5785) (5113cd038); post-merge review APPROVE (5/5 mutations killed). Rides the next train (after v2.290.0). Archived. Prior: 🚀 Dispatched to Pilot 2026-10-20 as [#5783](https://github.com/qf-studio/pilot/issues/5783) (`pilot`, `no-decompose`)
**Task ID**: TASK-579 · **Owner**: Navigator plans, Pilot executes · **Design**: founder-approved mockup v2 (2026-10-20 session)

## Context

The QUEUE panel in the TUI dashboard prints every task in `m.tasks` as one flat list (`renderTasks` in `internal/dashboard/tui.go`). The list has no row cap. Done and failed tasks stay in `m.tasks` for the life of the daemon (the monitor never evicts them, see the GH-4617 comment near `renderTasks`). With several projects the panel grows without bound and mixes projects.

Done rows also show an always-full progress bar, which carries no information. The `Duration` string on a done row is wrong: `convertTaskStatesToDisplay` in `cmd/pilot/commands.go` sets it to the time since start for every status, so it keeps growing after the task finishes.

## Target layout

Sample data. The width is the default 69 columns (65 inner).

```
╭─ queue ────┤ ● 1 running  ● gh  ● tg  ● slack  ● jira  ○ 4 idle ├─╮
│                                                                   │
│  pilot-console                                 implementing · 3m  │
│   ● running GH-420  fix(test): PR #41...  ■■░░░░░░░░░░░░░░    12% │
│   ✓ done    GH-418  test(ci): per-pac...  14m · 40m ago      #419 │
│   ✓ done    GH-390  feat(fleet): obse...  11m · 9h ago       #417 │
│                                                                   │
│  pilot                                            last ✓ 25m ago  │
│   ✓ done    GH-5781 chore(autopilot):...  9m · 25m ago      #5782 │
│   ✓ done    GH-5777 fix(github): List...  7m · 8h ago       #5779 │
│   ✗ failed  GH-5774 fix(ci): post-mer...  3m · 10h ago      ci_fa │
│                                                                   │
│  +2 projects                                                      │
╰───────────────────────────────────────────────────────────────────╯
```

## Requirements

1. **Grouping.** Group the tasks by project. The group key is `ProjectPath`. If it is empty, use `ProjectName`. If both are empty, use one group with the display name `(no project)`. Two different paths with the same base name stay two groups.
2. **Project display name.** Use `ProjectName`. If it is empty, use the base name of `ProjectPath`, the same fallback that `syncGitGraphToSelectedTask` uses.
3. **Project order.** Projects that have a running, queued or pending ticket come first. Then sort by the newest activity in the project (the latest of `CompletedAt` and `StartedAt` over its tasks), newest first. The project name is the tiebreak.
4. **Ticket order inside a project.** Running first, then queued (keep queue position order), then pending. Then finished tickets (done, failed, no_op) by `CompletedAt`, newest first. The ID is the tiebreak.
5. **Caps.** Show at most 3 projects and at most 3 tickets per project. When more projects exist, add one last line `+N projects` in `dimStyle` (follow the `maxAutopilotRows` "+ N more" idiom in the same file). Do not show a count for tickets hidden inside a project. Do not add a new hotkey and do not add hint text such as "z zoom". The existing zoom view (enter on the focused panel) shows the full list.
6. **Project header line.** Show the display name in `dimStyle`, the same style as the stage-label and time-ago columns in `renderStandaloneLine` (HISTORY rows). Show one value right-aligned, also in `dimStyle`:
   - A project with a running ticket shows that ticket's `Phase` (lowercase) and its elapsed time, for example `implementing · 3m`. Use `formatDurationShort(time.Since(StartedAt))`. If more than one ticket is running, use the one that started first.
   - Otherwise, with at least one done ticket: `last ✓ ` followed by `formatTimeAgo` of the newest done `CompletedAt`.
   - Otherwise, with only failed tickets: `last ✗ ` followed by `formatTimeAgo` of the newest failed `CompletedAt`.
   - Otherwise (only queued or pending): no right value.
   No rule lines and no status counts in the header.
7. **Blank line** between project groups, and one before the `+N projects` line. No blank line after the last group when there is no `+N projects` line.
8. **Finished rows (done, failed, no_op).** In the 16-column bar slot, show `<run time> · <time ago>` in `dimStyle`, padded to 16 columns, for example `14m · 40m ago`. The run time is `formatDurationShort(CompletedAt − StartedAt)`; the time ago is `formatTimeAgo(CompletedAt)`. If a timestamp is missing, show only the part that is known, or `–`. The meta column stays as today: `#PR` for done, the 5-character phase for failed and no_op.
9. **Running, queued and pending rows** keep today's bar and meta.
10. **Timestamps.** Add `StartedAt` and `CompletedAt` (`time.Time`, zero when unknown) to `TaskDisplay`. Fill them in `convertTaskStatesToDisplay` from the pointer fields on the executor `TaskState` (`internal/executor/monitor.go`). Make `Duration` the run time (`CompletedAt − StartedAt`) for finished tasks, and keep today's elapsed time for running tasks. Do not parse the `Duration` string anywhere.
11. **Selection marker.** `renderTasks` compares a sorted row index with `m.selectedTask`, which indexes the unsorted `m.tasks`. Fix this by matching the selected task by ID (`m.tasks[m.selectedTask].ID`, with a bounds check). The `▸` marker appears only when the selected task is visible.
12. **Legend.** The `● N running` count in the panel border stays computed over all of `m.tasks`, not only the visible rows.
13. **Zoom view.** `renderZoomedQueue` in `internal/dashboard/zoom.go` keeps the flat, uncapped `sortedTasks()` list, its selection (`zoomSel`) and the enter/o open action. If you change `renderTask`, the zoom rows change too. That is acceptable for the finished-row text from item 8. Zoom must not get grouping or caps.

## Known Pitfalls & Patterns

- **PITFALL** (mem-024): ANSI-styled strings break naive width math. Measure every rendered line with `lipgloss.Width`, as `internal/dashboard/queue_width_test.go` does, and use `padOrTruncate` / `truncateVisual` for the header's right value. No line may exceed the inner width.
- **PATTERN** (GH-3970, GH-4338): the title flexes with the inner width and the ID column adapts between 7 and 12 columns (`queueIDColumnWidth`). Keep the 20-column title floor and the 37-column fixed budget. Compute the ID width over the visible rows only.
- **PATTERN**: `maxAutopilotRows` with a "+ N more" line in `internal/dashboard/tui.go` is the cap idiom to copy.
- Grid mode has no task selection: `j`/`k`/arrows move panel focus (TASK-399), and enter opens zoom. Do not change key handling.

## Implementation

- Add one pure function that takes the tasks and returns the visible grouped rows: the project groups in order, their at most 3 tickets, and the hidden-project count. `renderTasks` uses it. Unit-test it without rendering.
- Keep `sortedTasks()` as the flat order for zoom and for `syncZoomQueueSelection`.
- Files: `internal/dashboard/tui.go` (TaskDisplay, renderTasks, renderTask finished-row slot), `cmd/pilot/commands.go` (convertTaskStatesToDisplay), tests in the dashboard package.

## Acceptance Criteria

- [ ] With 5 projects of 4 tickets each, the queue panel shows 3 project groups of 3 tickets each and a last line `+2 projects`. The panel height is at most 1 + 3×4 + 2 + 2 = 17 lines inside the borders, however many tasks exist.
- [ ] With 1 project and 2 tickets, there is no `+N projects` line and no trailing blank line.
- [ ] Project order and ticket order follow requirements 3 and 4. A table-driven test covers: a project with only finished tickets that is newer than an active project still sorts after it; queued order is kept; finished tickets sort by `CompletedAt` newest first.
- [ ] Project header right values follow requirement 6, including the running case, the done case, the only-failed case and the only-queued case.
- [ ] A done row shows `<run time> · <time ago>` and `#PR`. A running row still shows the bar and the percentage.
- [ ] Empty `ProjectName` with a set `ProjectPath` shows the path's base name. Both empty shows `(no project)`.
- [ ] `convertTaskStatesToDisplay` fills `StartedAt` and `CompletedAt`. A completed task's `Duration` is its run time, not the time since start. A test covers this.
- [ ] The `▸` marker is on the row of the task at `m.selectedTask`, matched by ID.
- [ ] The border legend running count includes running tasks in hidden projects.
- [ ] The zoom view still lists every task flat. `TestNav_ZoomedQueueOpensURL` and `TestNav_WidthInvariantMatrix` in `internal/dashboard/tui_nav_test.go` pass.
- [ ] Every rendered line in grid and zoom is at most the panel width, measured with `lipgloss.Width`, at 69 columns and in stacked mode.
- [ ] Existing tests are updated, not deleted, where they pin the old flat layout: `internal/dashboard/queue_width_test.go`, `TestRenderTasksAdapterLegend` in `internal/dashboard/tui_test.go`, `TestFullDashboardRender_WidthInvariants` in `internal/dashboard/grom_chrome_test.go`, and the selection and git-sync tests in `internal/dashboard/gitgraph_test.go`.

## Out of Scope

- New hotkeys, hint text, or changes to grid or zoom key handling.
- Grouping or caps in the zoom view.
- Monitor eviction of finished tasks.
- The HISTORY and AUTOPILOT panels.
- Colour changes other than `dimStyle` for the new header text and finished-row slot.

## Technical Decisions

| Decision | Options | Chosen | Reasoning |
|---|---|---|---|
| Group key | ProjectName · ProjectPath | ProjectPath, then ProjectName | Same base name in two paths must not merge |
| Finished-row data | join to completedTasks · new fields on TaskDisplay | new `StartedAt`/`CompletedAt` fields | completedTasks keeps only the last 5; its Duration format is not consistent |
| Overflow hint | "+N projects · z zoom" · "+N projects" | "+N projects" | No new hotkey; enter on the focused panel already opens zoom |
| Header text | counts · phase/age | phase + elapsed, or last ✓ age | Counts repeat what the rows show |

## Verify

```bash
go test -count=1 ./internal/dashboard/ ./cmd/pilot/
golangci-lint run ./internal/dashboard/... ./cmd/pilot/...
```

## Refs

- Pilot issue: https://github.com/qf-studio/pilot/issues/5783
- Founder design session 2026-10-20 (mockup v1 rejected as overloaded; v2 approved with dim project names and no zoom hint).
- Code map 2026-10-20 (nav-research): `renderTasks`, `sortedTasks`, `renderTask`, `queueIDColumnWidth`, `renderZoomedQueue`, `convertTaskStatesToDisplay`.

**Last Updated**: 2026-10-20
