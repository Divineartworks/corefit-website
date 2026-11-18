# Security Policy

## Reporting A Vulnerability

Do not create a public issue for secrets, authentication bypasses, or exploitable vulnerabilities.

Report privately through GitHub private vulnerability reporting if enabled. If it is not enabled, contact the repository owner directly.

## Secret Handling

- Never commit production secrets.
- Use `.env.example` for required variable names.
- Store CI secrets in GitHub Actions secrets or environment secrets.
- Rotate any exposed credential immediately.
- Treat leaked credentials as compromised even if the repository is private.

