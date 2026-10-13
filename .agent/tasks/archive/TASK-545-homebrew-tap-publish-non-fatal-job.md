# ci(release): publish the Homebrew formula in a separate non-fatal job so a tap-token failure never marks a shipped release red

**Status**: ✅ MERGED + REVIEWED 2026-10-13 → [#5666](https://github.com/qf-studio/pilot/issues/5666) → PR#5670 merged 20:02Z, post-merge review APPROVE-w-notes (formula path `dist/homebrew/Formula/pilot.rb` proven by a local goreleaser snapshot; `continue-on-error` confirmed). Notes: pasted `make lint` evidence exited 1 on pre-existing QF1012 sites → [TASK-548](TASK-548-lint-remaining-qf1012-tui.md) → #5672. Proof outstanding: the v2.284.0 Release run green on the normal path (closes #5615 evidence).
**Created**: 2026-10-13
**Repo**: qf-studio/pilot

Blocked by: none (independent of the token rotation in #5615; both are needed)

## Context

Every Release run since v2.277.4 ends in failure (#5615): goreleaser publishes the GitHub Release with all six assets, verifies them, and then the Homebrew formula push to qf-studio/homebrew-pilot fails with 403 because HOMEBREW_TAP_GITHUB_TOKEN lost access. The release itself is complete and the daemon self-upgrade works, but the run is red, which pollutes release-health signals and hides real failures. The brews block in `.goreleaser.yaml` pushes the formula inside the same goreleaser step as the release, so one publisher failure fails the whole run.

## Scope

- `.goreleaser.yaml`, the brews entry: set skip_upload to true so goreleaser still renders dist/homebrew/Formula/pilot.rb (with the real sha256 values) but no longer pushes it.
- `.github/workflows/release.yml`: in the goreleaser job, after the existing Verify release assets step, upload dist/homebrew/Formula/pilot.rb as a workflow artifact named homebrew-formula. Add a second job homebrew-tap that needs the goreleaser job, has continue-on-error true, downloads the artifact and pushes it to qf-studio/homebrew-pilot at Formula/pilot.rb through the GitHub contents API with HOMEBREW_TAP_GITHUB_TOKEN (read the current file sha first so the PUT updates instead of conflicts; commit message "pilot <tag>"). Log a clear one-line summary on failure that names the secret and #5615.
- Keep the goreleaser job's own success criteria unchanged: release published and assets verified.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `make lint` passes; paste the output into the PR body.
- `bash -n .github/workflows/release.yml` is not a valid check for YAML, so instead run `npx --yes @action-validator/cli .github/workflows/release.yml` and paste the output into the PR body.
- the rendered goreleaser config validates: run `go run github.com/goreleaser/goreleaser/v2@latest check` and paste the output into the PR body.
- the new job must be marked continue-on-error in the workflow; a reviewer confirms it by reading the file.

## Out of scope

- Rotating HOMEBREW_TAP_GITHUB_TOKEN (founder, #5615).
- The desktop release workflow.

## Refs

- `.goreleaser.yaml` (brews), `.github/workflows/release.yml` (goreleaser job, Verify release assets step), `scripts/verify-release-assets.sh`
- Issue #5615 (token), SOP `.agent/sops/operations/release-asset-completeness-gate.md`
- Pilot issue: https://github.com/qf-studio/pilot/issues/5666
