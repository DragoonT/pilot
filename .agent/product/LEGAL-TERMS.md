# Pilot Cloud — legal terms, source of truth for the website

**Status:** DRAFT 2026-10-14, assembled from founder decisions on record. **Not lawyer-reviewed.** Fields marked `[FOUNDER]` are facts only the founder can supply; no page may render with them missing (Paddle rejects placeholders).
**Consumers:** the `pilotcloud-site` session renders these as `/terms`, `/refunds`, `/privacy` (TASK-515 § S2) and the licence summary on `/self-hosted`. The software licence itself lives in `LICENSE` at the root of this repo; this doc restates its grant and the agreed addition.
**Rule:** numbers that can change with pricing (price, included tickets, fair-use ceiling, pack prices) are **not** repeated here. The terms point to the pricing page, so a price change never needs a terms change.

---

## 0. Facts the pages need

| Fact | Value | Source |
|---|---|---|
| Legal entity | `[FOUNDER]` legal name and form | Paddle live account is "Quantflow"; verification needs the registered legal name |
| Registered address | `[FOUNDER]` | Paddle verification; Montenegro per the sandbox business profile |
| Contact email | `hello@quantflow.studio` | `pilotcloud-site/lib/site.ts` `contactEmail` |
| Licensing contact | `mr.alex.petrov@gmail.com` | `LICENSE` footer |
| Merchant of record | Paddle.com Market Ltd (Paddle) | TASK-497; Paddle sells, invoices, collects tax, handles refunds and chargebacks |
| Hosting region | AWS `eu-central-1` (Frankfurt) | fleet design; one EC2 instance per customer organisation |
| Model provider | Anthropic (Claude) | included allowance on our key; overage on the customer's own key |
| Payment processor fee disclosure | none required; Paddle's fee is ours | — |
| Governing law and venue | `[FOUNDER]` (default: the entity's country) | — |
| Last updated | the date the page ships | — |

---

## 1. Terms of Service (Pilot Console)

### 1.1 Who and what
- These terms are between the legal entity above ("we") and the organisation that creates a Pilot Console account ("you"). The person who signs up confirms they may bind that organisation.
- **Pilot Console** is a hosted service: a dedicated Pilot instance for your organisation, a web console, and connections to your GitHub, Linear or Jira. It takes tickets you label and returns pull requests.
- **Pilot (terminal)** is software you run yourself under the Business Source License 1.1 (section 4). These terms do not cover it beyond section 4.

### 1.2 Account
- One account per organisation. One person is the owner; the owner may add members (when the invite feature ships; until then the account is single-user). Members act for the organisation.
- You keep your credentials secret and tell us at the contact email if they leak.
- You must be 18 or older and must not be subject to sanctions that prohibit us from serving you.

### 1.3 What the subscription includes
- A dedicated instance, the console, connectors, upgrades, backups and support by email.
- A monthly allowance of model usage on our Anthropic key, described on the pricing page as a number of tickets on the default model, subject to the fair-use ceiling shown there. When the allowance is used up, the instance continues on your own Anthropic key if you have provided one, otherwise work pauses until the next billing period.
- Usage on your own key is billed to you by Anthropic directly. We do not mark it up and we do not see that invoice.
- No per-seat charges. The price is per organisation.
- Rate limits and daily caps as published on the pricing page or in the console, to protect the service from runaway usage.

### 1.4 Your responsibilities
- You own your repositories and decide which ones Pilot may access. You review every pull request before merging it; Pilot's output is a proposal, not a release.
- You provide the API keys and tokens Pilot needs (GitHub, tracker, optionally Anthropic) and you may revoke them at any time. Revoking a required key pauses the service.
- You do not use the service to build a competing hosted offering, to attack systems you do not own, to process data you have no right to process, or in violation of Anthropic's or GitHub's acceptable-use terms.

### 1.5 Intellectual property
- Your code, tickets, and the pull requests Pilot opens in your repositories are yours. We claim no rights in them.
- The service, the console and Pilot are ours (or our licensors'). The terminal software is licensed under section 4, not sold.
- We do not use your repository contents to train models. Model requests go to Anthropic under Anthropic's commercial terms, which exclude training on API data.

### 1.6 Data, privacy and security
- Section 3 (Privacy notice) describes what we store and where. In short: account data, connector identities, repository metadata, execution logs and usage metrics, on AWS in Frankfurt, in an instance dedicated to your organisation.
- We encrypt secrets at rest, isolate organisations at the virtual-machine boundary, and keep backups for operational recovery.
- We notify you without undue delay of a security incident affecting your data.

### 1.7 Fees and billing
- Prices are on the pricing page in USD. Paddle, our merchant of record, charges you, issues the invoice, applies tax and may show the amount in your local currency.
- Billing is monthly in advance. The included allowance resets at each billing period and does not roll over.
- We may change prices with at least 30 days' notice by email. The change applies from your next billing period after the notice.
- If a payment fails, Paddle retries for up to 30 days. During that time the service may be limited; after it, the subscription ends.

### 1.8 Term, cancellation and refunds
- The subscription renews monthly until cancelled.
- You may cancel at any time from the console or via Paddle's customer portal. Cancellation takes effect at the end of the current billing period; the service stays available until then.
- Refunds follow section 2.
- We may suspend or end the service for breach of section 1.4, for non-payment, or if required by law, with notice where the law allows.
- On termination we delete your instance and its data within 30 days, except what we must keep for accounting.

### 1.9 Availability and support
- We aim for continuous availability but give no uptime guarantee during the design-partner period. We announce planned maintenance in the console.
- Support is by email at the contact address, on business days.

### 1.10 Warranties and liability
- The service is provided "as is". Pilot proposes code changes; you are responsible for reviewing and merging them.
- To the extent the law allows, our total liability under these terms is limited to the fees you paid in the 12 months before the claim. We are not liable for indirect or consequential loss, lost profits or lost data caused by merged changes you accepted.
- Nothing limits liability for fraud, wilful misconduct, or where the law does not allow limitation.

### 1.11 Changes to these terms
- We may update these terms. Material changes are announced by email at least 30 days ahead. Continued use after that date is acceptance.

### 1.12 Law and disputes
- `[FOUNDER]` governing law and venue. Before litigation both sides try to settle by discussion for 30 days.

### 1.13 Contact
- `hello@quantflow.studio`, with the postal address of section 0.

---

## 2. Refund Policy

- Monthly subscription, charged in advance by Paddle, our merchant of record.
- **First charge:** full refund on request within 14 days of the first payment. Email the contact address from the account owner's email; Paddle processes the refund to the original payment method within 5–10 business days.
- **Renewals:** no refunds for a period already started. Cancel before the renewal date to stop the next charge; the service stays available to the end of the paid period.
- **Unused allowance:** no partial refunds for unused tickets or model usage.
- **Prepaid packs** (when offered): refundable within 14 days of purchase if unused; non-refundable once any ticket from the pack has been consumed. Packs expire as stated at purchase.
- **Service faults:** if we fail to provide the service for more than 72 consecutive hours for reasons within our control, you may request a pro-rata credit for the affected days.
- **Chargebacks:** contact us first; a chargeback opened without contact may lead to suspension while Paddle investigates.
- Statutory rights of consumers are not affected; the service is sold to businesses.

---

## 3. Privacy Notice (facts for the page)

- **Controller:** the legal entity of section 0, contact `hello@quantflow.studio`.
- **What we collect:** account email and name; organisation name; GitHub, Linear or Jira identities and tokens you connect; repository names, branches, issue and pull-request metadata; execution logs, token counts and cost metrics; console chat messages you send to your instance; support emails; billing status from Paddle (never card numbers).
- **Why:** to run your instance, to meter the included allowance, to bill you, to support you, and to keep the service secure. Legal basis: contract performance; legitimate interest for security and metrics.
- **Processors:** AWS (hosting, `eu-central-1`); Paddle (billing, merchant of record); Anthropic (model requests, under its commercial terms, no training on API data); GitHub, Linear, Atlassian (connectors you enable); an email provider for transactional mail `[FOUNDER: name it]`; Doppler (secrets management).
- **Where:** EU (Frankfurt) for your instance and database. Paddle and Anthropic process data in their own regions under standard contractual clauses.
- **Retention:** account and billing records for the subscription plus the statutory accounting period; instance data deleted within 30 days of termination; logs up to 90 days.
- **Your rights:** access, correction, deletion, portability, objection, and complaint to a supervisory authority. Email the contact address.
- **Cookies:** the console uses a session cookie only; the marketing site uses no tracking cookies `[FOUNDER: confirm no analytics]`.
- **Children:** not directed at anyone under 18.

---

## 4. Software licence (Pilot, terminal)

- `LICENSE` at the repo root: **Business Source License 1.1**. Licensor Aleksei Petrov. Change Date four years from publication; Change License Apache 2.0.
- **Additional Use Grant (current text):** production use is allowed unless you offer Pilot to third parties on a hosted or embedded basis to compete with Pilot Cloud. Internal use inside an organisation, at any size, is never a competitive offering.
- **Agreed addition (founder decision 2026-10-13, TASK-02 in `pilotcloud-site`; not yet in `LICENSE`):** organisations with fewer than 10 employees, including all affiliates under common control, may make any production use, including a competitive offering.
- **Proposed sunset (Navigator suggestion 2026-10-13, founder to confirm with a lawyer):** that small-organisation grant ends 90 days after the organisation reaches 10 or more employees, after which the standard limits apply. Without a sunset a competitor keeps the grant after it grows.
- The site's `/self-hosted` page restates this in plain words and links to the `LICENSE` file. The site must not describe the sunset until it is in `LICENSE`.
- No telemetry, no licence keys, no enforcement mechanism in the software (founder decision 2026-10-13).

---

## 5. What is still open

| Item | Owner | Blocks |
|---|---|---|
| Legal entity name, registered address, governing law | founder | all three pages; Paddle verification |
| Lawyer review of sections 1, 2, 4 | founder | go-live of `/terms` |
| Small-organisation paragraph in `LICENSE` (with or without the 90-day sunset) | founder approves text → PR in this repo | `/self-hosted` licence wording |
| Email provider and analytics confirmation | founder | `/privacy` processors list |
| Pack wording in section 1.3/2 | Navigator, after TASK-546 D3–D5 | none today; keep the pricing-page pointer |

---

## Refs

- TASK-515 § S2 (page spec, placeholder test, mutation pin), TASK-497 (Paddle MoR facts), TASK-546 (pricing v3), `pilotcloud-site/.agent/tasks/TASK-02-install-and-license.md` (small-org grant decision)
- `product/PRICING-MODEL.md`, `product/UNIT-ECONOMICS.md`, `system/references/reference_paddle_account.md`
