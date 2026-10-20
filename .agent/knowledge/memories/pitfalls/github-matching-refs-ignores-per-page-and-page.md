---
name: github-matching-refs-ignores-per-page-and-page
description: GitHub git/matching-refs/heads/<prefix> ignores per_page and page and sends no Link header — a page loop that stops on len<100 works below 100 refs by accident and returns N identical pages above it (PR#5775 ListBranches → 50× per branch at 100+ refs, #5777); fetch it in one request, never paginate
type: pitfall
---

# `git/matching-refs` ignores pagination

**Probe (2026-10-20, qf-studio/pilot):** `matching-refs/heads/?per_page=1` →
7 refs; `per_page=1&page=2` → the same 7; no `Link` header. PR#5775's
`ListBranches` (internal/adapters/github/client.go) loops `page=1..50` and
breaks on `len(batch) < 100`; an httptest with 120 refs produced 50 requests and
6000 entries, and the sweeper would then evaluate every branch 50× (≈100×
branch-count API calls, past the 5000/h budget; `deleted` and the metric
inflate 50×). The tests passed because the fakes honoured `per_page`.

## Rules
- One request for `matching-refs`; dedupe by name if a bound is wanted.
- When a fake honours a query parameter, check that the real endpoint does
  (`gh api -i … | grep -i link`). Follow-up: #5777.
