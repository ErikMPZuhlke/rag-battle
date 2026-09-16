# Incidents

This document covers the operational lifecycle of an incident, complementing
`incident-response.md`'s focus on roles and emergency approvals.

## Detection

Most incidents are detected automatically by alerting rules (see
`observability.md`) and page the on-call engineer via the paging system
described in `on-call.md`. A smaller number are reported by customers
through support and escalated per `support.md`.

## Incident Timeline

Every incident has a timeline document created automatically when a page
fires, capturing key events (detection, acknowledgment, mitigation actions,
resolution). Incident timeline entries are retained for **180 days**,
distinct from both the general application log retention (30/90 days, see
`observability.md`) and the security audit log retention (1 year, see
`audit-logging.md`).

## Status Communication

P1 and P2 incidents trigger updates to the public status page at least every
30 minutes until resolution. Enterprise customers additionally receive
direct communication from their account team.

## Resolution

An incident is considered resolved when the customer-facing impact has
stopped, even if follow-up cleanup work remains. Resolution time is what's
measured against the SLA targets in `sla.md`.

## Postmortems

Postmortems are blameless and focus on systemic causes rather than
individual mistakes. They are published internally and, for Enterprise
customers directly affected by a P1, summarized in a customer-facing report
by the account team.

## Recurring Incidents

If the same root cause causes three or more incidents in a 90-day period, it
is automatically escalated to engineering leadership for prioritized
remediation, regardless of the individual incidents' severity.
