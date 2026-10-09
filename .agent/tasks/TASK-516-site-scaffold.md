# feat(site): Next.js static-export scaffold with console theme tokens

**Status**: 🚀 Dispatched to Pilot 2026-10-09 (S0 of TASK-515; repo qf-studio/pilotcloud-site; label `pilot` + `no-decompose`)
**Created**: 2026-10-09
**Repo**: qf-studio/pilotcloud-site (private, empty except README.md)

## Context

pilotcloud.dev is the public marketing site for Pilot. It covers both the terminal version (open source, BSL 1.1) and Pilot Console (hosted). This repo is new and contains only a README. This issue is scaffold-only: the build, the design tokens, the page shell and the quality gates. No marketing copy, no legal text. Later issues add the landing sections and the policy pages.

The site is a static export served from S3 behind CloudFront, so every route must render to a static HTML file. The look must match the Pilot Console: dark canvas, bordered cards, Inter. The console's tokens are the single source of truth and are reproduced here verbatim.

## Implementation

Package manager is Bun. Framework is Next.js 15 with the app router and output set to export. Styling is Tailwind CSS v4 through the PostCSS plugin. Tests use Vitest with jsdom and Testing Library.

Create these files (plain names, all new):

- package.json with scripts: dev (next dev), build (next build), typecheck (tsc --noEmit), lint (next lint), test (vitest run --passWithNoTests). Commit the Bun lockfile.
- Makefile with targets build, test, lint that call the matching bun scripts (install first with bun install --frozen-lockfile). This is what the Pilot quality gates run.
- .pilot/workflow.yaml with quality gates build, test, lint mapped to make build, make test, make lint (same shape as the console-ui repo).
- .github/workflows/ci.yml: on push to main and on pull_request, two jobs (test: make build + make test; lint: make lint), oven-sh/setup-bun.
- next.config.ts with output export, trailingSlash true, images unoptimized.
- tsconfig.json (strict), postcss.config.mjs with the Tailwind v4 plugin, .gitignore (node_modules, .next, out).
- app/globals.css: import tailwindcss, then a :root block and a dark block with EXACTLY these custom properties and values. Dark is the default (apply on :root); the light values apply under prefers-color-scheme light.
  - dark: color-canvas #0b0c0e, color-surface #17191d, color-ink #eceef1, color-hairline #2b2e34, color-rail #101113, color-panel #131417, color-text-2 #b4b9c1, color-muted #868c96, color-accent #6fa1ff, color-primary-bg #e4e7eb, color-success #4ade80, color-warning #fbbf24, color-error #f87171, color-info #6fa1ff, color-chart-1 #eceef1, color-chart-2 #9099a6, color-chart-3 #454a52
  - light: color-canvas #fafafa, color-surface #ffffff, color-ink #141821, color-hairline #e7e8ea, color-rail #f7f7f6, color-panel #f6f6f5, color-text-2 #5f6570, color-muted #9aa0a8, color-accent #2e6be6, color-primary-bg #181c24, color-success #187a4e, color-warning #8a5a06, color-error #b3423a, color-info #2e6be6, color-chart-1 #141821, color-chart-2 #8a909b, color-chart-3 #d4d7dc
  - shared: font-sans "Inter", system-ui, -apple-system, "Segoe UI", sans-serif; spacing 4px; max-width-content 1140px; shadow-card 0 1px 2px rgba(20,24,33,0.06), 0 0 0 1px rgba(20,24,33,0.05)
  - Expose them to Tailwind through an @theme block (colors canvas, surface, ink, hairline, rail, panel, text-2, muted, accent, primary-bg; font sans) so classes like bg-surface and text-ink work.
