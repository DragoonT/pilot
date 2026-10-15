# fix(orgs): write PILOT_ANTHROPIC_KEY_SOURCE=own when a customer saves an Anthropic key and no pool key is lent, so legacy orgs stop being metered as unknown

**Status**: ✅ MERGED 2026-10-15 15:58Z → [console#413](https://github.com/qf-studio/pilot-console/issues/413) → [PR#414](https://github.com/qf-studio/pilot-console/pull/414) (recovery PR from Pilot's preserved `b6acaba`; executor ended its turn with a background test running, 2nd instance today). Reviewer verified before opening: build + vet clean, 16/16 `TestHandlePutCredential*` PASS against Postgres, both pins kill (evidence in the PR body). Autopilot merged on green at 1c7e01ce1. Founder tenant already fixed by hand; new own-key saves now write the selector themselves.
**Created**: 2026-10-15
**Repo**: qf-studio/pilot-console

Blocked by: none

## Context

`putCredentialSecret` in `internal/orgs/handlers.go` (TASK-502 leg 1a) writes a saved Anthropic key to `ANTHROPIC_API_KEY_OWN`, and also to the legacy `ANTHROPIC_API_KEY` when the org has no assigned platform key. It never writes the selector `PILOT_ANTHROPIC_KEY_SOURCE`. The selector is written in two places only: `PlatformKeyAssigner.Assign` in `internal/fleet/platformkey.go` writes `platform` (or `own` inside a switched period), and `resumeAllowanceSuspended` in `internal/orgs/handlers.go` writes `own` after an allowance suspension. An org that was provisioned before TASK-502 and runs on its own key therefore has no selector at all. The tenant box dumps the SSM path into its env file, the daemon reads `PILOT_ANTHROPIC_KEY_SOURCE` for every execution and chat turn, and with no value it records `key_source=unknown`. The usage meter in `internal/fleet/usage_meter.go` sums `estimated_usd_cents` over `key_source='platform'` rows only, so such an org is never metered, and its ledger rows cannot be told apart from a misconfigured pool key. Observed 2026-10-15 on the founder tenant (org `425f9f99`, provisioned 09-25): every `ticket_ledger` row was `unknown` until an operator wrote the selector by hand; the next chat turn then recorded `own`. The daemon's `KeySourceFromEnv` and the box's `fetch-secrets.sh` selector block already handle `own` correctly; only the console write is missing.

## Scope

- `internal/orgs/handlers.go`, `putCredentialSecret`: in the no-platform-key branch (the existing `writeLegacy` case), after the two key writes, also `Put` `secrets.KeyAnthropicKeySource` with the value `keySourceOwn`. Keep the write order: `ANTHROPIC_API_KEY_OWN`, then legacy `ANTHROPIC_API_KEY`, then the selector last, so a failure between writes never leaves a selector that names an absent key. When a platform key is assigned, do not touch the selector; `Assign` owns it.
- The handler already calls `refreshInstanceConfig` after the put. That config push re-runs `fetch-secrets.sh` on the box and restarts the daemon when the env hash changes, so the selector goes live without a second code path. No change there.
- `internal/orgs/handlers_test.go`: update `TestHandlePutCredential_AnthropicBothKeysWithoutPlatformKey` to expect three writes with the selector `own` last. Add `TestHandlePutCredential_SelectorNotWrittenWithPlatformKey`: with a platform key assigned, exactly one write (`ANTHROPIC_API_KEY_OWN`) and no selector write. Add `TestHandlePutCredential_SelectorWriteFailureIsReturned`: the fake writer fails on the selector key, the handler returns the error and the response is not 200.
- Update the function comment on `putCredentialSecret` to name the selector write and its condition.

## Acceptance

- `go build ./...` passes; paste the output into the PR body.
- `go vet ./internal/orgs/` passes; paste the output into the PR body.
- `go test ./internal/orgs/ -run 'TestHandlePutCredential' -count=1 -v` prints `--- PASS` for every `TestHandlePutCredential_*` test, including the two new ones; paste the `--- PASS` lines into the PR body.
- `internal/orgs/handlers.go` contains exactly one `secrets.KeyAnthropicKeySource` write inside `putCredentialSecret`, in the no-platform-key branch.
- Pin: remove the selector write from `putCredentialSecret` -> `TestHandlePutCredential_AnthropicBothKeysWithoutPlatformKey` fails on the write count.
- Pin: write the selector unconditionally -> `TestHandlePutCredential_SelectorNotWrittenWithPlatformKey` fails.

## Out of scope

- A backfill for existing legacy orgs (one org today; fixed by hand).
- The daemon side (`KeySourceFromEnv`) and the box fetch script; both already honour `own`.
- The meter SQL.

## Refs

- `internal/orgs/handlers.go` (putCredentialSecret, resumeAllowanceSuspended, refreshInstanceConfig), `internal/orgs/handlers_test.go`, `internal/fleet/platformkey.go` (Assign, KeySource), `internal/secrets/writer.go` (KeyAnthropicKeySource), `internal/fleet/usage_meter.go`
- Predecessor: [TASK-558](archive/TASK-558-console-ledger-first-poll-sends-since.md); memory `founder-tenant-legacy-ssm-layout-key-source-unknown-unmetered`
- Pilot issue: https://github.com/qf-studio/pilot-console/issues/413
