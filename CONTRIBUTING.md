## How to Contribute

For large changes (new features, design changes), please open an issue before submitting a PR.
Small bug fixes and typos can be submitted directly as a PR.

## Development Setup

See [README.md](README.md) for setup instructions.

## Code Style

Follow [docs/dev-charter/CODE_STYLE.md](docs/dev-charter/CODE_STYLE.md).

Linting and formatting: `ruff check` / `ruff format` (scoped to `remote/` and `server/`).

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format (e.g. `fix: ...`, `feat: ...`).

## Pull Request Checklist

- [ ] No secrets or credentials included
- [ ] Lint passes (`ruff check`, `ruff format --check`)
- [ ] Type checks pass (`mypy`)
- [ ] Tests pass (`pytest`)
- [ ] Build succeeds
- [ ] New features include tests
- [ ] User-facing changes are documented
- [ ] Added entry to CHANGELOG.md [Unreleased] section (if applicable)
- [ ] Manually verified (if applicable)
