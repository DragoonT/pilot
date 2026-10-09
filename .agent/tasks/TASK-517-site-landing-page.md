# feat(site): landing page — hero, terminal vs console, how it works, pricing, FAQ, contact

**Status**: 🚀 Dispatched to Pilot 2026-10-09 (S1 of TASK-515; repo qf-studio/pilotcloud-site; labels `pilot` + `no-decompose`)
**Created**: 2026-10-09
**Repo**: qf-studio/pilotcloud-site

Blocked by: #1

## Context

The scaffold (issue #1) gives this repo the static-export build, the console theme tokens, the Section and card primitives, the header and the footer. This issue fills the home page. The page covers both ways to run Pilot: the terminal version (open source under BSL 1.1, installed with Homebrew, runs on the user's own Claude key) and Pilot Console (hosted, one plan, USD 499 per month). Legal pages are a separate issue and stay as placeholders here.

Visual rule, from the founder's reference (the console Usage page): every section is a title plus a one-line subtitle, then a row of three bordered cards, then one full-width bordered panel. Dark canvas, hairline borders, Inter, one accent colour. No gradients, no illustrations, no stock imagery. Use the Section primitive from the scaffold for every section; do not invent a second layout.

## Implementation

Replace the placeholder home page with these sections in this order. All copy below is final unless marked optional. Pull URLs, the contact email and the plan facts from the site constants module created by the scaffold; the price string must come from the console plan constant, not be typed again.

1. Hero (Section without cards, with the panel). Title: "AI that ships your tickets". Subtitle: "Navigator plans. Pilot executes. Run it in your terminal or let Pilot Console run it for you." Action slot: two buttons, "Install the terminal version" (link to the Install card anchor on this page) and "Open Pilot Console" (link to the console URL, accent style). Panel: a mock terminal block (monospace, rail background, hairline border) that shows these four lines verbatim:
   - brew install pilot
   - pilot start --github
   - picked up #142 fix(auth): refresh token rotation
   - PR #143 opened, CI green, auto-merged
   Below the block, one line in text-2: "Pilot watches your issue tracker, implements labeled tickets with Claude Code, opens the pull request and merges it when CI is green."

2. Two ways to run Pilot. Subtitle: "Same engine. Pick where it runs." Cards: Terminal (value "Free", hint "BSL 1.1 · your machine · your Claude key"); Console (value "USD 499 / month", hint "Hosted box per organisation · dashboard · billing by Paddle"); Both (value "One engine", hint "Same executor, same Navigator planning, same autopilot"). Panel title "What is different". Panel body: a two-column comparison table with rows Where it runs (your laptop or server / a managed box we operate), Who pays Anthropic (you, your key / included monthly ticket volume, then your key), Setup (brew install, one config file / sign in, connect GitHub), Dashboard (terminal UI / web console with usage, cost and side chat), Updates (pilot upgrade / rolled out for you), Support (GitHub issues and Discord / email support).

3. How it works. Subtitle: "A ticket goes in. A merged pull request comes out." Cards: Navigator plans (value "1", hint "Reads your repo, writes the implementation plan"); Pilot executes (value "2", hint "Runs Claude Code in an isolated worktree, commits, opens the PR"); Autopilot merges (value "3", hint "Watches CI, fixes failures, merges on green, cuts the release"). Panel title "Pipeline". Panel body: an inline SVG flow, left to right: Issue → Navigator → Pilot → Pull request → CI → Merge. Boxes use surface fill and hairline stroke, arrows use the muted colour, labels use the ink colour. Below the SVG, three short lines: "Works with GitHub, GitLab, Linear, Jira and Azure DevOps." · "Label an issue pilot and walk away." · "Every run is logged with tokens and cost."

4. Pricing. Subtitle: "Two options. No trial, no tiers." Cards: Terminal (value "Free", hint "Open source, BSL 1.1"); Pilot Console (value "USD 499", hint "per month, per organisation"); Included (value "100 tickets", hint "per month on Sonnet 5.5, then your own key"). Panel title "What the Console plan includes". Panel body, a bullet list: a managed Pilot box for your organisation; 100 included tickets per month, metered at Anthropic list price with a hard cap, overage runs on your own Anthropic key, never a surprise invoice; web console with queue, usage, cost per day and a side chat to your box; GitHub, Linear and Jira connections; email support; cancel any time, effective at the end of the billing period. Last line: "Payments are processed by Paddle, our merchant of record." and a button "Open Pilot Console" to the console URL.

5. FAQ (Section without cards). Subtitle: "Short answers." Panel: six question and answer pairs rendered as a definition list (question in ink, answer in text-2):
   - Is the terminal version really free? Yes. Pilot is source-available under the Business Source License 1.1. You pay Anthropic for the tokens your runs use.
   - What do I need for the terminal version? A machine with Git, a Claude subscription or API key, and a GitHub, GitLab, Linear, Jira or Azure DevOps project.
   - What happens when the 100 included tickets are used? The box switches to your own Anthropic key for the rest of the month. If no key is set, dispatch pauses until the period resets.
   - Does Pilot push to my main branch? No. Pilot works on a branch, opens a pull request and merges only when your CI is green and your merge rules allow it.
   - Where does Pilot Console run? On AWS in the EU (Frankfurt). Each organisation gets its own box.
   - Can I cancel? Yes, any time. The subscription ends at the close of the current period. See the refund policy.

6. Contact. Subtitle: "Reach a human." Cards: Email (value the contact email, as a mailto link); GitHub (value "qf-studio/pilot", link to the GitHub URL); Discord (value "Join", link to the Discord URL). Panel: one paragraph: "For sales, billing or security questions email us. For bugs and feature requests open an issue on GitHub. For everything else, Discord." Give the section id "contact" and link to it from the header.

Component rules: one new component per section under a components/landing directory, each built only from the Section primitive plus plain elements. Add an id to each section (hero, run, how, pricing, faq, contact) and an "Install" anchor on the terminal card. Honour prefers-reduced-motion (no animation at all is acceptable). Mobile first: the card grid collapses to one column under 768px; the comparison table scrolls horizontally on small screens. No new dependencies.

Tests: one test file per section is not required; one landing test file is. It renders the home page and asserts: the hero title text; the string "USD 499"; the string "100 tickets"; six FAQ questions; the three policy links in the footer are still present; the contact section exists with the mailto link.

## Acceptance

- `make build` passes and the exported home page is static HTML; paste the output into the PR body.
- `make test` passes including the landing test; paste the output into the PR body.
- `make lint` passes; paste the output into the PR body.
- change the console plan price constant to 299 -> the landing test named "shows the console price from the plan constant" fails
- remove the FAQ section from the home page -> the landing test named "renders six FAQ entries" fails
- The home page has exactly six top-level sections with ids hero, run, how, pricing, faq, contact in that order.
- The pricing section renders "USD 499" exactly once and the string 499 appears nowhere else on the page.
- Lighthouse mobile on the built home page scores performance 90 or more and accessibility 95 or more; paste the scores into the PR body.
- No new dependencies in the package manifest beyond what the scaffold added.

## Refs

- Pilot issue: https://github.com/qf-studio/pilotcloud-site/issues/2

- Plan: TASK-515 in the pilot repo (.agent/tasks/TASK-515-pilotcloud-landing-and-legal-pages.md)
- Scaffold: issue #1 in this repo
- Plan facts: TASK-502 in the pilot repo (100 included tickets per month, hard cap, own-key overage); Paddle live price pri_01m4g870rh98m207cjwhjn8taq (USD 499 per month)
- Layout reference: the console Usage page (section title + subtitle, three bordered cards, one bordered panel)
- Copy voice: direct, no superlatives, no exclamation marks

**Last Updated**: 2026-10-09
