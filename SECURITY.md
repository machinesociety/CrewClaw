# Security Policy

## Supported Versions
Security fixes are expected for:
- the current main branch
- the latest released minor version

Older versions may not receive fixes.

## Reporting a Vulnerability
Please do **not** open a public issue for security reports.

Report vulnerabilities privately to the maintainers first.
Before publishing this repository, replace this line with a real contact channel such as:

- `security@your-domain.com`
- or a private security reporting form

## What to Include
Please include:
- affected component
- impact
- reproduction steps
- logs or screenshots if helpful
- any suggested fix or mitigation

## Response Expectations
Maintainers should:
- acknowledge the report
- validate the issue
- prepare a fix
- publish a coordinated update when ready

## Security Principles
- User runtimes must remain isolated.
- Workspace routes must stay behind authentication.
- Model access should go through the unified gateway.
- Secrets must not be exposed in client-side code or public logs.
- Shared spaces and local folder access must use explicit permissions.
