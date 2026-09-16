# Production Deployments

This document describes how code moves from a merged pull request to running
in production.

## Deployment Pipeline

Every service uses the same CI/CD pipeline, owned and maintained by the
Platform team. A merge to `main` automatically builds an artifact and
deploys it to `staging`. Promotion from `staging` to `production` is a
separate, manual step.

## Approval Policy

**All production deployments must be approved by a member of the Platform
team** before the promotion step runs. This is enforced by the deployment
pipeline: the "promote to production" action is gated behind an approval
check in the CI system, and only accounts belonging to the `platform-team`
group in the identity provider are authorized approvers.

This is a hard technical control, not just a guideline — see
`access-control.md` for how the underlying permission is granted and to whom.

## Standard Exception: Incident Response

The one documented exception to the standard approval policy applies during
active P1 incidents. See `incident-response.md` for the emergency approval
process, which allows the Incident Commander to grant temporary deployment
approval to engineers outside the Platform team so that a fix can ship
immediately.

## Deployment Windows

Standard (non-emergency) production deployments should occur Monday through
Thursday, 09:00–16:00 in the region of the primary on-call engineer, to
ensure adequate staffing if something goes wrong. Friday deployments are
discouraged but not forbidden; they require an additional sign-off from the
on-call lead.

## Rollbacks

Any deployment can be rolled back via the same pipeline by re-promoting the
previous artifact version. Rollbacks do not require Platform team approval
if they restore a previously-approved version, since no new code is being
introduced.

## Change Records

Every production deployment automatically creates a change record, including
the approver's identity, the artifact version, and the deployment time. These
records are retained for one year and are referenced during compliance
audits (see `audit-logging.md`).
