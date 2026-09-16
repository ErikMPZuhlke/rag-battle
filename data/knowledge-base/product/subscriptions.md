# Subscriptions

This document covers how customers manage their Acme Cloud subscription
lifecycle: upgrades, downgrades, and cancellations.

## Upgrades

Upgrading a subscription (e.g., Starter to Growth) takes effect immediately,
and the customer is billed a prorated amount for the remainder of the
current billing cycle at the new tier's rate.

## Downgrades

Downgrades take effect at the start of the next billing cycle, not
immediately, to avoid mid-cycle data loss if the new tier has a shorter
retention window. Customers are warned in the dashboard if their current
usage exceeds the limits of the tier they are downgrading to.

## Cancellations

Customers can cancel at any time from the billing settings page. Cancelling
stops future billing but does not issue a refund for the current billing
period — refunds are handled separately; see `refunds.md` for the current
refund policy.

## Reactivation

A cancelled account can be reactivated within 90 days with all historical
data intact (subject to the data retention rules of the reactivated tier).
After 90 days, historical data is deleted per `data-classification.md`, and
reactivation creates a fresh account.

## Multi-Year Contracts

Enterprise customers may sign multi-year contracts with fixed pricing; early
termination terms for multi-year contracts are negotiated individually and
documented in the customer's order form, not in this handbook.

## Seat Management

Adding or removing team member seats on Growth and Enterprise plans can be
done self-service from the dashboard and is billed on the next invoice on a
prorated basis.
