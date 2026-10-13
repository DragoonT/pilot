# feat(board): render the pr_merged activity kind and mark ingest-sourced status rows

**Status**: 🚀 Dispatched to Pilot 2026-10-13 → [#229](https://github.com/qf-studio/pilot-console-ui/issues/229) (labels `pilot` + `no-decompose`)
**Created**: 2026-10-13
**Repo**: qf-studio/pilot-console-ui

Blocked by: none

## Context

pilot-console PR #397 (issue #395) now journals two things the UI does not know: a new activity kind pr_merged with prNumber and prUrl, and a source field with value ingest on status rows written by the sync ingest (user-driven rows have no source). `src/lib/activityMessage.ts` switches on the four known kinds, so a pr_merged row renders with no message, and ACTIVITY_STATUS has no dot color for it. Both the board activity list in `src/views/BoardView.vue` and the bell popover in `src/design-system/components/BellPopover.vue` use these helpers.

## Scope

- `src/lib/api/types.ts`: extend the BoardActivityEntry union with the pr_merged variant (kind, cardId, createdAt, prNumber, prUrl, optional source) and add the optional source field with the literal type ingest to the status variant.
- `src/lib/activityMessage.ts`: formatActivityMessage returns "PR #<prNumber> merged" for pr_merged, and for a status entry whose source is ingest prefixes the existing text with "Synced:" (so a user move and a tracker-driven move read differently). ACTIVITY_STATUS gains pr_merged with the success color.
- `src/views/BoardView.vue` and `src/design-system/components/BellPopover.vue`: when the entry has prUrl, render the message text as a link to it (same anchor styling the transcript autolink uses, opens in a new tab).

## Acceptance

- `bun run test` passes; paste the output into the PR body.
- `bun run lint` passes; paste the output into the PR body.
- `bun run build` passes; paste the output into the PR body.
- remove the pr_merged case from formatActivityMessage -> the test "formats a pr_merged entry with its PR number" fails
- remove the Synced prefix for ingest-sourced status entries -> the test "prefixes ingest-sourced status changes" fails
- render the pr_merged message without the link -> the test "links a pr_merged activity row to its PR" fails

## Out of scope

- Changes to the console journal or DTO.
- Filtering or grouping of the activity feed.

## Refs

- `src/lib/activityMessage.ts`, `src/lib/api/types.ts`, `src/views/BoardView.vue`, `src/design-system/components/BellPopover.vue`
- Tests: `src/views/__tests__/BoardView.spec.ts` (activity list rendering), a new spec next to the other lib specs under src/lib
- Producer: pilot-console PR #397 (kind pr_merged, source ingest)
- Pilot issue: https://github.com/qf-studio/pilot-console-ui/issues/229
