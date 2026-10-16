# feat(invites): accept-invite page — land the emailed link, join the org, and show expired / wrong-email / already-in-an-org states

**Status**: ✅ MERGED 2026-10-16 11:13Z → [ui#235](https://github.com/qf-studio/pilot-console-ui/issues/235) → [PR#236](https://github.com/qf-studio/pilot-console-ui/pull/236) (ddbd556dd), reviewed APPROVE-w-notes pre-merge (3/3 pins kill). The UI deploys on its release train. End-to-end invites still wait on infra#21 (TASK-565: `PILOT_CONSOLE_INVITE_BASE_URL`), then one smoke invite.
**Created**: 2026-10-16
**Repo**: qf-studio/pilot-console-ui

Blocked by: none (the console API side is on main; the prod env var is a separate infra change)

## Context

pilot-console PR #406 (issue #404) added org invites: an owner invites an email from the Members page (ui PR #232 already ships invite, revoke and remove), the console emails a link `<console origin>/accept-invite?token=…`, and the invitee joins through `POST /api/v1/org/members/invites/{token}/accept`. The UI has no page for that link: `src/router/index.ts` has no `/accept-invite` route and `src/lib/api/adapter.ts` has no accept call, so the link opens a 404 today. The accept endpoint needs a session (the API authenticates it) and answers 404 for an unknown, revoked or already-accepted token, 410 for an expired one, 403 when the session email is not the invited one, 409 when the caller already belongs to an organisation, and 200 with the member row on success. Two router rules matter: an unauthenticated visitor is bounced to `login` with `redirect` set to the full path (`router.beforeEach` in `src/router/index.ts`), and an authenticated user without an org is bounced to `onboarding` — which is exactly the invitee's state, so the accept route must be exempt from that second bounce. `src/views/VerifyEmailView.vue` is the model: it reads `token` off the query, calls the adapter once per distinct token, never retries automatically, and renders one state per outcome.

## Scope

- `src/lib/api/adapter.ts`: add `acceptInvite(token: string): Promise<OrgMember>`. `src/lib/api/httpAdapter.ts`: `POST /api/v1/org/members/invites/{encodeURIComponent(token)}/accept`, map the wire member row like `inviteMember` does; non-2xx passes through as `ApiError` (`src/lib/api/errors.ts`) with its status. `src/lib/api/mockAdapter.ts`: a deterministic implementation (one known token joins, `expired-…` tokens throw 410, `wrong-…` 403, `taken-…` 409, anything else 404).
- `src/router/index.ts`: route `/accept-invite`, name `accept-invite`, lazy view, `meta: { blank: true }`. It is NOT public (the API needs a session), so the existing guard sends a logged-out visitor to `login` with `redirect` — keep that. Exempt `accept-invite` from the "authenticated but no org → onboarding" bounce, the way the email-change pages are exempt from the logged-in bounce.
- New view AcceptInviteView.vue under src/views, modeled on VerifyEmailView.vue: states `missing` (no token), `working`, `joined`, `expired` (410), `wrong-email` (403, show the session email and a sign-out link), `already-member` (409, link to `/`), `invalid` (404), `error` (anything else). On `joined`: call `auth.bootstrap()` so the store picks up the new org, then offer a "Go to the console" link to `/`. Never auto-retry; a `route.query.token` watcher re-runs for a different token.
- Specs: AcceptInviteView.spec.ts under src/views/__tests__ (one case per state via a mocked adapter; `joined` asserts `bootstrap` was called once and the success copy renders; `missing` never calls the adapter). Router spec in `src/router/__tests__/index.spec.ts`: an org-less authenticated session on `/accept-invite?token=x` is not redirected to onboarding; a logged-out visitor is redirected to `login` with `redirect=/accept-invite?token=x`.

## Acceptance

- `bun run build` passes; paste the output into the PR body.
- `bun run test` passes; paste the output into the PR body. The output must list AcceptInviteView.spec.ts with all state cases and the two new router cases.
- The router has exactly one route named `accept-invite`, and the onboarding bounce in `router.beforeEach` exempts it.
- Mutation pin: remove the `accept-invite` exemption from the onboarding bounce -> the org-less router case fails.
- Mutation pin: map 410 to the `invalid` state -> the `expired` case fails.
- Mutation pin: skip `auth.bootstrap()` after a successful accept -> the `joined` case fails.

## Out of scope

- The Members page (shipped in ui PR #232).
- The prod env var `PILOT_CONSOLE_INVITE_BASE_URL` (infra issue).
- Registration flow changes: an invitee without an account registers, verifies, logs in; the login `redirect` brings them back to the link.

## Refs

- `src/router/index.ts` (beforeEach guard), `src/views/VerifyEmailView.vue`, `src/views/__tests__/VerifyEmailView.spec.ts`, `src/lib/api/adapter.ts`, `src/lib/api/httpAdapter.ts`, `src/lib/api/mockAdapter.ts`, `src/lib/api/errors.ts`, `src/stores/auth.ts` (bootstrap), `src/router/__tests__/index.spec.ts`
- Contract: pilot-console repo, orgs package, file invites_handlers.go, handleAcceptInvite (404 / 410 / 403 / 409 / 200); PR #406
- Pilot issue: https://github.com/qf-studio/pilot-console-ui/issues/235
