# Change Management

This document describes how planned, non-emergency changes to production
systems are tracked and communicated.

## What Counts as a Change

Any production deployment (see `deployments.md`), infrastructure
modification, or configuration change that could affect customers is
considered a change and must be logged in the change calendar, even if it
doesn't require special approval beyond the standard deployment pipeline.

## Planned Maintenance

Maintenance that may cause customer-visible downtime or degraded
performance must be scheduled at least 72 hours in advance and posted to
the status page, so it can be excluded from uptime calculations per
`sla.md`.

## Change Freeze Periods

Acme Cloud observes a change freeze during major shopping/traffic events
relevant to customers (communicated ahead of time) and during the last two
weeks of the calendar year, except for security patches and P1 incident
fixes, which are always allowed regardless of freeze status.

## Emergency Changes

Emergency changes outside a normal deployment (e.g., a manual database
fix during an incident) require sign-off from the Incident Commander and
must still be logged in the change calendar retroactively, per
`incident-response.md`.

## Change Advisory

High-risk changes (schema migrations, cross-region failovers, changes to
the authentication system) are reviewed by a lightweight change advisory
consisting of a Platform team representative and the requesting team's lead
before scheduling.

## Post-Change Verification

Every change owner is responsible for verifying system health for at least
30 minutes after a change completes, using the dashboards described in
`observability.md`.
