---
name: tag-push-runs-full-pre-push-gate
description: Pushing a release tag (git push origin vX.Y.Z) runs the FULL pre-push gate (go test -short -race ./..., ~4-5 min) — the docs-only fast path does not apply to tag pushes. Run the push in the background; the tag reaches GitHub only after the gate passes. Out-of-band release = tag the exact main SHA after CI is green; goreleaser publishes (never gh release create).
type: learning
---

# Out-of-band release: tag push runs the full gate

**2026-10-21:** v2.291.0 cut by hand at 11:2xZ (`git tag v2.291.0 808bba8b2 && git push origin v2.291.0`). The push blocked ~5 min in `scripts/pre-push-gate.sh` (`go test -short -race ./...`), then Release (goreleaser + homebrew-tap), Docker, Release Desktop and Sync Docs Version (#5787) ran. Box hot self-upgraded to 2.291.0 within minutes.

## Checklist
1. `gh release list --limit 3` → version = max + 1 (minor if any feat).
2. CI green on the exact `origin/main` SHA; no existing tag.
3. `git tag vX.Y.Z <sha> && git push origin vX.Y.Z` in the background.
4. Watch the Release run; verify `homebrew-tap` job success and the formula version.
5. `~/bin/pilot-board` → `ver=` shows the new version.

Related: decision_release_pipeline_tag_only.
