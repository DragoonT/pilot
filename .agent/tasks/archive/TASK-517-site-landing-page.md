# feat(site): landing page — ticket-to-green story (hero, Pilot at work, CI green, six feature cards, pricing, contact)

**Status**: ✅ 10-20: merged as site PR#4, site#2 closed; tracked under TASK-515. Archived. Prior: 🧑‍💻 BUILT LOCALLY 2026-10-11/12 by Navigator (founder iterating visually) on `feat/landing-story` in pilotcloud-site — NOT executed by Pilot; site#2 label `pilot` removed, issue kept as the spec of record. Spec below superseded in two places by the paper sketch (IMG_6027): no "Pilot at work" two-window stage — a kanban Board instead; no six-card feature grid — a steps/gates timeline + Triggers/Integrations/Gates columns instead. Tickets must be real, PM-readable, vendor-free. Next: PR closing #2.
**Created**: 2026-10-09
**Repo**: qf-studio/pilotcloud-site

Blocked by: #1

## Context

The scaffold (issue #1) gives this repo the static-export build, the console theme tokens, the Section and card primitives, the header and the footer. This issue fills the home page. The page covers both ways to run Pilot: the terminal version (open source under BSL 1.1, installed with Homebrew, runs on the user's own Claude key) and Pilot Console (hosted, one plan, USD 499 per month). Legal pages are a separate issue and stay as placeholders here.

Layout source of truth is the founder's whiteboard sketch. The home page is ONE vertical story, centred in a 720px column on a dark canvas, read top to bottom:

1. Title "Pilot ships your tickets".
2. A fan of three ticket cards, then a GO button, then a down arrow.
3. A large "Pilot at work" illustration: a console window in front, a terminal window behind it offset to the top right (labelled Terminal), a status bar with tokens, minutes and cost. Then a down arrow.
4. A result card: "CI / Prod — Done / Green".
5. A grid of six feature cards, three per row, two rows.

Below the sketch, two short blocks keep Paddle's requirements: a pricing strip and a contact strip, then the footer from the scaffold. Everything is CSS and inline SVG built from the theme tokens: no screenshots, no raster images, no illustrations library, no gradients. Dark canvas, surface fills, hairline borders, Inter, the accent colour only on the GO button, the "running" arrow and the green check.

## Implementation

Build the home page from these components, one file each under a components/landing directory, composed in the home page in this order. Use the existing theme tokens through Tailwind classes (bg-canvas, bg-surface, bg-panel, bg-rail, border-hairline, text-ink, text-text-2, text-muted, text-accent, text-success). Pull URLs, the contact email and the plan facts from the site constants module created by the scaffold; the price string must come from the console plan constant, not be typed again.

1. Hero. Centred h1 "Pilot ships your tickets" (text-5xl on desktop, text-3xl on mobile, font-semibold, tracking-tight). One subtitle line in text-text-2: "Label an issue. Pilot plans it, implements it, opens the pull request and merges it on green." Below the subtitle, the TicketFan component: three ticket cards that overlap like a hand of cards (the left one rotated about minus 8 degrees and shifted down, the middle one upright and in front, the right one rotated about plus 8 degrees and shifted down). Each card is bg-surface, border-hairline, rounded-xl, about 220px wide, with a top row (a small muted label "#142" and a tiny pill "pilot" with a hairline border), a bold one-line title and two short muted lines. Titles: "fix(auth): refresh token rotation", "feat(api): rate limit per org", "chore(ci): cache bun installs". Under the fan, one GO button: a pill, bg-accent, text-canvas, font-semibold, uppercase letter-spaced text "GO", at least 44px tall, about 120px wide. It links to the console URL and carries aria-label "Open Pilot Console". Under the button a muted text link "or install the terminal version" to the id install on this page. Then a DownArrow component: a centred inline SVG arrow, 32px, stroke text-muted, with 40px of vertical padding.

2. PilotAtWork. A stage about 720px wide. Two overlapping windows:
   - Back window (Terminal): offset about 24px up and 24px right from the front window, bg-rail, border-hairline, rounded-xl, a title bar with three muted dots and the word "Terminal" in text-muted; its visible body shows two monospace lines in text-text-2: "$ pilot start --github" and "▸ picked up #142 · worktree ready". A small label to the right of the window, outside it, in text-muted with a short line pointing at it: "Terminal".
   - Front window (Console): bg-surface, border-hairline, rounded-xl, shadow-card. Inside: a left sidebar column (about 120px) with four muted bars of different lengths and a small dot at the top; a main area with a queue of three task rows (each a rounded-lg bg-panel block with a short bold line and a muted line: "#142 fix(auth): refresh token rotation" / "running · 3 min", "#139 feat(api): rate limit per org" / "queued", "#137 chore(ci): cache bun installs" / "PR open"); to the right of the first row a dashed-border rounded box (border-dashed border-accent, about 120 by 72px) labelled "worktree" in text-accent, with a curved inline SVG arrow in the accent colour from the first row into the dashed box. A bottom status bar across the front window, border-t border-hairline, monospace, text-muted, with three stats separated by middle dots: "123k tokens", "15 min", "USD 0.42".
   - Below the stage, one centred muted caption: "Console or terminal. Same engine." Then a DownArrow.

3. ResultCard. A centred card about 420px wide, bg-surface, border-hairline, rounded-xl, padded. First line in text-muted, small, uppercase letter-spaced: "CI / PROD". Second line, bold, text-xl, with a leading check mark SVG in text-success: "Done · Green". Two muted lines: "PR #143 merged after CI passed." and "Released v1.4.2 on the 16:00 train."

4. FeatureGrid. A heading row like the scaffold's Section header (h2 "What Pilot does", subtitle "Six things, no setup theatre."), then a grid, three columns on desktop, one column under 768px, six cards, each bg-surface, border-hairline, rounded-xl, p-6, a bold title and a two-line muted description:
   - Works with your tracker — GitHub, GitLab, Linear, Jira and Azure DevOps. Label an issue pilot and walk away.
   - Plans before it codes — Navigator reads your repo and writes the implementation plan first.
   - Never touches main — Each task runs in an isolated worktree, commits to a branch and opens a pull request.
   - Autopilot to merge — Watches CI, fixes failures, merges on green and cuts the release.
   - Every run metered — Tokens, minutes and cost per task, per project, per day.
   - Terminal or Console — Free in your terminal with your own key, or hosted with 100 tickets a month included.
   Give the sixth card the id install and a small inline code line "brew install pilot" in a bg-rail rounded block.

5. PricingStrip. Section id pricing. h2 "Pricing", subtitle "Two options. No trial, no tiers." Two cards side by side (one column on mobile): Terminal — big value "Free", lines "BSL 1.1 · your machine · your Claude key", a secondary button "Install" linking to the id install; Pilot Console — big value "USD 499" with "per month, per organisation" under it, lines "100 included tickets a month on Sonnet 5.5, metered at Anthropic list price with a hard cap", "Overage runs on your own Anthropic key, never a surprise invoice", "Web console, side chat, GitHub, Linear and Jira", "Cancel any time, effective at the end of the billing period", a primary button "Open Pilot Console" to the console URL. One muted line under the cards: "Payments are processed by Paddle, our merchant of record."

6. ContactStrip. Section id contact. h2 "Contact", subtitle "Reach a human." Three small cards in a row: Email (the contact email as a mailto link), GitHub (qf-studio/pilot, link to the GitHub URL), Discord (Join, link to the Discord URL). One muted line: "Sales, billing and security by email. Bugs and features on GitHub."

Header: add a "Contact" link to the id contact. Honour prefers-reduced-motion: no animation anywhere is acceptable; if a hover lift is added to cards it must be disabled under reduced motion. The ticket fan rotations are static transforms, not animations. The feature grid collapses to one column under 768px; the PilotAtWork stage scales down with the column and the back window may hide under 640px. No new dependencies.

Tests: one landing test file. It renders the home page and asserts: the h1 text; the GO link has aria-label "Open Pilot Console" and points at the console URL; the string "USD 499"; the string "100 included tickets"; exactly six feature cards; the "Done · Green" result text; the contact mailto link; the footer still has the three policy links.

## Acceptance

- `make build` passes and the exported home page is static HTML; paste the output into the PR body.
- `make test` passes including the landing test; paste the output into the PR body.
- `make lint` passes; paste the output into the PR body.
- change the console plan price constant to 299 -> the landing test named "shows the console price from the plan constant" fails
- remove one card from the feature grid -> the landing test named "renders six feature cards" fails
- The home page reads top to bottom: hero with ticket fan and GO, down arrow, Pilot at work stage, down arrow, result card, feature grid, pricing, contact. Ids present: hero, work, result, features, install, pricing, contact.
- The pricing strip renders "USD 499" exactly once and the string 499 appears nowhere else on the page.
- No raster images in the repository and none referenced from the home page; all drawings are CSS or inline SVG.
- Lighthouse mobile on the built home page scores performance 90 or more and accessibility 95 or more; paste the scores into the PR body.
- No new dependencies in the package manifest beyond what the scaffold added.

## Refs

- Pilot issue: https://github.com/qf-studio/pilotcloud-site/issues/2
- Plan: TASK-515 in the pilot repo (.agent/tasks/TASK-515-pilotcloud-landing-and-legal-pages.md)
- Scaffold: issue #1 in this repo
- Layout reference: founder whiteboard sketch 2026-10-09 (title → ticket fan + GO → arrow → console window with terminal behind, status bar "tokens · minutes · cost" → arrow → "CI/PROD DONE/GREEN" card → six feature cards)
- Plan facts: TASK-502 in the pilot repo (100 included tickets per month, hard cap, own-key overage); Paddle live price pri_01m4g870rh98m207cjwhjn8taq (USD 499 per month)
- Copy voice: direct, no superlatives, no exclamation marks

**Last Updated**: 2026-10-09
