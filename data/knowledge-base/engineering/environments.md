# Environments

Acme Cloud maintains three primary environments for every service.

## Dev

The `dev` environment is a shared, always-on environment used for manual
testing and integration work between teams. Any engineer can deploy their
own branch to `dev` at any time using the `acme-cli deploy --env dev`
command; no approval is required.

## Staging

`staging` is a production-like environment used for automated end-to-end
testing and pre-release verification. Deployments to `staging` happen
automatically on every merge to `main` (see `deployments.md`). Staging uses
synthetic (non-customer) data only.

## Production

`production` serves real customer traffic and is subject to the full
approval policy described in `deployments.md` and `access-control.md`.
Production infrastructure is provisioned in two regions for redundancy;
failover between regions is described in `business-continuity.md`.

## Environment Parity

Staging and production run the same infrastructure-as-code templates to
minimize configuration drift. The only intentional differences are scale
(staging runs smaller instance sizes) and data (staging never contains real
customer data, to simplify compliance).

## Secrets Per Environment

Each environment has its own isolated secret store; a secret valid in
staging is never valid in production and vice versa. See `secrets.md` for
how secrets are provisioned and rotated.

## Local Development

Engineers run a local development environment via Docker Compose, which
mocks external dependencies. Local environments do not have access to any
real cloud credentials.
