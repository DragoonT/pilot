---
name: goreleaser-rerun-on-published-tag-fails-422-push-formula-by-hand
description: Rerunning a failed Release job on an already-published tag cannot help: goreleaser re-uploads assets and GitHub answers 422 (asset exists) before the Homebrew step. Recovery = render Formula/pilot.rb from the live tap file + release checksums.txt and PUT it via the contents API (push rights on homebrew-pilot). Also: the tap token mix-up on 2026-10-05 (token scoped to homebrew-tap, goreleaser pushes to homebrew-pilot) caused 8 days of red Release runs; fix is token repository access, not a new token.
type: pitfall
---

# goreleaser rerun on a published tag fails with 422; push the formula by hand

**Seen 2026-10-13 (v2.283.0, run 38437693021 attempt 2):** after the tap token was fixed, `gh run rerun --failed` re-ran the goreleaser job. It rebuilt and tried to upload `pilot-linux-arm64.tar.gz` to the existing release → `422 Validation Failed` → the run died before the Homebrew step. A rerun can never repair a tap push on a published tag.

**Recovery that works (3 minutes):** fetch `Formula/pilot.rb` + its blob sha from `qf-studio/homebrew-pilot`, fetch `checksums.txt` of the tag, replace the version, the four download URLs and the four sha256 values, `gh api --method PUT repos/qf-studio/homebrew-pilot/contents/Formula/pilot.rb` with the base64 content and the blob sha. Commit message `Brew formula update for pilot version vX.Y.Z` matches goreleaser's.

**The token incident (pilot#5615):** `HOMEBREW_TAP_GITHUB_TOKEN` was rewritten 2026-10-05 08:06Z with the fine-grained token `qf-studio-homebrew-tap` whose repository access was only `qf-studio/homebrew-tap` (grot's tap). goreleaser pushes to `qf-studio/homebrew-pilot` (users run `brew tap qf-studio/pilot`). Fix = edit the token's repository access on the owner's account page (the org page only revokes); no secret change needed. 403 "Resource not accessible by personal access token" on a fine-grained PAT = wrong repo list or permission, not expiry.

**How to apply:** TASK-545 moves the tap push into a separate non-fatal job that PUTs the goreleaser-rendered formula via the API — exactly this recovery, automated.
