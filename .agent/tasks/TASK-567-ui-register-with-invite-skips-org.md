# fix(invites): a visitor who arrives with an invite registers without an organisation, so the accept does not 409

**Status**: 🚀 Dispatched to Pilot 2026-10-16 → [https://github.com/qf-studio/pilot-console-ui/issues/237](https://github.com/qf-studio/pilot-console-ui/issues/237)
**Created**: 2026-10-16
**Repo**: qf-studio/pilot-console-ui

Blocked by: none

## Context

Org invites are live end to end (console PR #406, ui PR #236, infra PR #22): the owner invites an address, the console emails `<origin>/accept-invite?token=…`, and the page calls `POST /api/v1/org/members/invites/{token}/accept`. The first real smoke on 2026-10-16 stopped at registration: `src/views/RegisterView.vue` requires an Organisation name and its one submit does `auth.register` then `auth.createOrg` (the onboarding-v1 design). The console allows one organisation per user (`UNIQUE(user_subject)` on `org_members`), so an invitee who registers this way owns a fresh organisation and the accept answers 409 "already belongs to an organisation". There is no organisation-delete route to undo it. The login page already carries a `redirect` query and validates it (`safeRedirect` in `src/views/LoginView.vue`: must start with `/` and not `//`); the router guard sends a logged-out visitor on `/accept-invite` to `login` with `redirect=/accept-invite?token=…`, and `/accept-invite` is exempt from the "no org → onboarding" bounce (ui #235). The missing piece is the registration branch of that path.

## Scope

- `src/views/LoginView.vue`: the "Sign up" link to `/register` (line with `RouterLink ... to="/register"`) carries the current `redirect` query through unchanged.
- `src/views/RegisterView.vue`: invite mode when `route.query.redirect` is a string that passes the same safety rule as `safeRedirect` and starts with `/accept-invite`. In invite mode: the Organisation field is not rendered and its `required` validator is not applied; the submit calls `auth.register` only (no `createOrg`), then `router.push(redirect)`. Outside invite mode nothing changes (register → createOrg → `/onboarding`). Show a one-line note above the form in invite mode: "You're joining an existing organisation."
- `src/views/OnboardingView.vue`: one line under the create-organisation form, "Have an invite? Open the link from your email." No logic.
- Specs: `src/views/__tests__/RegisterView.spec.ts` — invite mode hides the Organisation field, calls `register` once and `createOrg` never, and pushes to the redirect; a `redirect` that fails the safety rule (for example `//evil.example/accept-invite` or `/billing`) falls back to normal mode; normal mode still calls `createOrg`. `src/views/__tests__/LoginView.spec.ts` — the create-account link preserves `redirect`.

## Acceptance

- `bun run build` passes; paste the output into the PR body.
- `bun run test` passes; paste the output into the PR body. The output must list RegisterView.spec.ts and LoginView.spec.ts with the new cases.
- Mutation pin: call `createOrg` in invite mode too -> the invite-mode RegisterView case fails.
- Mutation pin: accept any `redirect` string as invite mode -> the unsafe-redirect case fails.
- Mutation pin: drop the `redirect` query from the create-account link -> the LoginView case fails.

## Out of scope

- Any console API change; the accept endpoint already works for an org-less user.
- Carrying `redirect` across email verification; registration establishes the session directly, so the push to the redirect happens right after register.

## Refs

- `src/views/RegisterView.vue`, `src/views/LoginView.vue` (safeRedirect), `src/views/OnboardingView.vue`, `src/router/index.ts` (guard), `src/views/AcceptInviteView.vue`, `src/views/__tests__/RegisterView.spec.ts`, `src/views/__tests__/LoginView.spec.ts`
- Prior leg: ui #235 / PR #236; contract: console PR #406
- Pilot issue: https://github.com/qf-studio/pilot-console-ui/issues/237
