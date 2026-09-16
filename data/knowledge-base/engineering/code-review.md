# Code Review Policy

Code review is mandatory for every change merged into any Acme Cloud
repository.

## Standard Reviews

A pull request needs at least one approval from someone other than the
author before it can be merged. Reviewers are expected to check for
correctness, test coverage, and adherence to `coding-standards.md`.

## Security-Sensitive Changes

Changes that touch authentication, authorization, secrets handling, or
billing logic require an additional review from a designated security
reviewer (a member of the security team, not just any engineer). This is
enforced by a CODEOWNERS rule on the relevant directories.

## Review SLAs

Reviewers are expected to provide an initial response within one business
day. If a pull request is blocking an active P1 incident fix, the requester
may ping the on-call security reviewer directly and expect a response within
30 minutes, per `incident-response.md`.

## Review Size

Pull requests should be kept small — under 400 lines of diff where
practical — to keep review quality high. Larger refactors should be broken
into a sequence of smaller, reviewable pull requests, or discussed with the
team in advance.

## Automated Checks

Reviews happen only after automated checks pass: lint, unit tests, and the
diff-coverage gate described in `testing.md`. Reviewers are not expected to
manually verify things a machine already checked.

## Disagreements

If author and reviewer disagree after discussion, either party may request a
third opinion from the team's tech lead. Tech leads have final say on
technical disagreements within their own team's codebase.
