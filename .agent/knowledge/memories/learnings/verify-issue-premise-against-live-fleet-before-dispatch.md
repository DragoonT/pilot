---
name: verify-issue-premise-against-live-fleet-before-dispatch
description: console#390 was written on a premise the train fixed the same day (GH-5651 headless self-upgrade, v2.282.0) — before dispatching a planning-era issue, check the release tag of any related fix and read the live tenant over SSM; the check shrank #390 to version visibility and surfaced the real gap, a golden AMI older than the self-upgrade fix
type: learning
---

# Verify an issue's premise against the live fleet before dispatching it

**What happened (2026-10-20):** console#390 (filed 10-13, "train never reaches
tenants", desired-version pin + console-pushed SSM binary rollout) was about to
be labeled `pilot`. nav-research on the console code found `RunAMIRollout` has
no production caller and nothing records a tenant version. Two cheap checks
then killed the premise: pilot GH-5651 (headless self-upgrade) merged the same
day #390 was filed (PR#5654, first tag **v2.282.0**), and the tenant
`i-0289111000cebcee9` showed `Pilot 2.289.0` with a journal line
"upgrade verified complete from=2.288.1 to=v2.289.0 via hot restart" at
10-19 14:06Z. Founder decision 10-13 also stood: daemon self-upgrade is the
tenant path. #390 was re-titled and re-scoped to **observed version per tenant**
(read `/health` in the existing ready probe → `observed_pilot_version` →
`consolectl status` VERSION → floor warning).

**Real gap found by the same check:** the reconciler task definition
(`pilot-fleet-console-reconciler`) launches `ami-06825978577ce40d4`
(`pilot-agent-20261007-145025`, bakes pilot **2.277.4**) and sets no
`PILOT_CONSOLE_FLEET_BINARY_S3_URI`. 2.277.4 < 2.282.0, so a tenant
provisioned today boots a daemon whose self-upgrade is still dashboard-gated
and stays there until an operator SSM swap. Fix = golden AMI refresh in
`aws-infrastructure-pilot` (bake workflow inputs `pilot_version`,
`pilot_binary_s3_uri`), or the S3 override — infra issue, not console code.

## Rules
- Before `pilot`-labeling an issue older than a few days: `gh issue view`
  any "Blocked by"/related pilot issues → if closed, `git tag --contains
  <merge sha>`; then read the live tenant (`pilot version`, `journalctl -u
  pilot | grep -i upgrade`) over SSM. Five minutes; it changes the scope.
- An H2 that says "(for planning, not yet a Pilot ticket)" is a stop sign.
- Golden-AMI pilot version must be ≥ the headless self-upgrade release
  (v2.282.0) or every new tenant drifts silently. Check
  `aws ssm get-parameter --name /pilot-fleet/console/GOLDEN_AMI_ID` →
  `describe-images` Description after each train that matters.
