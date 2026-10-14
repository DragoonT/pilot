# Learning: Founder instruction 2026-09-30: use the navigator-research agent for every proje

## Summary
Founder instruction 2026-09-30: use the navigator-research agent for every project research question (locate code, map seams, post-merge review verification, defect characterization) instead of inline grep chains; Explore only for known-file one-off lookups

## Context
Discovered during development.

## Details
Founder instruction 2026-09-30: use the navigator-research agent for every project research question (locate code, map seams, post-merge review verification, defect characterization) instead of inline grep chains; Explore only for known-file one-off lookups

## Recommended Approach
Apply this knowledge when working on related topics.

## Related
- None documented

---
**Captured**: 2026-09-30
**Confidence**: 95%
**Concepts**: workflow-discipline, review, navigator-integration

## Recurrence 2026-10-14 (founder correction, strong)

Reviewer session grepped the codebase by hand for the PR #5620 triage (pool-manager scoping, `origin/main` hardcodes), for the PR #5683 bootstrap review and for the #5677 usage-route clash before delegating. Founder: "use nav research, how many times to repeat this — every research on the codebase, features, similar should be done with nav research."

**Rule restated:** any question of the form "how does X work / where is X scoped / what else assumes Y" in this or a sibling repo goes to the `navigator:navigator-research` agent FIRST, with a precise brief and citations required. Direct `grep`/`git show` is only for a single known symbol or to verify one line the agent already cited. Reviews count as research: the pins are mine, the map is the agent's.
