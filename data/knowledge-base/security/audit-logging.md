# Audit Logging

Audit logs record security- and compliance-relevant events across Acme
Cloud's systems, separately from the general application logs described in
`observability.md`.

## What Is Audited

- Authentication events (logins, MFA challenges, failed attempts).
- Authorization changes (group membership changes, permission grants and
  revocations, including changes made via `access-control.md`'s request
  process).
- Administrative actions (production deployment approvals, secret reads from
  the vault, customer data exports).

## Retention

**Security audit logs are retained for one year**, considerably longer than
the 30/90-day retention applied to general application logs, to support
compliance investigations and customer security reviews. This longer
retention period applies specifically to the audit event categories listed
above, not to general debug or request logs.

## Access to Audit Logs

Audit logs can only be read by members of the `security-team` group. Unlike
general application logs (which team members can access for their own
services by default, per `observability.md`), audit log access is never
granted by default to individual engineers, even for their own team's
events.

## Tamper Resistance

Audit log entries are written to an append-only store; no role, including
security-team members, has permission to delete or modify an existing audit
entry. This is a deliberate control to preserve evidentiary integrity during
investigations.

## Use in Investigations

During a P1 security incident, the on-call security engineer may query audit
logs directly to reconstruct a timeline, per `incident-response.md`. Findings
from audit logs are included in the incident postmortem when relevant.
