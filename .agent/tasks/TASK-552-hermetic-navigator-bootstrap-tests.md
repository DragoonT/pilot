# test(executor): build the Navigator bootstrap fixtures from the embedded templates so the suite passes on machines with the Navigator plugin installed

**Status**: 🚀 Dispatched to Pilot 2026-10-14 → [#5689](https://github.com/qf-studio/pilot/issues/5689) (labels `pilot` + `no-decompose`; found in the post-merge review of PR #5683 / TASK-549)
**Created**: 2026-10-14
**Repo**: qf-studio/pilot

Blocked by: none

## Context

`fixtureClone` in `internal/executor/navigator_bootstrap_test.go` calls `NewNavigatorInitializer`, which prefers the Navigator plugin templates under `~/.claude/plugins/cache/navigator-marketplace/navigator/<version>/templates/` when they exist and falls back to the embedded `internal/executor/templates/` otherwise. Plugin 8.3.5 nests `### Key Components` under `## Project Structure`; the embedded README keeps it under `## Architecture`. With the plugin installed, `filledReadme` replaces the `## Project Structure` body, which swallows the nested header, and `TestNavigatorBootstrap_FillsContextSections` fails with `navigator_bootstrap_test.go:236: section "### Key Components" missing after bootstrap`. CI and the box have no plugin cache, so they pass. Every developer machine with the plugin fails `go test ./internal/executor/`.

## Scope

- `internal/executor/navigator_bootstrap_test.go`: build the fixture with an initializer that uses the embedded templates only (construct `NavigatorInitializer` with an empty `templatesPath`, or add a small `newEmbeddedNavigatorInitializer` test helper in a non-test file if the fields are unexported).
- `filledReadme`: replace only the direct body of each section (text up to the next heading of any level), so a nested subsection keeps its header. Add a case to `TestNavigatorReadmeHasPlaceholder` with the plugin layout (Key Components nested under Project Structure) to show detection still works there.
- No change to production code paths beyond the optional helper.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go test ./internal/executor/ -run 'NavigatorBootstrap|NavigatorReadmeHasPlaceholder' -count=1` passes; paste the output into the PR body.
- `HOME=$(mktemp -d) go test ./internal/executor/ -run 'NavigatorBootstrap' -count=1` passes; paste the output into the PR body.
- make fixtureClone call NewNavigatorInitializer again -> the new nested-layout case in TestNavigatorReadmeHasPlaceholder still passes but TestNavigatorBootstrap_FillsContextSections fails on a machine with plugin 8.3.5 installed (reviewer runs this pin)

## Out of scope

- Changing which templates production uses.

## Refs

- `internal/executor/navigator_bootstrap_test.go` (fixtureClone, filledReadme), `internal/executor/navigator.go` (NewNavigatorInitializer, FindTemplatesPath, contextInjectionSections), `internal/executor/templates/DEVELOPMENT-README.md`
- PR #5683 post-merge review (note section)

- Pilot issue: https://github.com/qf-studio/pilot/issues/5689
