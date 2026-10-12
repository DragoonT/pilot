# Pitfall: pilot-console CI job 'Check Wire-Contract Tests' (scripts/check-wire-contract-te

## Summary
pilot-console CI job 'Check Wire-Contract Tests' (scripts/check-wire-contract-tests.sh) fails any PR that adds or changes a json-tagged field in a handler/DTO struct unless a test in the SAME package reads rec.Body.String() and then asserts strings.Contains(...) naming the field inside one test function; fake-gateway request assertions and bytes.Equal relays do not count. Console PR#388 (TASK-524, 2026-10-12) was held by autopilot for this. Every console spec that adds a JSON field must name a Test<Handler>_<Field>JSON with that exact shape and add 'make check-wire-contract-tests passes; paste the output' as an acceptance bullet.

## Context
Discovered during development.

## Details
pilot-console CI job 'Check Wire-Contract Tests' (scripts/check-wire-contract-tests.sh) fails any PR that adds or changes a json-tagged field in a handler/DTO struct unless a test in the SAME package reads rec.Body.String() and then asserts strings.Contains(...) naming the field inside one test function; fake-gateway request assertions and bytes.Equal relays do not count. Console PR#388 (TASK-524, 2026-10-12) was held by autopilot for this. Every console spec that adds a JSON field must name a Test<Handler>_<Field>JSON with that exact shape and add 'make check-wire-contract-tests passes; paste the output' as an acceptance bullet.

## Recommended Approach
Apply this knowledge when working on related topics.

## Related
- None documented

---
**Captured**: 2026-10-12
**Confidence**: 90%
**Concepts**: issue-authoring, testing, pilot-console, ci, wire-contract
