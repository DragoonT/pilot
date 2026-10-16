# chore(console-api): add the InviteBaseUrl parameter and PILOT_CONSOLE_INVITE_BASE_URL env so org invites are enabled in prod

**Status**: 📨 FILED 2026-10-16 → [https://github.com/qf-studio/aws-infrastructure-pilot/issues/21](https://github.com/qf-studio/aws-infrastructure-pilot/issues/21) — assigned to the founder (repo not registered with Pilot; Nelya may take it)
**Created**: 2026-10-16
**Repo**: qf-studio/aws-infrastructure-pilot

Blocked by: none

## Context

pilot-console PR #406 (issue #404, merged 2026-10-16 10:49Z) added org member invites. The console API only enables them when both an email transport and `PILOT_CONSOLE_INVITE_BASE_URL` are configured (`invitesEnabled()` in the orgs handler); otherwise `POST /api/v1/org/members/invites` answers 503. The console-api task definition is rendered from `stacks/pilot-fleet/services/console-api.yml` in this repo (synced to `s3://pilot-fleet-s3-app-data/templates/pilot-fleet/console-api.yml` by the infra pipeline, then deployed by pilot-console's deploy workflow with `aws cloudformation deploy`). The template has the email parameters (`EmailEnabled`, `EmailFrom`, env `PILOT_CONSOLE_EMAIL_*`) but nothing for the invite base URL, so prod has no such variable today (checked on task definition revision 53). The accept link the console emails is `<base>/accept-invite?token=…`; the console UI origin is `https://console.pilotcloud.dev`. The UI page for that link is a separate pilot-console-ui issue.

## Scope

- In `stacks/pilot-fleet/services/console-api.yml`, add a parameter after `EmailFrom`:
  - `InviteBaseUrl`, Type String, Default `https://console.pilotcloud.dev`, Description "PILOT_CONSOLE_INVITE_BASE_URL — console-ui origin the org-invite accept link points at; empty disables invites (POST /api/v1/org/members/invites answers 503)".
- In the container's environment list, right after `PILOT_CONSOLE_EMAIL_FROM`, add `PILOT_CONSOLE_INVITE_BASE_URL` with `Value: !Ref InviteBaseUrl`.
- No workflow change: the pilot-console deploy workflow omits parameters it does not override, and `aws cloudformation deploy` then takes a new parameter's default.
- Let the infra pipeline sync the template to S3; the next pilot-console release deploys it.

## Acceptance

- `aws cloudformation validate-template --template-body file://stacks/pilot-fleet/services/console-api.yml` succeeds; paste the output into the PR body.
- After the next console-api deploy, the active task definition's environment contains `PILOT_CONSOLE_INVITE_BASE_URL` with value `https://console.pilotcloud.dev`.
- `POST /api/v1/org/members/invites` from an owner session answers 201 (not 503).

## Out of scope

- The accept page in pilot-console-ui (separate issue).
- Any other console-api parameter.

## Refs

- `stacks/pilot-fleet/services/console-api.yml` (Parameters: EmailEnabled, EmailFrom; env block PILOT_CONSOLE_EMAIL_*)
- pilot-console PR #406, issue #404; pilot-console deploy workflow deploy-quantflow-aws.yml (TEMPLATE_BASE, parameter-overrides)
- Issue: https://github.com/qf-studio/aws-infrastructure-pilot/issues/21
