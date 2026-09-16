# Coding Standards

All engineering teams at Acme Cloud follow a shared set of coding standards
to keep the codebase consistent and maintainable across services.

## Languages

The primary backend language is Go, used for `ingest-service`,
`alerting-service`, and `auth-service`. `query-service` is written in
TypeScript (Node.js) to share code with the frontend team. The billing engine
is written in Python because of its numerical libraries. Frontend
applications are written in TypeScript with React.

Acme Cloud does not currently have a documented standard for Finance,
Sales, or other non-engineering business functions — those teams choose
their own tooling independently and it is not tracked in this handbook.

## Style and Linting

- Go code must pass `gofmt` and `golangci-lint` with the shared ruleset in
  the `platform-lint-config` repository.
- TypeScript code must pass `eslint` with the `@acme/eslint-config` package.
- Python code must be formatted with `black` and type-checked with `mypy` in
  strict mode.

## Commit and Branching Conventions

Acme Cloud uses trunk-based development. Feature branches are short-lived
(ideally under three days) and merged to `main` via pull request. Commit
messages follow the Conventional Commits format (`feat:`, `fix:`, `chore:`,
etc.) so that release notes can be generated automatically.

## Code Review

All changes require at least one approving review before merge. See
`code-review.md` for the detailed review policy, including required
reviewers for security-sensitive changes.

## Testing Expectations

New code must include unit tests, and any change to a public API must
include integration tests. See `testing.md` for coverage thresholds and the
test pyramid used across teams.

## Documentation

Every service must maintain a `README.md` with a service description, local
setup instructions, and a link to its on-call runbook. Public APIs must be
documented following the conventions in `api-design.md`.
