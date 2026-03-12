# Contributing

Thanks for your interest in contributing.

## What to Contribute
- Bug reports
- Documentation improvements
- UI improvements
- Runtime management improvements
- Shared space and local model support
- Tests and developer tooling

## Before You Start
- Read `ARCHITECTURE.md` and `ROADMAP.md`.
- Open an issue before starting large changes.
- Keep proposals small, clear, and easy to review.

## Development Principles
- Prefer simple designs over clever ones.
- Keep user isolation intact.
- Do not bypass the model gateway.
- Keep private spaces and shared spaces clearly separated.
- Avoid changes that weaken auth, permissions, or auditability.

## Pull Request Rules
- One focused change per PR.
- Include a short description of the problem and the solution.
- Update docs when behavior changes.
- Add tests when possible.
- Keep breaking changes explicit.

## Commit Guidance
Use clear commit messages, for example:
- `feat: add shared space status API`
- `fix: prevent runtime start for disabled users`
- `docs: clarify local model routing`

## Security Issues
Do **not** report security vulnerabilities in public issues.
Please follow `SECURITY.md`.