- app/layout.tsx: html lang en, Inter via next/font/google with display swap, body uses bg-canvas text-ink font-sans antialiased; renders SiteHeader, children, SiteFooter. Metadata: metadataBase https://pilotcloud.dev, title default "Pilot — AI that ships your tickets", template "%s | Pilot", description "Navigator plans. Pilot executes. Run it in your terminal or in Pilot Console.".
- components/site-header.tsx: sticky top bar, max-w-[1140px] centered, left wordmark "Pilot" (text link to /), right links Docs (https://pilot.quantflow.studio), GitHub (https://github.com/qf-studio/pilot), and a pill button "Open Console" to https://console.pilotcloud.dev with hairline border, rounded-xl, surface background.
- components/site-footer.tsx: hairline top border, two rows. Row 1 links: Terms (/terms), Privacy (/privacy), Refunds (/refunds), Docs, GitHub, Discord (https://discord.gg/Hsz63MTB3c). Row 2: "© 2026 Pilot" in text-muted. The three policy links are internal Next links.
- components/section.tsx: the reusable layout primitive used by every landing section. Props: title, subtitle, action (optional ReactNode rendered right-aligned in the header row), cards (optional array of up to three { label, value, hint? }), children (rendered inside one full-width bordered panel). Markup: section with max-w-[1140px] mx-auto px-6 py-16; header row flex justify-between items-start; h2 text-3xl font-semibold; subtitle text-text-2 mt-1; card row grid grid-cols-1 md:grid-cols-3 gap-4 mt-8; each card rounded-2xl border border-hairline bg-surface p-6 with label text-text-2 text-sm and value text-4xl font-semibold; panel rounded-2xl border border-hairline bg-surface p-6 mt-4 with an optional panelTitle (text-xl font-semibold mb-4).
- lib/site.ts: exported constants siteUrl, consoleUrl, docsUrl, githubUrl, discordUrl, contactEmail (value hello@quantflow.studio), plans: terminal (name "Terminal", price "Free", note "BSL 1.1 · your Claude key") and console (name "Pilot Console", priceUsdMonthly 499, note "USD 499 / month · no trial"). Put a source comment next to priceUsdMonthly: Paddle price id pri_01m4g870rh98m207cjwhjn8taq.
- app/page.tsx: one Section titled "Pilot" with subtitle "Scaffold. Landing sections arrive in the next issue." and one placeholder card row (Terminal / Console / Both) and an empty panel. No marketing copy yet.
- app/terms/page.tsx, app/privacy/page.tsx, app/refunds/page.tsx: each renders a page title (Terms of Service / Privacy Policy / Refund Policy) and the single line "This page is being prepared." inside a Section panel. Metadata title per page.
- app/robots.ts (allow all, sitemap at /sitemap.xml) and app/sitemap.ts listing /, /terms, /privacy, /refunds.
- tests/footer.test.tsx: one test named "renders the three policy links" that renders SiteFooter and asserts links with href /terms, /privacy and /refunds exist.
- tests/section.test.tsx: one test named "renders three cards and the title" that renders Section with a three-card fixture and asserts the three card values and the h2 title render.
- vitest.config.ts with jsdom environment and the React plugin; vitest setup file for jest-dom matchers.
- README.md: replace the generated README with a short one: what the site is, bun install, bun run dev, make build/test/lint, static output in the out directory.

Do not add analytics, cookie banners, a CMS, MDX, or any marketing copy. Do not add a deploy workflow (separate issue). Keep dependencies to next, react, react-dom, tailwindcss, @tailwindcss/postcss, typescript, vitest, jsdom, @testing-library/react, @testing-library/jest-dom, @vitejs/plugin-react, eslint config from next.

## Acceptance

- `make build` passes and writes out/index.html, out/terms/index.html, out/privacy/index.html and out/refunds/index.html; paste the output into the PR body.
- `make test` passes with the two test files; paste the output into the PR body.
- `make lint` passes; paste the output into the PR body.
- remove the Refunds link from the footer component -> the footer test named "renders the three policy links" fails
- drop the third card from the fixture in the section test -> the section test named "renders three cards and the title" fails
- app/globals.css contains the exact dark value color-surface #17191d and the exact light value color-surface #ffffff.
- The CI workflow file exists with the two jobs and the Makefile has the three targets.
- The exported out directory contains no localhost or 127.0.0.1 strings.

## Refs

- Pilot issue: https://github.com/qf-studio/pilotcloud-site/issues/1

- Plan: TASK-515 in the pilot repo (.agent/tasks/TASK-515-pilotcloud-landing-and-legal-pages.md)
- Theme tokens source: pilot-console-ui, src/design-system/theme.css (copied verbatim above)
- Gate shape source: pilot-console-ui, .pilot/workflow.yaml and Makefile
- Layout reference: the console Usage page (section title + subtitle, three bordered cards, one bordered panel)

**Last Updated**: 2026-10-09
