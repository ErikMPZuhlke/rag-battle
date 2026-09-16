# Testing Standards

Acme Cloud expects every service to maintain a reasonable, enforced level of
automated test coverage before code reaches production.

## The Test Pyramid

Teams are expected to follow a standard test pyramid:

- **Unit tests** — fast, isolated, run on every commit. Target: majority of
  the test suite.
- **Integration tests** — exercise a service against real dependencies
  (a test database, a local message broker) using Docker Compose in CI.
- **End-to-end tests** — a small suite that exercises full user journeys
  against the staging environment after each deployment to staging.

## Coverage Thresholds

CI enforces a minimum of 80% line coverage for new code in pull requests
(measured as a diff-coverage check, not overall repository coverage). Pull
requests that drop diff coverage below 80% are blocked from merging unless a
Platform team member overrides the check with a documented justification.

## Flaky Tests

Tests that fail intermittently must be quarantined (marked `@flaky` and
excluded from the blocking suite) within one business day of being reported,
and a ticket must be filed to fix or delete them within two weeks. Flaky
tests are not allowed to block unrelated pull requests indefinitely.

## Staging Verification

Before a change is promoted to production, the automated end-to-end suite
must pass against staging. A failing end-to-end suite blocks promotion
regardless of who is requesting it, including during incident response —
though see `incident-response.md` for how this interacts with emergency
fixes.

## Load and Performance Testing

Services that sit in a critical request path (ingest, query, alerting) run a
weekly automated load test against a dedicated performance environment. Load
test regressions of more than 15% latency at the 95th percentile must be
investigated before the next release.
