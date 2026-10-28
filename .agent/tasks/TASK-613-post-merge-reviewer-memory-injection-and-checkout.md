# TASK-613: post-merge reviewer reads project memory (M1, now) and, if calibration says so, a read-only checkout (M2, held)

**Status**: 🚀 M1 DISPATCHED 2026-10-28 → pilot#5911 (`pilot`+`no-decompose`, Depends on #5910). M2 DISPATCHED 2026-10-28 → pilot#5916 (`pilot`+`no-decompose`, Depends on #5915); gate met by the calibration (recall 39.4 %). M1 is in the autopilot fix cycle (PR#5914 lint fail → #5915).
**Spec refs**: TASK-387 (executor memory injection: buildMemoryInjectionBlock in `internal/executor/prompt_builder.go`, graphrecall.RecallRelevant in `internal/memory/graphrecall/recall.go`), TASK-591/610/612 (reviewer, diff budget, calibration).
**Origin**: question 2026-10-28 "does Pilot use nav-research patterns on review?" — no: the reviewer is a fixed five-item checklist over the diff; the executor prompt gets up to five ranked graph memories, the reviewer gets none, and it has no checkout to open the counterpart files its checklist asks about.

## Why
- Executor prompts carry "## Known pitfalls from project memory" (≤5 memories, ≤1500 chars, ranked by RecallRelevant over `.agent/knowledge/graph.json` in the project checkout). The reviewer prompt has only issue, diff, PR body, CI.
- 215 pitfall memories encode the defect classes hand reviews keep finding (doc-vs-wire ×4, backticked paths ×8, unwired config fields). The reviewer cannot use them.
- Checklist item 2 asks the model to "name the counterpart producer or consumer file"; with no checkout it can only guess, hence "I could not see" in every verdict.

## Legs — pilot (daemon)

