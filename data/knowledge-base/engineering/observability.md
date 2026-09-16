# Observability

Acme Cloud instruments its own services with the same monitoring product it
sells to customers, plus some internal-only tooling.

## Logging

Every service emits structured JSON logs to the central logging pipeline.

**Application logs** (request logs, application errors, debug traces) are
retained for **30 days in the hot (searchable) tier**, and then archived to
cold storage for an additional **60 days** (90 days total) before permanent
deletion. Cold-tier logs can be restored on request but are not searchable
directly.

This retention period applies to general application and infrastructure
logs. It does **not** apply to security audit logs, which have a separate
and longer retention period — see `audit-logging.md`.

## Metrics

Each service exposes Prometheus-compatible metrics on `/metrics`. Standard
metrics (request rate, error rate, latency percentiles) are scraped every 15
seconds and retained at full resolution for 13 months for trend analysis.

## Tracing

Distributed tracing uses OpenTelemetry, with traces sampled at 10% in
production (100% in staging). Traces are retained for 14 days.

## Dashboards and Alerting

Each team maintains a service dashboard covering the four golden signals
(latency, traffic, errors, saturation). Alert rules that page an on-call
engineer must have a corresponding runbook link; see `on-call.md` for the
paging policy and `sla.md` for the incident severity definitions that alerts
map to.

## Log Access

Read access to the logging pipeline is available to all engineers for their
own team's services by default. Cross-team log access, and any access to
logs containing customer data, follows the same request process described in
`access-control.md`.
