# feat(syncingest): derive In Progress for GitHub-linked cards from the pilot-in-progress label

**Status**: 🚀 Dispatched to Pilot 2026-10-13 → [#391](https://github.com/qf-studio/pilot-console/issues/391) (labels `pilot` + `no-decompose`)
**Created**: 2026-10-13
**Repo**: qf-studio/pilot-console

Blocked by: none

## Context

A GitHub-linked card's status derives only from the issue being open or closed (defaultStatusForState in `internal/syncingest/mapping.go`; GitHubRows in `internal/statusmap/rules.go`), and the reconciler diffs status on ProviderState only (remoteChanged in `internal/syncengine/reconcile.go`). A pilot-in-progress label flip therefore leaves State=open and never moves the card: on the 2026-10-13 tenant smoke the card sat in Todo and jumped straight to Done. Founder decision: In Progress only; label removal while open demotes back to Todo; In Review (needs a PR lookup) is out of scope.

## Scope

- `internal/statusmap/rules.go`: add an exported pure DeriveProviderState(provider, state string, labels []string) (providerState string, status, ok bool). For GitHub with state open and the label pilot-in-progress it returns ("open+pilot-in-progress", In Progress, true); everything else returns (state, zero status, false). Also move defaultStatusForState here as the exported DefaultStatusForState so boardapi stops duplicating it. GitHubRows stays untouched. statusmap is the home because it is pure, has no I/O, is already imported by syncingest and boardapi, and imports only board.
- `internal/syncingest/mapping.go`: resolve gains the labels argument, calls DeriveProviderState first, and otherwise falls back to the status_maps lookup with providerState equal to state. remoteSnapshot writes the derived key into ProviderState. Update the two callers in `internal/syncingest/worker.go` (ingestSnapshot and the unmapped branch of ingestKnownCard).
- `internal/syncoutbound/worker.go`: writeShadow passes the connection's provider into buildShadowSnapshot; when DeriveProviderState reports ok on the outcome snapshot (State and Labels) the derived key becomes ProviderState, else the current logic applies. Without this fold the next ingest of a labeled issue would see a spurious status change.
- `internal/boardapi/dispatch.go`: linkAndSeed seeds ProviderState through DeriveProviderState; delete defaultDispatchStatusForState in favour of statusmap.DefaultStatusForState.
- Reconciler: no code change. Assert in tests that a remote key open+pilot-in-progress against a base of open with a clean local moves the card (rule R2), and that a user-moved card plus a label flip ends remote-wins with a sync_conflicts row (rule R4), as accepted in the pilot repo design doc .agent/system/saas-kanban-sync-design.md section 4.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go vet ./...` passes; paste the output into the PR body.
- `go test ./internal/statusmap/ -run TestDeriveProviderState -count=1` passes; paste the output into the PR body.
- `go test ./internal/syncingest/ -run TestDeltaPoll -count=1` passes; paste the output into the PR body.
- `go test ./internal/syncoutbound/ -run TestProcessOp -count=1` passes; paste the output into the PR body.
- `go test ./internal/boardapi/ -run TestHandleDispatch -count=1` passes; paste the output into the PR body.
- delete the pilot-in-progress label check in DeriveProviderState -> TestDeriveProviderState_GitHubOpenWithLabelIsInProgress fails
- revert resolve to return the raw issue state as the provider state -> TestDeltaPoll_LabelFlipMovesOpenCardToInProgress fails
- revert the label-removal branch so the key stays open+pilot-in-progress when the label is gone -> TestDeltaPoll_LabelRemovedWhileOpenDemotesToTodo fails
- remove the DeriveProviderState fold from buildShadowSnapshot -> TestProcessOp_StatusNoopOnLabeledIssueKeepsDerivedProviderState fails
- change the In Progress GitHubRows row's provider state away from open -> TestGitHubRows fails

## Out of scope

- In Review derivation (needs a PR lookup per issue and read budget).
- pilot-failed and pilot-done label semantics beyond closed mapping to Done.
- status_maps row changes or a backfill of existing shadows (the first labeled ingest self-heals).
- Any outbound write triggered by an inbound change (design doc loop-safety rule).

## Refs

- `internal/statusmap/rules.go`, `internal/syncingest/mapping.go`, `internal/syncingest/worker.go`, `internal/syncoutbound/worker.go`, `internal/boardapi/dispatch.go`, `internal/syncengine/reconcile.go`
- Tests to extend: `internal/syncingest/mapping_test.go`, `internal/syncingest/worker_test.go`
- Design: pilot repo .agent/system/saas-kanban-sync-design.md sections 4 to 6 (plain text, lives in another repo)
- Pilot issue: https://github.com/qf-studio/pilot-console/issues/391
