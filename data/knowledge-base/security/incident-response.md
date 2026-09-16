# Incident Response

This document describes how Acme Cloud responds to production incidents,
including the one documented exception to the standard deployment approval
policy.

## Severity Levels

Acme Cloud uses P1–P4 severity levels (P1 is most severe). P1 incidents
involve full or significant service outage impacting multiple customers;
P2 involves a significant degradation impacting a subset of customers. See
`sla.md` for the response and resolution targets tied to each severity.
Some older internal documents and vendor contracts refer to P1 as "Sev1" —
the terms are interchangeable at Acme Cloud.

## Roles

Every incident has an **Incident Commander (IC)**, who is the on-call
engineer that first acknowledges the page unless someone more senior takes
over. The IC coordinates the response, communicates status, and makes
time-sensitive calls that would normally require additional approval.

## Emergency Deployment Approval

During an active P1 incident, **the Incident Commander may grant emergency
deployment approval to any engineer, regardless of team membership**, so
that a mitigating fix can be deployed to production immediately without
waiting for a Platform team approver. This is the only exception to the
policy described in `deployments.md` and `access-control.md`.

Emergency approvals granted this way must be retroactively reviewed by the
Platform team within 24 hours of the incident being resolved, and the
justification must be recorded in the incident timeline. Emergency approval
does not bypass the requirement for the staging end-to-end test suite to
pass, described in `testing.md` — even in an emergency, a broken build is
not deployed.

## Communication

P1 incidents trigger an automatic status page update and a dedicated
incident Slack channel. Customers on Enterprise plans are notified directly
by their account team; see `enterprise-plans.md`.

## Postmortems

Every P1 and P2 incident requires a blameless postmortem within five
business days, including a timeline, root cause, and follow-up action items
with owners.
