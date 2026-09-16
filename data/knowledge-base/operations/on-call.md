# On-Call

This document describes the on-call rotation and paging expectations for
engineering teams.

## Rotation Structure

Each product engineering team (Ingest, Query, Alerting, Billing) maintains
its own primary and secondary on-call rotation, typically one week at a
time. The Platform team maintains a separate rotation covering shared
infrastructure and the deployment pipeline.

## Paging and Response Time

Primary on-call must acknowledge a page within **15 minutes**, matching the
P1 acknowledgment target in `sla.md`. If the primary doesn't acknowledge
within 15 minutes, the page automatically escalates to secondary, and then
to the team's manager if secondary also doesn't respond within a further 10
minutes.

## Compensation

Engineers on the primary on-call rotation receive on-call pay for each week
of active rotation, plus additional compensation for hours actually spent
responding to a page outside business hours.

## Swaps and Time Off

On-call shifts can be swapped between team members with manager awareness,
but a rotation slot can never be left uncovered. Engineers on pre-approved
vacation are removed from the rotation schedule in advance, per
`time-off.md`.

## Connectivity Requirements

On-call engineers must have reliable internet access and be able to reach a
laptop within the acknowledgment window for their entire on-call shift,
regardless of whether they are working from an office or remotely that day
(see `remote-work.md`).

## Becoming an Incident Commander

The on-call engineer who acknowledges a page becomes the default Incident
Commander for that incident unless a more senior engineer explicitly takes
over; see `incident-response.md` for what the IC role entails, including the
emergency deployment approval authority.
