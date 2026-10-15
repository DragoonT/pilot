# Learning: Founder tenant org 425f9f99 (instance 404746db, EC2 i-0289111000cebcee9, provisi

## Summary
Founder tenant org 425f9f99 (instance 404746db, EC2 i-0289111000cebcee9, provisioned 2026-09-25) has the pre-TASK-502 SSM layout: /tenants/<org>/ holds ANTHROPIC_API_KEY, GITHUB_TOKEN, PILOT_GATEWAY_TOKEN only, no PILOT_ANTHROPIC_KEY_SOURCE and no _PLATFORM/_OWN pair. fetch-secrets.sh therefore writes no key source into /run/pilot/env, the daemon records key_source=unknown on every execution and chat turn, and the console meter (usage_meter.go, FILTER key_source='platform') counts nothing for this org. Tenants provisioned 10-07 (Testica b79d7a56) and 10-08 (19135877) have the full layout. Verified 2026-10-15 via SSM parameter names + ticket_ledger rows. Fix is operator-side: add PILOT_ANTHROPIC_KEY_SOURCE (and the key pair) for that org or re-push its config; not a code defect. Also: ticket_ledger ingest proven end to end 12:55Z (4 execution + 1 chat_turn rows) after console#411.

## Context
Discovered during development.

## Details
Founder tenant org 425f9f99 (instance 404746db, EC2 i-0289111000cebcee9, provisioned 2026-09-25) has the pre-TASK-502 SSM layout: /tenants/<org>/ holds ANTHROPIC_API_KEY, GITHUB_TOKEN, PILOT_GATEWAY_TOKEN only, no PILOT_ANTHROPIC_KEY_SOURCE and no _PLATFORM/_OWN pair. fetch-secrets.sh therefore writes no key source into /run/pilot/env, the daemon records key_source=unknown on every execution and chat turn, and the console meter (usage_meter.go, FILTER key_source='platform') counts nothing for this org. Tenants provisioned 10-07 (Testica b79d7a56) and 10-08 (19135877) have the full layout. Verified 2026-10-15 via SSM parameter names + ticket_ledger rows. Fix is operator-side: add PILOT_ANTHROPIC_KEY_SOURCE (and the key pair) for that org or re-push its config; not a code defect. Also: ticket_ledger ingest proven end to end 12:55Z (4 execution + 1 chat_turn rows) after console#411.

## Recommended Approach
Apply this knowledge when working on related topics.

## Related
- None documented

---
**Captured**: 2026-10-15
**Confidence**: 95%
**Concepts**: usage-ledger, ssm, tenant-provisioning, allowance, key-source
