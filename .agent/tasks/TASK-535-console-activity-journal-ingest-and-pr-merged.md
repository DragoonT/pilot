# feat(board): journal ingest-observed status transitions and merged PRs into activity_journal

**Status**: 🚀 Dispatched to Pilot 2026-10-13 → [#395](https://github.com/qf-studio/pilot-console/issues/395) (labels `pilot` + `no-decompose`)
**Created**: 2026-10-13
**Repo**: qf-studio/pilot-console

Blocked by: pilot-console#391 (TASK-534, same worker.go functions)

## Context

activity_journal is written only by the console verbs (journalActivity in `internal/boardapi/handlers.go`: dispatch, status, decision), so the Activity panel stayed empty for the whole 2026-10-13 Pilot run. Ingest already knows every remote-driven transition (the CardChanges in the syncengine Result, see transitionedToDone in `internal/syncingest/donepr.go`) and the merged PR it resolves (maybeResolvePR then SetLinkPR). No execution-lifecycle poller exists; that is deferred.

## Scope

- New migration pair 0027_activity_journal_pr_merged up and down under internal/db/migrations: the up migration drops activity_journal_kind_check and re-adds it with the values dispatch, status, decision, pr_merged; the down migration deletes rows with kind pr_merged and restores the three-value CHECK.
- `internal/board/activity.go`: add ActivityKindPRMerged with value pr_merged to the constants and to validActivityKinds.
- `internal/syncingest/worker.go`: add AppendActivity to the boardStore interface. Add a helper journalStatusTransition(ctx, boardID, card, result) called after ReconcileAndCommit in ingestKnownCard and ingestNewCard: it finds the status field change, skips when from equals to, and appends kind status with detail from, to and source "ingest". Errors are logged and swallowed; the journal never fails the pass.
- `internal/syncingest/donepr.go`: maybeResolvePR gains the board id; after a successful SetLinkPR append kind pr_merged with detail prNumber and prUrl.
- `internal/boardapi/dto.go`: the activity DTO gains Source (omitempty), PRNumber and PRURL; the status detail gains Source; add the pr_merged detail struct and the toJournalActivityDTO case. User-driven rows keep source absent.
- Fakes: the fake board store in `internal/syncingest/worker_test.go` records AppendActivity calls; `internal/boardapi/handlers_test.go` gets a raw-body test for the new fields (wire-contract gate).

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go vet ./...` passes; paste the output into the PR body.
- `go test ./internal/syncingest/ -run TestDeltaPoll -count=1` passes; paste the output into the PR body.
- `go test ./internal/syncingest/ -run TestMaybeResolvePR -count=1` passes; paste the output into the PR body.
- `go test ./internal/boardapi/ -run TestHandleActivity -count=1` passes; paste the output into the PR body.
- `make check-wire-contract-tests` passes; paste the output into the PR body.
- remove the AppendActivity call from journalStatusTransition -> TestDeltaPoll_RemoteStatusChangeJournalsIngestStatusActivity fails
- remove the from equals to guard in journalStatusTransition -> TestDeltaPoll_EchoNeverJournalsStatusActivity fails
- remove the pr_merged append after SetLinkPR -> TestMaybeResolvePR_ResolvedPRJournalsPRMerged fails
- remove the ActivityKindPRMerged case from toJournalActivityDTO -> TestHandleActivity_PRMergedAndIngestSourceJSON fails

## Out of scope

- Execution started and finished events (would need a daemon queue poller).
- UI rendering of the new kind (pilot-console-ui follow-up).
- Backfilling history and journaling first-ingest card creation.

## Refs

- `internal/board/activity.go`, `internal/db/migrations/0011_activity_journal.up.sql` (the CHECK being extended)
- `internal/syncingest/worker.go`, `internal/syncingest/donepr.go`
- `internal/boardapi/dto.go`, `internal/boardapi/handlers.go`, `internal/boardapi/handlers_test.go`
- `scripts/check-wire-contract-tests.sh`
- Pilot issue: https://github.com/qf-studio/pilot-console/issues/395
