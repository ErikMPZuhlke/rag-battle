# Network Security

Acme Cloud follows a zero-trust network model rather than relying on
perimeter security alone.

## Zero Trust Principles

No request is trusted based on network location alone. Every service-to-
service call is authenticated with mutual TLS (mTLS) via the service mesh,
and every request carries an identity that is checked against the calling
service's authorized permissions.

## VPN

Acme Cloud does not use a traditional corporate VPN. Employees connect to
internal tools over the public internet through an identity-aware proxy that
enforces SSO and MFA (see `authentication.md`) on every request, rather than
granting broad network access after a single login.

## Production Network Isolation

Production infrastructure runs in a dedicated cloud account with no direct
network path from corporate laptops. Engineers access production only
through audited, time-boxed break-glass sessions (via the identity-aware
proxy) that are logged in the audit trail described in `audit-logging.md`.

## Firewall and Segmentation

Each service has its own network segment, and traffic between segments is
denied by default; explicit allow rules are defined in infrastructure-as-code
and reviewed like any other change (see `code-review.md`).

## DDoS Protection

The public API and dashboard sit behind a managed DDoS mitigation service
and a web application firewall (WAF) that blocks common attack patterns
before traffic reaches application servers.

## Third-Party Network Access

Vendors requiring network access to Acme Cloud systems (for support or
integration purposes) must go through the process described in
`vendor-management.md`, which requires a signed security addendum before any
access is granted.
