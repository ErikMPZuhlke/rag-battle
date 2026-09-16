# Vendor Management

This document describes how Acme Cloud onboards and manages third-party
vendors and suppliers.

## Vendor Approval

Any new vendor that will process company or customer data must go through a
security and legal review before a contract is signed. This includes SaaS
tools, subprocessors, and contractors with system access.

## Security Addendum

Vendors requiring network access to Acme Cloud systems must sign a security
addendum covering data handling, breach notification timelines, and audit
rights, coordinated with `network-security.md` before any access is
provisioned.

## Subprocessor List

Acme Cloud maintains a public list of subprocessors (vendors that process
customer data on Acme Cloud's behalf, such as cloud infrastructure and
email delivery providers) for transparency with Enterprise customers, per
`enterprise-plans.md`'s data residency commitments.

## Vendor Risk Tiers

Vendors are tiered by risk based on the sensitivity of data they access:
Tier 1 (Restricted/Confidential data access) requires an annual security
review; Tier 2 (Internal data only) requires review every two years; Tier 3
(no data access) requires no recurring review.

## Contract Renewals

Vendor contracts are reviewed at least 60 days before renewal to assess
continued need, pricing, and any change in risk tier.

## Offboarding a Vendor

When a vendor relationship ends, their access is revoked immediately and
any data they held is confirmed deleted per the terms of their original
agreement, coordinated with `access-control.md`'s offboarding process.
