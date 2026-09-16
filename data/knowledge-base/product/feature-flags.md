# Feature Flags

Acme Cloud uses feature flags to control the rollout of new functionality
independently of deployments.

## Flag Types

- **Release flags** — temporary, used to gradually roll out a new feature
  (e.g., 5% → 25% → 100% of tenants) and removed once fully released.
- **Ops flags** — longer-lived, used as a kill switch for expensive or
  risky features so they can be disabled without a deployment during an
  incident.
- **Permission flags** — gate features by subscription tier (see
  `pricing.md`) or by explicit entitlement for Enterprise customers.

## Who Can Change Flags

Engineers can change release and ops flags for their own team's services
without additional approval, since flag changes don't go through the
production deployment pipeline described in `deployments.md`. Flags that
affect billing or entitlements require sign-off from a product manager,
since they can have direct revenue impact.

## Flag Lifecycle

Release flags must be removed (and the flag-gated code paths cleaned up)
within 90 days of reaching 100% rollout. Stale flags are flagged by an
automated weekly report to the owning team.

## Flags During Incidents

Ops flags are a first-class incident mitigation tool: disabling a risky
feature via a flag is often faster and safer than a deployment, and does not
require the deployment approval described in `access-control.md`, since no
new code is being shipped. This is frequently the fastest path to
mitigating a P1 incident, per `incident-response.md`.

## Auditing

All flag changes are logged with the engineer who made the change and the
timestamp, visible in the internal flag dashboard, though this log is
distinct from the security audit log described in `audit-logging.md`.
