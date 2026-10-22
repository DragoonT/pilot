#!/usr/bin/env python3
"""Dispatch `### LEG` sections of a Navigator task doc as pilot-labeled GitHub issues.

Format in the task doc:

    ### LEG <ID> — repo: <owner/repo> — title: <issue title>
    <issue body ... until the next "### LEG" or a doc-level "## " heading>

Issue-level H2 sections (## Context, ## Scope, ## Acceptance, ## Out of scope, ...)
belong to the body. Only doc-level headings end a leg: "## Legs…", "## Held…",
"## Refs", "## Dispatched…", "## Known pitfalls…".

Bodies may reference other legs as `#{{ID}}`; the script files legs in document
order and substitutes the issue number once the referenced leg is filed (same repo
only — cross-repo refs are rejected). A leg already filed in an earlier run resolves
from the doc's `## Refs` block (`- ID → https://github.com/owner/repo/issues/N`), so
`--only` re-runs can reference it. Before filing, every backticked path span that
matches the executor's referenced-path rule (contains "/", not a URL, no whitespace,
no glob chars, a dot after the last slash) is checked against `origin/main` of the
local checkout given by --checkout owner/repo=path; a missing path aborts the run
(SOP new-project-issue-authoring Rule 3b).

A leg may also carry probe lines, which are stripped from the filed body:

    probe: present owner/repo <regex>
    probe: absent  owner/repo <regex>

Each probe runs `git grep -E <regex>` on that repo's `origin/main` (any repo with a
--checkout, not only the leg's own). `present` requires a match, `absent` requires
none; a mismatch aborts the run. Use them to pin the premise a leg rests on: that a
knob has no enforcer yet, or that a producer actually emits a field the leg decodes.

Usage:
    nav-dispatch-legs.py TASK.md --checkout qf-studio/x=~/Projects/x [--only S3,S4] [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

LEG_RE = re.compile(r"^### LEG (?P<id>[A-Z]+\d+) — repo: (?P<repo>[\w.-]+/[\w.-]+) — title: (?P<title>.+)$")
REF_RE = re.compile(r"#\{\{([A-Z]+\d+)\}\}")
REFS_LINE_RE = re.compile(r"^- ([A-Z]+\d+) → (https://github\.com/([\w.-]+/[\w.-]+)/issues/(\d+))$", re.M)
DOC_SECTION_RE = re.compile(r"^## (Legs|Held|Refs|Dispatched|Known pitfalls)\b")
SPAN_RE = re.compile(r"`([^`\s]+)`")
PROBE_RE = re.compile(r"^probe:\s+(?P<mode>present|absent)\s+(?P<repo>[\w.-]+/[\w.-]+)\s+(?P<regex>.+?)\s*$")
URL_RE = re.compile(r"^[a-z]+://")


def parse_legs(text: str):
    legs, cur = [], None
    for line in text.splitlines():
        m = LEG_RE.match(line)
        if m:
            cur = {"id": m["id"], "repo": m["repo"], "title": m["title"].strip(), "body": []}
            legs.append(cur)
            continue
        if cur is not None and DOC_SECTION_RE.match(line):
            cur = None
            continue
        if cur is not None:
            cur["body"].append(line)
    for leg in legs:
        probes, kept = [], []
        for line in leg["body"]:
            m = PROBE_RE.match(line)
            if m:
                probes.append((m["mode"], m["repo"], m["regex"]))
            else:
                kept.append(line)
        leg["probes"] = probes
        leg["body"] = "\n".join(kept).strip() + "\n"
    return legs


def parse_refs(text: str):
    """Legs filed by earlier runs: id -> (repo, number, url) from the `## Refs` block."""
    if "## Refs" not in text:
        return {}
    block = text.split("## Refs", 1)[1]
    return {lid: (repo, int(num), url) for lid, url, repo, num in REFS_LINE_RE.findall(block)}


def referenced_paths(body: str):
    out = []
    for span in SPAN_RE.findall(body):
        if "/" not in span or URL_RE.match(span) or any(c in span for c in "*?[]{}"):
            continue
        tail = span.rsplit("/", 1)[-1]
        if "." in tail:
            out.append(span)
    return out


def grep_matches_on_main(checkout: Path, regex: str) -> bool:
    r = subprocess.run(["git", "-C", str(checkout), "grep", "-qE", regex, "origin/main", "--"],
                       capture_output=True)
    return r.returncode == 0


def path_exists_on_main(checkout: Path, rel: str) -> bool:
    r = subprocess.run(["git", "-C", str(checkout), "cat-file", "-e", f"origin/main:{rel}"],
                       capture_output=True)
    return r.returncode == 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("doc")
    ap.add_argument("--checkout", action="append", default=[], help="owner/repo=path")
    ap.add_argument("--only", default="", help="comma-separated leg ids")
    ap.add_argument("--label", default="pilot")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    checkouts = {}
    for item in args.checkout:
        repo, path = item.split("=", 1)
        checkouts[repo] = Path(os.path.expanduser(path))
    only = {s.strip() for s in args.only.split(",") if s.strip()}

    doc = Path(args.doc)
    text = doc.read_text()
    filed = parse_refs(text)
    legs = parse_legs(text)
    if only:
        legs = [l for l in legs if l["id"] in only]
    if not legs:
        print("no legs found", file=sys.stderr)
        return 1

    # pre-flight: paths + refs
    problems = []
    for leg in legs:
        co = checkouts.get(leg["repo"])
        if co is None:
            problems.append(f"{leg['id']}: no --checkout for {leg['repo']}")
            continue
        for rel in referenced_paths(leg["body"]):
            if not path_exists_on_main(co, rel):
                problems.append(f"{leg['id']}: backticked path not on origin/main: {rel}")
        for mode, repo, regex in leg["probes"]:
            pco = checkouts.get(repo)
            if pco is None:
                problems.append(f"{leg['id']}: probe needs --checkout for {repo}")
                continue
            found = grep_matches_on_main(pco, regex)
            if mode == "present" and not found:
                problems.append(f"{leg['id']}: probe expected /{regex}/ in {repo} origin/main, found nothing")
            elif mode == "absent" and found:
                problems.append(f"{leg['id']}: probe expected no /{regex}/ in {repo} origin/main, but it matches")
    ids_by_order = [l["id"] for l in legs]
    repo_by_id = {lid: repo for lid, (repo, _, _) in filed.items()}
    repo_by_id.update({l["id"]: l["repo"] for l in legs})
    for leg in legs:
        if leg["id"] in filed:
            problems.append(f"{leg['id']}: already filed as {filed[leg['id']][2]} (drop it from --only)")
        for ref in REF_RE.findall(leg["body"]):
            in_run = ref in ids_by_order and ids_by_order.index(ref) < ids_by_order.index(leg["id"])
            if not in_run and ref not in filed:
                problems.append(f"{leg['id']}: ref {{{{{ref}}}}} is neither an earlier leg in this run nor in ## Refs")
            elif repo_by_id.get(ref) != leg["repo"]:
                problems.append(f"{leg['id']}: ref {{{{{ref}}}}} is in another repo")
    if problems:
        print("PRE-FLIGHT FAILED:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2

    numbers: dict[str, int] = {lid: num for lid, (_, num, _) in filed.items()}
    urls: dict[str, str] = {}
    for leg in legs:
        body = REF_RE.sub(lambda m: f"#{numbers[m.group(1)]}", leg["body"])
        print(f"[{leg['id']}] {leg['repo']}: {leg['title']}")
        if args.dry_run:
            numbers[leg["id"]] = 0
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(body)
            tmp = f.name
        r = subprocess.run(["gh", "issue", "create", "--repo", leg["repo"], "--title", leg["title"],
                            "--label", args.label, "--body-file", tmp], capture_output=True, text=True)
        os.unlink(tmp)
        if r.returncode != 0:
            print(f"  FAILED: {r.stderr.strip()}", file=sys.stderr)
            return 3
        url = r.stdout.strip().splitlines()[-1]
        num = int(url.rsplit("/", 1)[-1])
        numbers[leg["id"]], urls[leg["id"]] = num, url
        print(f"  -> {url}")

    if not args.dry_run and urls:
        text = doc.read_text()
        lines = [f"- {lid} → {urls[lid]}" for lid in ids_by_order if lid in urls]
        marker = "(filled by the dispatch script)"
        block = "\n".join(lines)
        if marker in text:
            text = text.replace(marker, block, 1)
        elif filed:
            last = list(REFS_LINE_RE.finditer(text))[-1]
            text = text[:last.end()] + "\n" + block + text[last.end():]
        else:
            text = text.rstrip() + "\n\n## Refs\n\n" + block + "\n"
        doc.write_text(text)
        print(f"Refs written to {doc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
