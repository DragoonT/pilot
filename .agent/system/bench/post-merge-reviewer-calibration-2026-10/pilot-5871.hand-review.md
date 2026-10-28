## Post-merge review — APPROVE-WITH-NOTES

Reviewed merge `62fdf98ca` against #5849 (own diff read, independent second read, `go test -race`, one mutation pin).

### Verified
- The live gate (`githubLiveAdmissionSkipReason`) re-checks, in order: closed · trigger label absent · `pilot-needs-human` · `pilot-blocked` · `pilot-needs-clarification`, against a fresh `GetIssue` read (SDK client with default retry on 429/403), before `AddLabels`, before `handleIssueGeneric` and before any claim. A gate skip writes no label, posts no comment, creates no task row and no claim, so it cannot strand `pilot-in-progress` or wedge a claim (GH-5273 class).
- The remaining window between the GET and `AddLabels`/`handleIssueGeneric` is seconds (the spec guard may GET parents), not the minutes-long slot wait; the spec puts "stopping a task that already started" out of scope.
- `gh5056` test change: only the argument of `githubEventHasNeedsHumanLabel` was renamed (`ev.Labels` → `liveLabels`); the positional "before `handleIssueGeneric(`" assertion is unchanged.
- Tests drive the real handler, a real `memory.Store`/`Dispatcher` and an `httptest` GitHub through the new `githubTaskClientOpts` seam; closed and trigger-removed are separate subtests.
- Mutation pin: gate returns `""` → `TestHandleGithubIssueEventSDK_LiveLabelsGate` fails. Applied and reverted locally.

```
go test -race -count=1 ./cmd/pilot/ -run 'GH5072|Gh5072|GH5056|Gh5056|NeedsHuman|SlotWait|Repick'   ok  9.368s
```

### Defect (low) — the trigger-label re-check is exact-case; the poller and webhook are not
`githubEventHasLabel` compares `l == label`, while the SDK's `HasLabel` (`sdk/integrations/github/client.go` L556-558) and the webhook handler both use `strings.EqualFold`, and GitHub's `labels=` filter is case-insensitive. A config `pilot_label: Pilot` against a repo label `pilot` admitted before this PR and now skips every offer with `trigger_label_removed`, re-arms the backoff each time and never runs — surfaced only at INFO. The founder box uses lower-case `pilot`, so it is not affected. Fix: `strings.EqualFold` in `githubEventHasLabel` (it also serves the needs-human and pilot-strip checks, which GitHub itself treats case-insensitively).

### Notes (no action required)
- Any fetch error (rate-limit retries exhausted, 404, 5xx) is WARN + fail-open to the pre-wait snapshot — spec-sanctioned, but a 404 (issue deleted or transferred) is positive evidence of ineligibility and is treated as unknown.
- The `issueState != StateClosed` else-branch ("issue already closed, skipping pilot-in-progress label") is now unreachable (closed returns at the gate); dead code with a misleading INFO line.
- The backoff pre-check reports `skipReasonNeedsHuman` for every key the gate armed, so an issue whose label was removed and re-added inside the window shows the wrong reason until it expires.
- Gate skips increment the same `claimLostDrops` counter the GH-5300 pilot-strip reads (threshold 3); human holds and claim-lost drops are now conflated. Low likelihood, since blocked/closed/un-labeled issues leave the candidate set.
- `resolveAutopilotFixBranch`, `taskDesc`, `AcceptanceCriteria` and the pilot-strip guard still read the pre-wait snapshot while `specBody`/labels use the live one — pre-existing, outside #5849.
- The fetch-error subtest only asserts "not one of the five skip reasons"; it does not pin "proceeds with `ev.Labels`". It returns 500, which the client retries with backoff (the PR's `ok 20.8s` is mostly that); a 404 would be fast and non-retryable.
- `githubTaskClientOpts` is a package-level mutable test seam written by subtests without synchronisation; safe only while nothing in the package calls `t.Parallel()`.
- Both mutation-check acceptance items were recorded "Not verified: freeform mutation" in the PR body. Verified here.

