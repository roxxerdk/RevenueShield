# Security Policy

## Supported Versions

RevenueShield provides security updates and patches for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of RevenueShield and sensitive payment recovery workflows seriously.

If you discover a security vulnerability, please **DO NOT** open a public issue. Instead, report it privately:

1. **Email**: Send vulnerability details to `dhanush5240435@gmail.com` with the subject `[SECURITY] RevenueShield Vulnerability`.
2. **Details to Include**:
   - Description of the vulnerability and its potential impact.
   - Exact steps or proof-of-concept (PoC) to reproduce the issue.
   - Any relevant logs, payloads, or configurations (with secrets redacted).
3. **Response Timeline**:
   - Initial acknowledgement within **24 hours**.
   - Assessment and status update within **48 hours**.
   - Remediation and patched release within **7 days**.

## Security Guidelines & Zero-Hardcoding Guarantee

- RevenueShield enforces **Zero Hardcoding** of credentials, API secrets, and webhook secrets.
- All webhook requests are cryptographically validated using HMAC-SHA256 signatures.
- All audit log outputs automatically redact sensitive keys.
