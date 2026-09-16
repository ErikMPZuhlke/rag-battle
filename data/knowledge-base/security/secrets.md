# Secrets Management

Acme Cloud stores all credentials, API keys, and certificates in a central
secrets vault rather than in code or configuration files.

## The Vault

Secrets are organized by environment and service (for example,
`production/billing-service/db-password`). The vault encrypts secrets at
rest and in transit, and every read is logged (see `audit-logging.md`).

## Access to Secrets

Reading a production secret requires membership in the `secrets-readers`
group. As described in `access-control.md`, joining this group requires
manager approval plus sign-off from a security team lead — there is no
self-service option for production secrets, even for senior engineers.

Staging and dev secrets have a lighter-weight process: any engineer on the
owning team can read them without additional approval, since no customer
data is at risk in those environments (see `environments.md`).

## Rotation

- Database credentials rotate automatically every 90 days.
- Third-party API keys rotate on the schedule required by the vendor, with a
  minimum of once per year.
- Any secret suspected of being exposed (e.g., accidentally committed to a
  repository) must be rotated within one hour of discovery, and the incident
  must be reported per `incident-response.md`.

## Secrets in CI/CD

The deployment pipeline retrieves secrets directly from the vault at
deploy time using a short-lived service identity; secrets are never stored
as CI environment variables in plaintext.

## Local Development

Local development uses mock/fake secrets only. Real secrets are never
distributed to individual laptops, in line with the zero-trust principles
described in `network-security.md`.
