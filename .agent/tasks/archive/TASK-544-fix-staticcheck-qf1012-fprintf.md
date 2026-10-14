# chore(lint): replace WriteString(fmt.Sprintf(...)) with fmt.Fprintf at the three staticcheck QF1012 sites

**Status**: ✅ MERGED + REVIEWED 2026-10-13 → PR#5668 (APPROVE on read); the remaining sites went in TASK-548 → PR#5673 (42-file sweep, `make lint` 0 issues). Shipped in v2.284.0.
**Created**: 2026-10-13
**Repo**: qf-studio/pilot

Blocked by: none

## Context

The local pre-push gate runs golangci-lint with staticcheck and fails on three pre-existing QF1012 findings: two in `e2e/mocks/claude.go` (the script builder writes) and one in `internal/memory/query.go` (the pattern summary line). CI does not fail on them, so every docs-only push from a shell where the hook gets no stdin falls to the full gate and is blocked. Fix the three sites so the full gate is green again.

## Scope

- `e2e/mocks/claude.go`: replace the two scriptBuilder.WriteString(fmt.Sprintf(...)) calls with fmt.Fprintf(&scriptBuilder, ...) keeping the format strings and arguments identical.
- `internal/memory/query.go`: replace sb.WriteString(fmt.Sprintf(...)) with fmt.Fprintf(&sb, ...) keeping the format and arguments identical.
- No behaviour change; the rendered strings must be byte-identical.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go vet ./e2e/mocks/ ./internal/memory/` passes; paste the output into the PR body.
- `make lint` passes; paste the output into the PR body.
- `go test ./internal/memory/ -run TestQuery -count=1` passes; paste the output into the PR body.

## Out of scope

- Any other lint category or file.

## Refs

- `e2e/mocks/claude.go`, `internal/memory/query.go`
- `.golangci.yml` (staticcheck is enabled there)
- Pilot issue: https://github.com/qf-studio/pilot/issues/5663
