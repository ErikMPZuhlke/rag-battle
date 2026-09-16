# Service Level Agreement (SLA)

This document defines Acme Cloud's incident response and uptime commitments.

## Severity Definitions

Severity levels are defined and used consistently with `incident-response.md`
(P1 = critical, full/major outage; P2 = significant degradation; P3 = minor
issue; P4 = cosmetic/no customer impact).

## Response and Resolution Targets

  | Severity | Acknowledgment | Resolution Target |
  |----------|----------------|--------------------|
  | P1       | 15 minutes     | 4 hours            |
  | P2       | 1 hour         | 1 business day     |
  | P3       | 1 business day | 5 business days    |
  | P4       | Best effort    | Best effort        |

These targets apply to Enterprise customers as contractual commitments; for
Starter and Growth customers they are internal operating goals rather than
contractual guarantees (see `pricing.md` for what's included per tier).

## Uptime Commitment

Enterprise customers receive a **99.9% monthly uptime commitment**. If Acme
Cloud fails to meet this commitment, affected customers are eligible for
service credits as described in their order form (see
`enterprise-plans.md`).

## Measuring Uptime

Uptime is measured as the percentage of time the public API and dashboard
successfully respond to synthetic health checks run every 60 seconds from
three independent regions.

## Planned Maintenance

Planned maintenance windows are excluded from uptime calculations if
customers are notified at least 72 hours in advance, per
`change-management.md`.

## Credit Requests

Customers must request an SLA credit within 30 days of the qualifying
incident by contacting their account team or support, per `support.md`.
