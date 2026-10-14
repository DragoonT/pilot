# fix(board): map the `pr_merged` activity kind and the `source` field on the wire, and never let an unknown kind blank the board

**Status**: ✅ MERGED + REVIEWED + LIVE 2026-10-14 → [ui#233](https://github.com/qf-studio/pilot-console-ui/issues/233) → PR#234 merged 11:47Z (squash 74d182984), post-merge review APPROVE (2/2 pins killed by the reviewer; 194 tests; vue-tsc clean), deployed 11:56Z, verified on `/board`: GH-9 in Done, Activity shows "PR #10 merged" (linked) and "Synced: Status changed: In Progress → Done", no console errors. Authoring miss on dispatch: a backticked cross-repo `.agent/` path in Refs tripped the base-presence hold for ~20 min (SOP 3b) — fixed by an issue-body edit.
**Created**: 2026-10-14
**Repo**: qf-studio/pilot-console-ui

Blocked by: none

## Context

The first real `pr_merged` activity row in production (tenant smoke 2026-10-14 10:57:10Z, pilot-ship-test-go#9 → PR#10) blanks the whole Board view. `GET /api/v1/board/activity` returns two valid rows (`status` in_progress→done with `source: "ingest"`, and `pr_merged` with `prNumber`, `prUrl`, `source`). `toActivityEntry` in `src/lib/api/httpAdapter.ts` (line 698 on main a1d92f8) switches on `wire.kind` with cases for `conflict`, `dispatch`, `status`, `decision` only and has no default, so a `pr_merged` row maps to `undefined`. `BoardView.vue` line 362 renders `v-for="entry in board.activity" :key="entry.id"`, which throws `TypeError: Cannot read properties of undefined (reading 'id')` on every poll; the main area stays empty. PR #230 (TASK-543) added `pr_merged` to `types.ts`, `activityMessage.ts`, `BoardView.vue` and `BellPopover.vue` but not to the wire mapper, and its tests built entries by hand, so the wire path was never exercised. The same mapper also drops `source` from `status` rows, so the "Synced: " prefix from PR #230 never renders from real data either.

Confirmed in the browser: console shows the TypeError at `BoardView-jHL5URCM.js:1:24280` (the `key: e.id` of the activity list) on every refresh; `/api/v1/board/cards` returns five cards, all `done`, including the new one.

## Scope

- `src/lib/api/httpAdapter.ts`: add `WirePrMergedActivity` (`kind: 'pr_merged'`, `prNumber: number`, `prUrl: string`, `source?: 'ingest'`) to the `WireActivityEntry` union; add the `pr_merged` case to `toActivityEntry` returning `{ ...base, kind: 'pr_merged', prNumber, prUrl, ...(source !== undefined ? { source } : {}) }`; carry `source` on the `status` case the same way; add a `default` that returns `undefined` for an unknown kind, and make `listBoardActivity` filter those out so one unrecognised row can never blank the list again. Add a `WireStatusActivity.source?: 'ingest'` field.
- `src/lib/api/__tests__/fixtures/board-activity.json`: add a `pr_merged` row with `source: "ingest"`, a `status` row with `source: "ingest"`, and one row with an unknown kind (for example `kind: "future_kind"`).
- No view changes; `BoardView.vue` and `activityMessage.ts` already handle the typed entry.

## Acceptance

- `npm run build` passes; paste the output into the PR body.
- `npx vitest run src/lib/api/__tests__/httpAdapter.spec.ts` passes; paste the output into the PR body. Extends the existing listBoardActivity test (or adds `listBoardActivity maps pr_merged with prNumber/prUrl/source, keeps source on status rows, and drops an unknown kind instead of throwing`): the mapped list contains the `pr_merged` entry with `prNumber`, `prUrl` and `source: 'ingest'`, the `status` entry carries `source: 'ingest'`, the unknown-kind row is absent, and no entry is `undefined`.
- `npx vitest run src/views/__tests__/BoardView.spec.ts` passes; paste the output into the PR body.
- `npx vue-tsc --noEmit` passes; paste the output into the PR body.
- remove the `pr_merged` case from toActivityEntry -> the extended listBoardActivity test fails
- remove the undefined filter in listBoardActivity -> the extended listBoardActivity test fails on the unknown-kind row

## Out of scope

- Any Board or Bell rendering change.
- The console (Go) side; the wire shape is correct.

## Refs

- `src/lib/api/httpAdapter.ts` (toActivityEntry, listBoardActivity, WireActivityEntry), `src/lib/api/types.ts` (BoardActivityPrMerged), `src/lib/activityMessage.ts`, `src/views/BoardView.vue:362`
- ui PR #230 (TASK-543) — the leg that added the kind everywhere except the mapper
- pilot repo task doc TASK-543 (archived) — the planning record for PR #230
- Pilot issue: https://github.com/qf-studio/pilot-console-ui/issues/233
