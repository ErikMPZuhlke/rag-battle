# Architecture Overview

Acme Cloud is a multi-tenant SaaS platform for infrastructure monitoring and
alerting. The platform is organized around a small number of core services
that communicate over gRPC internally and expose a public REST/GraphQL API.

## Service Map

- **ingest-service** — receives metrics and logs from customer agents,
  validates payloads, and writes to the streaming pipeline.
- **query-service** — serves dashboards and API reads from the time-series
  store and the document store.
- **alerting-service** — evaluates alert rules against incoming data and
  triggers notifications (email, Slack, PagerDuty).
- **billing-service** — meters usage per tenant and feeds the pricing engine
  described in `pricing.md`.
- **auth-service** — issues and validates tokens; see `authentication.md` for
  details on supported login methods.

## Data Stores

Time-series data lives in a managed columnar store; relational metadata
(tenants, users, teams, roles) lives in PostgreSQL. Object storage (S3-
compatible) holds raw log blobs before they are indexed.

## Environments

Acme Cloud runs three environments — `dev`, `staging`, and `production` — each
in a separate cloud account. Details on promotion between environments are in
`environments.md`.

## Ownership Model

Every service has a single owning team recorded in the internal service
catalog. The **Platform team** owns the shared infrastructure that all other
services run on: the Kubernetes clusters, the CI/CD pipelines, the service
mesh, and the production deployment tooling. Because Platform owns the
deployment tooling, they are also the team responsible for final production
deployment approvals — see `deployments.md` and `access-control.md` for the
exact policy.

Product engineering teams (Ingest, Query, Alerting, Billing) own their
service's code and are responsible for its correctness and on-call rotation,
but they do not own the underlying deployment mechanism.

## Architecture Decision Records

Significant architecture changes are documented as ADRs in the internal wiki
(not in this knowledge base). This document reflects the state of the
architecture as of the most recent quarterly review and is updated by the
Platform team.
