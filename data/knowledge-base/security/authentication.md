# Authentication

Acme Cloud supports several authentication methods for both employees and
customers.

## Employee Authentication

All internal systems require single sign-on (SSO) via the corporate
identity provider, with mandatory multi-factor authentication (MFA). Shared
accounts are not permitted; every system access must be traceable to an
individual employee.

## Customer Authentication

Customers accessing the Acme Cloud dashboard authenticate via:

- Email + password with mandatory MFA (TOTP or WebAuthn).
- SSO via SAML 2.0 for Enterprise plan customers (see `enterprise-plans.md`).

## API Authentication

Programmatic access to the public API uses either:

- **API keys** — simplest option, scoped to a single project, suitable for
  server-to-server integrations.
- **OAuth2 client credentials** — recommended for integrations that need
  fine-grained, revocable scopes.

API keys and OAuth2 credentials are both considered secrets and are subject
to the exposure-response process in `secrets.md`.

## Session Management

Web sessions expire after 12 hours of inactivity. API tokens issued via
OAuth2 expire after 1 hour and must be refreshed; API keys do not expire but
can be revoked instantly from the dashboard.

## Password Policy

Passwords must be at least 12 characters. Acme Cloud does not enforce
periodic password rotation for employees or customers, following current
industry guidance that favors MFA and breach monitoring over forced
rotation.

## Account Lockout

After 10 consecutive failed login attempts, an account is locked for 15
minutes. Repeated lockouts trigger a security review, which may be escalated
per `incident-response.md` if credential stuffing is suspected.