### LEG M1 — repo: qf-studio/pilot — title: feat(autopilot): post-merge reviewer prompt carries the ranked project memories (pitfalls, patterns, decisions) relevant to the issue and the touched files
probe: present qf-studio/pilot func RecallRelevant\(projectPath, taskText string, limit int\)
probe: present qf-studio/pilot Known pitfalls from project memory
probe: absent  qf-studio/pilot Known pitfalls from project memory \(review

## Context

Depends on #5910 (it moves the review-input gather into one exported function; this leg extends that function). The executor already injects ranked knowledge-graph memories into task prompts: buildMemoryInjectionBlock in `internal/executor/prompt_builder.go` calls graphrecall.RecallRelevant(projectPath, text, limit) from `internal/memory/graphrecall/recall.go` and renders "## Known pitfalls from project memory" capped at five entries and 1500 characters, gated on the memory_injection config and a Navigator project. The post-merge reviewer in `internal/executor/post_merge_reviewer.go` builds its prompt from the issue, the diff, the PR body and CI only, so the 215 recorded pitfalls (doc-vs-wire bindings, unwired config fields, stale-snapshot guards) never reach the review, although they are the classes hand reviews keep finding.

## Implementation

1. Add Memories to PostMergeReviewInput (a slice of graphrecall.MemorySummary, or the rendered block as a string — pick the slice so the reviewer owns the rendering).
2. In the exported gather function in `internal/autopilot/post_merge_review.go` (from #5910), when the project path has a Navigator checkout and memory injection is enabled, call RecallRelevant with the issue title, the issue body and the list of files the diff touches (from the diff headers), limit five. Fail open: no graph, no matches or any error leaves Memories empty and logs nothing above Debug.
3. In Review(), render a "## Known pitfalls from project memory (review context)" block between the issue and the diff, same entry format and the same 1500-character cap as the executor block; add one checklist line to the system prompt: "6) For each listed project memory, say whether the diff repeats that pitfall; cite the file and line when it does." Keep the block out of the untrusted-data region note: it is daemon-generated.
4. Log the count of memories injected on the existing "post-merge review" result line, and carry it into the Diff line of the posted comment as "memories: N".
5. Share the renderer: move the entry formatting and the cap into one helper used by both the executor block and the review block so the two cannot drift.
6. Tests, table-driven: gather with a temp project that has a graph.json with two matching and one unrelated memory returns the two; gather with no graph returns none and no error; Review() renders the block and the checklist line only when memories are present; the comment shows memories: N. Fakes read their arguments.
7. Example config: note under post_merge_review that the executor's memory_injection block also gates review context.

## Acceptance

- A review of a PR in a Navigator project with matching pitfalls carries the memory block in the prompt sent to the CLI, and the posted comment's Diff line ends with memories: N where N is greater than zero.
- A review in a project without a graph renders no block and the comment says memories: 0.
- `go test -race ./internal/autopilot/ -run TestGatherPostMergeReviewInput_Memories` passes; paste the output into the PR body.
- `go test -race ./internal/executor/ -run TestPostMergeReviewPromptMemories` passes; paste the output into the PR body.
- skip the RecallRelevant call in the gather -> TestGatherPostMergeReviewInput_Memories_TwoMatching fails
- render the block when Memories is empty -> TestPostMergeReviewPromptMemories_EmptyRendersNothing fails
- exceed the 1500-character cap -> TestPostMergeReviewPromptMemories_CapHolds fails

## Out of scope

- A checkout or tools for the reviewer (M2, held for the calibration result).
- Writing new memories from verdicts.

## Refs

- https://github.com/qf-studio/pilot/issues/5910

## Held — do not dispatch before the TASK-612 calibration report

### LEG M2 — repo: qf-studio/pilot — title: feat(autopilot): post-merge reviewer runs against a read-only checkout of the merge commit with read tools, so checklist item 2 opens the counterpart file instead of naming it
probe: present qf-studio/pilot func localMergedDiff

## Context

Depends on #5915 (the lint fix of the memory-injection PR; both change the reviewer). Gate met by the 2026-10-28 calibration (`.agent/system/bench/post_merge_reviewer_calibration_2026-10.md`): defect recall 39.4 % against a 0.5 bar, and about 18 of the 28 misses need code outside the diff — pre-existing helpers the change interacts with, counterpart DTOs in the same repo, the file a wire field is produced in. The reviewer today invokes the model with --print and the prompt on stdin, no working directory and no tools (`internal/executor/post_merge_reviewer.go` Review, runner from `internal/executor/intent_judge.go`). Checklist item 2 asks it to confirm a wire field's producer in a counterpart file it cannot open.

## Implementation

1. Create a detached read-only worktree of the merge commit under the daemon's temp root (same helper family as the executor's worktrees), remove it after the review, bounded by the review timeout.
2. Run the CLI with the worktree as the working directory and a read-only tool allowlist (Read, Grep, Glob only; no Bash, no Edit, no Write), max turns bounded (for example 12), the same model and timeout.
3. Extend checklist item 2: open the counterpart file and quote the producing line; a field with no producer in the checkout is a defect.
4. Record in the comment's Diff line: "checkout: yes, files read: N".
5. Tests with a fake runner that asserts the working directory and the tool flags; an integration test behind a build tag that runs a real read against a temp repo.

## Acceptance

- The CLI invocation for a review carries the worktree as cwd and a read-only tool allowlist; the worktree is gone after the review.
- A review of a diff that binds a JSON field absent from the producer file in the checkout reports it as a defect with the producer file and line.
- `go test -race ./internal/executor/ -run TestPostMergeReviewCheckout` passes; paste the output into the PR body.
- allow Bash in the tool list -> TestPostMergeReviewCheckout_ReadOnlyTools fails
- skip the worktree removal -> TestPostMergeReviewCheckout_Cleanup fails

## Out of scope

- Letting the reviewer run tests or build.
- Reviews of PRs without a local project path (they keep the diff-only path).

## Refs

- M1 → https://github.com/qf-studio/pilot/issues/5911
- M2 → https://github.com/qf-studio/pilot/issues/5916
