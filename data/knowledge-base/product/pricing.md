# Pricing

Acme Cloud offers three subscription tiers: Starter, Growth, and Enterprise.

## Tiers Overview

- **Starter** — $49/month, up to 3 team members, 7-day data retention,
  community support only.
- **Growth** — $299/month, up to 25 team members, 30-day data retention,
  email support with a 1-business-day response target.
- **Enterprise** — custom pricing, unlimited team members, configurable data
  retention (up to 2 years), dedicated account team, and the SLA commitments
  described in `sla.md`. See `enterprise-plans.md` for details.

## Usage-Based Add-Ons

All tiers include a base allotment of ingested data volume per month.
Overage is billed per GB ingested beyond the plan allotment, at a rate that
decreases at higher volume tiers. Usage is metered by the billing-service
described in `architecture.md`.

## Annual Discounts

Customers who pay annually instead of monthly receive a 15% discount on the
Growth and Enterprise tiers. Starter is month-to-month only.

## Rate Limits by Tier

API rate limits scale with the subscription tier: Starter is limited to 60
requests/minute, Growth to 600 requests/minute, and Enterprise limits are
negotiated individually. See `api-design.md` for the rate-limit response
format.

## Price Changes

Acme Cloud provides at least 30 days' notice before any price increase takes
effect for existing customers. Promotional pricing for new customers can
change at any time and does not affect customers already on a plan.

## Trial Accounts

New customers can start a 14-day free trial of the Growth tier without a
credit card; see `trial-accounts.md` for trial limitations and conversion
details.
