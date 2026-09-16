---
name: conventional-commit
description: 'Generate a Conventional Commits-style commit message and stage/commit the change. Use when the user asks to commit, write a commit message, "conventional commit", or wants staged changes turned into a git commit following type(scope): description format.'
---

# Conventional Commit

## When to Use
- User asks to commit changes, write a commit message, or "make a conventional commit"
- Staged or unstaged changes need a standardized `type(scope): description` message

## Procedure

1. Run `git status` to see changed files.
2. Run `git diff` (unstaged) and `git diff --cached` (staged) to understand the actual change.
3. Decide what to stage:
   - If the conversation makes clear which files belong to this change, stage only those with `git add <file>...`.
   - If the context is shallow (no clear file-level intent), stage everything with `git add -A`.
4. Build the commit message using the structure below.
5. Show the constructed commit message to the user and ask for confirmation before committing — do not run `git commit` unprompted.
6. On confirmation, run:
   ```bash
   git commit -m "type(scope): description"
   ```
   Add `-m` blocks (or a heredoc body) for the optional body/footer if present.

## Commit Message Structure

```xml
<commit-message>
    <type>feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert</type>
    <scope>(optional area of the codebase affected)</scope>
    <description>A short, imperative summary of the change</description>
    <body>(optional: more detailed explanation)</body>
    <footer>(optional: e.g. BREAKING CHANGE: details, or issue references)</footer>
</commit-message>
```

## Examples

- `feat(parser): add ability to parse arrays`
- `fix(ui): correct button alignment`
- `docs: update README with usage instructions`
- `refactor: improve performance of data processing`
- `chore: update dependencies`
- `feat!: send email on registration` with footer `BREAKING CHANGE: email service required`

## Validation

- **type**: required, must be one of the allowed types. See the [Conventional Commits spec](https://www.conventionalcommits.org/en/v1.0.0/#specification).
- **scope**: optional, recommended when it clarifies which area changed.
- **description**: required, imperative mood (e.g. "add", not "added"), no trailing period.
- **body**: optional, explain *why* not just *what*.
- **footer**: optional, use for `BREAKING CHANGE:` notes or issue references (e.g. `Closes #123`).
