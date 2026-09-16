# API Design Guidelines

Acme Cloud exposes both a REST API and a GraphQL API to customers, plus
internal gRPC APIs between services.

## Public API Principles

- APIs are versioned in the URL path for REST (`/v1/...`) and via schema
  deprecation fields for GraphQL.
- Breaking changes are never made to a published API version. A new version
  must be introduced instead, with the old version supported for at least
  six months after the new version ships.
- All public endpoints require authentication; see `authentication.md` for
  supported methods (API keys, OAuth2 client credentials).

## Naming Conventions

REST resources use plural nouns (`/v1/alerts`, `/v1/dashboards`). Fields use
`snake_case` in JSON payloads for backward compatibility with early SDKs,
even though internal Go code uses idiomatic Go naming.

## Rate Limiting

Public API rate limits depend on the customer's subscription plan; see
`pricing.md` and `subscriptions.md` for the exact limits per tier. Rate
limit responses use HTTP 429 with a `Retry-After` header.

## Error Format

All error responses follow a consistent envelope:

```json
{ "error": { "code": "string", "message": "string", "request_id": "string" } }
```

`request_id` is always included so support engineers can correlate a
customer-reported error with internal logs (see `observability.md` and
`support.md`).

## Internal gRPC APIs

Internal service-to-service APIs are defined with Protocol Buffers in a
shared `proto` repository. Internal APIs are not bound by the same
backward-compatibility guarantees as public APIs, but breaking changes still
require coordinating a rollout with all dependent teams.

## Documentation

Every public endpoint must have an OpenAPI (REST) or SDL (GraphQL) schema
entry, published automatically to the developer portal on each release.
