# Business Continuity

This document describes how Acme Cloud maintains service availability
during major disruptions, beyond routine incident response.

## Multi-Region Design

Production infrastructure runs across two geographic regions. Core
customer-facing services can fail over from the primary to the secondary
region; see `environments.md` for how production environments are
structured and `architecture.md` for the service map.

## Failover Triggers

A regional failover is declared by the Incident Commander during a
severity-1 ("Sev1"/P1) event when the primary region is unavailable or
severely degraded, following the same incident command structure described
in `incident-response.md`.

## Recovery Objectives

Acme Cloud targets a Recovery Time Objective (RTO) of 30 minutes and a
Recovery Point Objective (RPO) of 5 minutes for core services in a full
regional failover, meaning at most 5 minutes of data could be lost and
service should be restored within 30 minutes.

## Disaster Recovery Testing

Full regional failover is tested in a controlled game-day exercise twice a
year, coordinated with `change-management.md` since it involves production
traffic shifts.

## Business-Critical Vendors

Business continuity planning also considers dependencies on business-
critical vendors (e.g., the cloud infrastructure provider itself); see
`vendor-management.md` for how vendor risk is assessed.

## Communication During a Disaster

During a business continuity event, customer communication follows the same
status page and account team channels used for standard P1 incidents,
described in `incidents.md` and `support.md`, just at a larger scale.
