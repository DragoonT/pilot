## Post-merge review — APPROVE-WITH-NOTES

Reviewed merge `bfa013cbc` against #5803 (own diff read, independent second read, `go test -race`, one mutation pin).

### Verified
- The write now runs on `WithTimeout(WithoutCancel(pollCtx), 10s)`; it is released by `defer cancelWrite()` when `checkApproval` returns (`resolvePending` is synchronous). Ordering: delete from `h.pending` under lock → `pending.CancelFn()` (the `HasApprovalReview` call already finished on that ctx) → `resolvePending(writeCtx)` → `RecordDecision` → send on `ResponseCh` + close → `pollForApproval` exits. No leak, no double-cancel.
- Every other decision source already records on a live ctx: Telegram/Slack pass the adapter's long-lived ctx; the wall-clock default and the async waiter use `context.Background()`; the gateway passes `r.Context()` (pre-existing, out of scope).
- Mutation pin: write on the cancelled poll ctx again → `TestCheckApproval_RecordsDecisionOnDetachedContext` and `TestCheckApproval_Rehydrated_RecordsDecisionOnDetachedContext` fail. Applied and reverted locally.

```
go test -race -count=1 ./internal/approval/   ok  1.895s
```

### Defect (minor) — the Manager branch widens past the spec and regresses the unlinked-request HTTP path
`Manager.RecordDecision` now returns early on every writer error except `ErrApprovalAlreadyDecided`, *before* the pending-map delete and `pr.CancelFn()`. The gateway's decision handler treats `sql.ErrNoRows` (an unlinked request: `SetApprovalRequestID` never landed) as "warn and still resolve" (`internal/gateway/approvals.go` ~L294-301) — but the Manager's async waiter is no longer cancelled, so it lives until the stage timeout, then logs "async approval timed out", attempts the default-action write, and only then calls `handler.CancelRequest`; the Telegram/Slack card stays armed meanwhile. Before this commit the waiter was cleaned on every writer error (GH-4777). The gateway test for this case uses a fake recorder, so it cannot see it. Spec said "no behaviour change for the cancel path, Slack or Telegram handlers". Fix: special-case `sql.ErrNoRows` alongside `ErrApprovalAlreadyDecided` (cleanup, then return), and refresh the GH-4777 doc comment above `RecordDecision`, which now contradicts the code ("must run even when the writer rejects the decision").

### Notes (no action required)
- "Keep the pending entry so the next poll tick can retry" is not achievable: `checkApproval` has already deleted its pending entry and cancelled the poll, and `resolvePending` deletes the persisted row *before* `RecordDecision`. On the fresh path the one retry is the async waiter's `SetApprovalDecision(context.Background(), …)`; on the rehydrated path a transient DB error loses the decision permanently. The #5803 drop is fixed; the retry rationale only holds for fresh requests.
- `WithoutCancel` also drops the shutdown ctx; the detached write can run up to 10 s past shutdown. `pollForApproval` is not tracked by any WaitGroup — pre-existing.
- The rehydrated test sleep-polls (`waitFor`, 5 ms / 2 s) for the poll goroutine's first tick and mutates `p.CancelFn` outside `h.mu`; `-race` passes, but it is timing-based. The fresh-path test is synchronous.
- PR body evidence: the pasted output is `ok … (cached)`, not a fresh `-race` run, and both mutation checks were marked "Not verified". Verified here instead.

