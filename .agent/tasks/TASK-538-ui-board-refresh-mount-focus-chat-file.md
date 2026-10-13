# fix(board): refresh cards on mount, on tab focus and after a chat File; never stall polling

**Status**: ✅ REVIEWED 2026-10-13 — [ui#227](https://github.com/qf-studio/pilot-console-ui/issues/227) → PR#228 (9b21140ed, +308/-25, autopilot-merged 10:57Z), review **APPROVE** (3/3 pins kill; full suite 880/880). Notes-only: Node 25 webstorage stub breaks local vitest runs unless NODE_OPTIONS=--no-experimental-webstorage (CI unaffected); no in-flight guard on refreshAll (benign duplicate fetch).
**Created**: 2026-10-13
**Repo**: qf-studio/pilot-console-ui

Blocked by: none (pilot-console TASK-536 makes the File refresh land faster)

## Context

`src/views/BoardView.vue` mounts with the cache-guarded loadCards and a raw setInterval whose first tick is 30 seconds after mount; a failed tick is swallowed by a void call; there is no visibilitychange listener. Re-entering the board route or returning to the tab shows stale cards until a reload. A chat File (decideCard in `src/stores/chat.ts` with action id file) never refreshes the board; the "Filed" reply arrives later as a text event in poll. The drawer's share of mutationsInFlight is not released when the drawer unmounts mid-save (v-if on openCardId), so polling can stall forever. cardsLoaded is never reset, not even on logout, so the next org's board can paint the previous org's cards.

## Scope

1. `src/stores/board.ts`: add lastSyncedAt (Date or null) stamped at the end of refreshCards; add reset() that clears cards, activity, cardsLoaded, activityLoaded and lastSyncedAt; watch the auth store's isAuthenticated and call reset() on logout (same idiom chat.ts uses with useAuthStore). Keep loadCards cache-guarded, because `src/views/IssueView.vue` depends on it; the immediate view refresh below gives stale-while-revalidate for free.
2. `src/views/BoardView.vue`: delete pollTimer, startPolling and stopPolling. Add refreshAll() that returns early while mutations are in flight, else runs refreshCards and refreshActivity together, setting a syncFailed flag true in catch and false on success, with no rethrow. Use the usePolling composable from `src/composables/usePolling.ts` with refreshAll and POLL_INTERVAL_MS. In onMounted call refreshAll first, then start the poller, load connections, and add a visibilitychange listener that refreshes when the document becomes visible; remove the listener in onUnmounted. The auth watch stops the poller. Show an inline notice (data-testid board-sync) above the lanes: "Synced" plus formatRelativeTime of lastSyncedAt, and while syncFailed "Couldn't refresh, retrying" in the error text color. Not a toast.
3. mutationsInFlight: keep the view's own counter; add a drawerMutations ref adjusted by onDrawerMutating and zeroed in closeCard(); the poll gate reads the sum.
4. `src/stores/chat.ts`: add a filedPending set of callback ids, filled in decideCard after a successful callback whose action id is file. In poll, inside the existing branch for new messages, if the set is non-empty: clear it, refresh the board now and once more 15 seconds later (keep the timer id and clear it in reset()). The refresh is the board store's refreshCards with errors swallowed. A Discard decision must not refresh.
5. Tests with fake timers, advanceTimersByTimeAsync and flushPromises; stub document.hidden with vi.spyOn on the hidden getter. `src/views/__tests__/BoardView.spec.ts` polling describe: refreshes immediately on mount even when the store already holds cards; refreshes when the tab becomes visible again; closing the drawer mid-edit does not stall polling; a failed refresh shows the inline notice and clears on the next success. `src/stores/__tests__/board.spec.ts`: refreshCards stamps lastSyncedAt and reset() re-arms loadCards; auth loss resets the store. `src/stores/__tests__/chat.spec.ts` confirmation cards describe: a File decision refreshes the board when the reply lands and once more 15 seconds later; a Discard decision does not refresh; reset() cancels the pending refresh. The existing decideCard test that asserts the callback body now also triggers a refresh; switch it to fake timers.

## Acceptance

- `bun run test` passes; paste the output into the PR body.
- `bun run lint` passes; paste the output into the PR body.
- `bun run build` passes; paste the output into the PR body.
- remove the visibilitychange addEventListener call in BoardView.vue -> the test "refreshes cards when the tab becomes visible again" fails
- make closeCard stop zeroing drawerMutations -> the test "closing the drawer mid-edit does not stall polling" fails
- delete the filedPending branch in the chat store poll -> the test "a File decision refreshes the board when the reply lands and once more 15 s later" fails

## Out of scope

- Stale-while-revalidate inside loadCards, the IssueView refresh, the bell and chat pollers, toasts for poll failures, keep-alive of BoardView, and the console-side ingest nudge.

## Refs

- `src/stores/board.ts`, `src/views/BoardView.vue`, `src/views/BoardCardDrawer.vue`, `src/composables/usePolling.ts`, `src/stores/chat.ts`, `src/stores/auth.ts`, `src/lib/relativeTime.ts`
- Tests: `src/views/__tests__/BoardView.spec.ts`, `src/stores/__tests__/board.spec.ts`, `src/stores/__tests__/chat.spec.ts`, `src/composables/__tests__/usePolling.spec.ts`
- Pilot issue: https://github.com/qf-studio/pilot-console-ui/issues/227
