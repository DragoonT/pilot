# feat(upgrade): verify release asset sha256 against checksums.txt before install

**Status**: 📋 Planned 2026-10-13
**Created**: 2026-10-13
**Repo**: qf-studio/pilot

Blocked by: none

## Context

Headless tenants will soon exec into whatever downloadAsset in `internal/upgrade/upgrade.go` fetched from an unauthenticated GitHub download URL. The upgrade package has no integrity check, although every release publishes checksums.txt (see `.goreleaser.yaml`). Verify before backup and install so a corrupt or tampered archive never replaces the binary.

## Scope

- `internal/upgrade/upgrade.go`: add findChecksumsAsset(release) that returns the checksums.txt asset or nil, and verifyAssetChecksum(ctx, release, asset, downloadPath) on the Upgrader. The verifier fetches the checksums asset through the Upgrader's httpClient, parses lines of the form hex, two spaces, filename, finds asset.Name, computes sha256 of the downloaded file and compares with hex.EqualFold. A mismatch, fetch error or parse error returns an error. A release with no checksums.txt asset logs a warning and proceeds; the asset list comes from api.github.com, so absence cannot be forged by a download-path interception.
- Upgrade in the same file: call verifyAssetChecksum after downloadAsset and before createBackup, with the progress message "Verifying checksum...".

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go vet ./internal/upgrade/` passes; paste the output into the PR body.
- `go test ./internal/upgrade/ -run TestUpgrader_verifyAssetChecksum -count=1` passes; paste the output into the PR body. Table cases: Match, Mismatch, MissingChecksumsAssetSkips, MalformedLineErrors, with one httptest server that serves both the asset and checksums.txt.
- `go test ./internal/upgrade/ -run TestUpgrader_Upgrade_ChecksumMismatchAbortsBeforeBackup -count=1` passes; paste the output into the PR body. Asserts no backup file exists and the original binary bytes are untouched.
- `go test ./internal/upgrade/ -run TestHotUpgrader -count=1` passes; paste the output into the PR body.
- replace the hex comparison in verifyAssetChecksum with a constant true -> TestUpgrader_verifyAssetChecksum/Mismatch fails
- remove the verifyAssetChecksum call from Upgrade -> TestUpgrader_Upgrade_ChecksumMismatchAbortsBeforeBackup fails

## Out of scope

- Signature verification (cosign), the Homebrew path, asset naming changes, and the headless wiring (separate issue).

## Refs

- `internal/upgrade/upgrade.go` (downloadAsset, Upgrade, createBackup), `internal/upgrade/upgrade_test.go`, `internal/upgrade/hot_test.go` (httptest client swap), `internal/upgrade/hot.go`
- `.goreleaser.yaml` (checksums.txt publication)
