# Pitfall: A test that reads a commit by its pre-rewrite SHA can never see the rewrite

## Summary
Git objects are immutable: after a history rewrite the old SHA still resolves to the old commit with its old message. A test that captures a SHA before the operation and then runs git log -1 <oldSHA> to assert the message is untouched passes even when the whole branch was rewritten. Assert on a ref (HEAD~2) or compare rev-parse of the ref to the captured SHA.

## Context
2026-10-17 post-merge review of PR #5740 (GH-5738). Under the pin that removed the origin-refs check the whole history was rewritten, yet the older-commit assertion stayed green; only the HEAD^-unchanged check caught it.

## Details
In internal/executor/git_test.go the helper captured oldest := rev-parse HEAD~2 before stripCoAuthorBeforePush, then asserted git log -1 --format=%B <oldest> still contained the trailer. The old object is never mutated, so this cannot fail. The same holds for rev-list --count after any message-only rewrite. The load-bearing assertions are the ones that read through a ref after the operation: rev-parse HEAD^ == parentBefore, or log -1 HEAD~2.

## Recommended Approach
When asserting that history was NOT rewritten beyond a point: compare rev-parse <ref> after the operation to the SHA captured before, or read the message through the ref. Never read through a SHA captured before the rewrite. Mutation-test the assertion: apply the bug and confirm the assertion fails.

## Related
- TASK-571
- `internal/executor/git_test.go`

---
**Captured**: 2026-10-17
**Confidence**: 95%
**Concepts**: testing, git, executor
