# Contributing

1. Branch from `master`: `feat/…`, `fix/…`, `docs/…`.
2. Use [Conventional Commits](https://www.conventionalcommits.org/) (`feat: add --quality flag`).
3. Before pushing run `make check` (format check, lint, mypy, tests).
4. Update `docs/` and `docs/changelog.md` when behaviour changes.
5. Open a PR; CI must be green on Linux, macOS and Windows.

## PR checklist

- [ ] Tests added/updated
- [ ] `make check` passes locally
- [ ] Docs and changelog updated
