# Access Control

This document describes how permissions are granted and enforced across
Acme Cloud's internal systems.

## Group-Based Permissions

Access to sensitive systems is managed through groups in the corporate
identity provider, not individual grants. The key groups relevant to
engineering are:

- `platform-team` — members can approve production deployments, modify
  shared infrastructure, and manage the CI/CD pipeline.
- `secrets-readers` — members can read production secrets from the vault.
- `security-team` — members can approve security-sensitive code reviews and
  access audit logs across all teams.

## Production Deployment Approval

**Engineers outside the Platform team do not have permission to approve
production deployments.** Membership in `platform-team` is the only
credential that grants the "approve production deployment" action in the
CI/CD system; this is enforced at the pipeline level, not just by policy. An
engineer on the Ingest, Query, Alerting, or Billing teams cannot approve
their own production deployment, no matter their seniority.

The only documented exception is the emergency approval an Incident
Commander can grant during a P1 incident — see `incident-response.md`.

## Requesting Access

Access requests (including `secrets-readers` membership) are submitted
through the IT portal. Standard requests require:

1. Manager approval.
2. Approval from the owning team's lead for the specific system
   (for `secrets-readers`, this is a security team lead).

Access requests are typically fulfilled within two business days. Emergency
access requests can be expedited by the on-call security engineer but still
require after-the-fact manager sign-off.

## Access Reviews

All group memberships are reviewed quarterly by the security team. Access
that hasn't been used in 90 days is automatically revoked and must be
re-requested if still needed.

## Offboarding

When an employee leaves Acme Cloud, all access is revoked automatically on
their last working day as part of the offboarding workflow (see
`onboarding.md` for the mirrored onboarding flow).
