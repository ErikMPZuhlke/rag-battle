# Billing

This document explains how customers are billed for their Acme Cloud usage.

## Billing Cycle

Customers are billed monthly on the anniversary of their signup date, or
annually if they've chosen an annual plan (see `pricing.md` for the annual
discount). Invoices are generated automatically and emailed to the account's
billing contact.

## Payment Methods

Acme Cloud accepts major credit cards and, for Enterprise customers, ACH
bank transfer or wire transfer against a purchase order. Starter and Growth
customers must use a credit card on file.

## Failed Payments

If a payment fails, the customer is notified immediately and given a 7-day
grace period to update their payment method before the account is
downgraded to a read-only state. Data is not deleted during the grace
period or the read-only state.

## Invoicing and Taxes

Invoices include applicable sales tax or VAT based on the billing address on
file. Customers can update their tax ID (e.g., VAT number) in billing
settings, which may exempt them from certain taxes depending on jurisdiction.

## Usage Reports

Customers can view real-time usage (data ingested, API calls, active team
members) in the billing dashboard, which uses the same metering data as the
billing-service described in `architecture.md`.

## Disputes

Billing disputes are handled by the billing team, not general support.
Disputes must be raised within 60 days of the disputed invoice. See
`refunds.md` for how confirmed billing errors are resolved.
