# Deprecation Policy

This document tracks policy and feature deprecations across the product,
and is the source of truth when an older document conflicts with it.

## Refund Window Update (Effective July 2025)

**Effective July 2025, the refund request window was extended from 14 days
to 30 days** for all paid subscription plans. The previous 14-day window
described in the older version of `refunds.md` no longer applies to any
charge billed on or after the effective date. Support agents should always
apply the 30-day window unless handling a legacy case explicitly flagged as
pre-July-2025.

## Feature Deprecations

Acme Cloud deprecates features with a minimum 6-month notice period before
removal, in line with the API versioning guarantee described in
`api-design.md`. Deprecation notices are posted on the status page and
emailed to affected customers.

## Currently Deprecated

- The legacy v0 REST API (pre-versioning) — removal scheduled, customers
  notified individually.
- The original 14-day refund window — superseded as described above.
- The legacy on-premise agent (replaced by the current cloud-native agent).

## Deprecation vs. Removal

"Deprecated" means a feature or policy is no longer recommended and will be
removed, but may still function during a transition period. "Removed" means
it no longer functions at all. This document is updated whenever a
deprecated item is fully removed.

## Requesting an Exception

Customers materially impacted by a deprecation can request a temporary
exception through their account team (Enterprise) or standard support
(self-serve tiers), per `support.md`.
