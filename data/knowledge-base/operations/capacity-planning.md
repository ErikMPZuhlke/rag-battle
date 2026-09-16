# Capacity Planning

This document describes how Acme Cloud plans infrastructure capacity ahead
of demand.

## Forecasting

The Platform team reviews usage growth trends quarterly, using metering data
from the billing-service (see `architecture.md`) as a leading indicator of
infrastructure demand, since ingestion volume correlates closely with
compute and storage needs.

## Headroom Targets

Production infrastructure is provisioned to maintain at least 40% headroom
above peak observed load at all times, to absorb both organic growth and
unexpected traffic spikes without emergency scaling work.

## Scaling Events

Known high-traffic events (a large customer's product launch, a marketing
campaign) should be flagged to the Platform team at least two weeks in
advance so capacity can be pre-provisioned rather than relying on reactive
autoscaling alone.

## Autoscaling

Most services autoscale automatically based on CPU and request-queue depth,
within limits set by the Platform team to control cost. Autoscaling limits
are reviewed as part of the quarterly capacity review.

## Cost Reviews

Capacity planning is done jointly with a cost review, since over-
provisioning has a direct cost impact; the Platform team balances headroom
targets against the cost efficiency goals discussed with Finance during
budget planning.

## Capacity-Related Incidents

If an incident is caused by insufficient capacity (rather than a bug), the
postmortem (see `incidents.md`) must include a capacity-planning action
item, not just a code fix.
