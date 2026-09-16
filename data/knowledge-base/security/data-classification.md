# Data Classification

Acme Cloud classifies data into four tiers to determine how it must be
handled, stored, and who may access it.

## Tiers

- **Public** — marketing content, published documentation. No restrictions.
- **Internal** — internal handbooks (like this knowledge base), architecture
  docs, non-sensitive metrics. Accessible to all employees.
- **Confidential** — customer account data, billing details, internal
  financial data. Access requires a business justification and is logged.
- **Restricted** — authentication secrets, encryption keys, and raw
  customer log/metric payloads that may contain sensitive data. Access
  requires group membership as described in `access-control.md` and
  `secrets.md`.

## Handling Rules

Confidential and Restricted data may never be copied to a personal device,
pasted into an unapproved third-party tool (including consumer AI chat
tools), or emailed outside the company without encryption.

## Customer Data in Logs

Application logs are scrubbed of common sensitive fields (passwords,
tokens, payment details) automatically before being written to the logging
pipeline described in `observability.md`. Engineers must not manually log
raw request bodies that could contain Confidential or Restricted data.

## Data Residency

Enterprise customers on the EU plan have their data stored exclusively in
the EU region, per contractual data residency commitments described in
`enterprise-plans.md`.

## Retention and Deletion

Confidential customer data is retained for the duration of the customer's
subscription plus 30 days, after which it is permanently deleted unless a
legal hold requires longer retention. Deletion requests can be made through
`support.md`'s standard support channel.
