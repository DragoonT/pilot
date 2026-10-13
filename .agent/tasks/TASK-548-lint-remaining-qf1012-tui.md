# chore(lint): fix the remaining staticcheck QF1012 sites so `make lint` passes with golangci-lint 2.14

**Status**: 🚀 Dispatched to Pilot 2026-10-13 → [#5672](https://github.com/qf-studio/pilot/issues/5672) (labels `pilot` + `no-decompose`; found in the post-merge review of PR #5670)
**Created**: 2026-10-13
**Repo**: qf-studio/pilot

Blocked by: none

## Context

PR #5668 (TASK-544) replaced three WriteString(fmt.Sprintf(...)) sites, but `make lint` on main (3a2cde3e5) with golangci-lint 2.14.0 still reports three QF1012 findings in `internal/dashboard/tui.go` at lines 1514, 2865 and 2872. CI runs golangci-lint v2.8.0, which does not flag them, so CI is green while the local full gate (and the pre-push hook when it falls through to the full gate) is red. `internal/adapters/github/converter.go` lines 149, 150, 151 and 164 use the same pattern and appeared in the lint output pasted into PR #5670; fix them in the same pass so the next linter bump does not reopen this.

## Scope

- `internal/dashboard/tui.go`: replace the three `WriteString(fmt.Sprintf(...))` calls with `fmt.Fprintf(&builder, ...)` (or `fmt.Fprintf(builder, ...)` where the builder is already a pointer). No behaviour change.
- `internal/adapters/github/converter.go`: same replacement at the four sites.
- Run `golangci-lint cache clean` before the final `make lint` so results from other worktrees do not leak in.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `golangci-lint cache clean && make lint` passes; paste the output into the PR body.
- `go test ./internal/dashboard/ ./internal/adapters/github/ -count=1` passes; paste the output into the PR body.
- `grep -rn 'WriteString(fmt.Sprintf' internal/dashboard/tui.go internal/adapters/github/converter.go` prints nothing; paste the output into the PR body.

## Out of scope

- Bumping the golangci-lint version pinned in `.github/workflows/ci.yml`.
- Any other linter category.

## Refs

- `internal/dashboard/tui.go`, `internal/adapters/github/converter.go`
- PR #5668 (TASK-544), PR #5670 review notes
- Pilot issue: https://github.com/qf-studio/pilot/issues/5672
