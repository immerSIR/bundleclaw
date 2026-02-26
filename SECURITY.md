# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in BundleClaw, **please do not open a public issue.**

Instead, report it privately:

1. **GitHub Security Advisories** (preferred): Use [GitHub's private vulnerability reporting](https://github.com/immerSIR/bundleclaw/security/advisories/new).
2. **Email**: Contact the maintainer directly via their [GitHub profile](https://github.com/immerSIR).

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Fix or mitigation**: Varies by severity, targeting < 30 days for critical issues

## Security Considerations

BundleClaw handles sensitive agent state that may include credentials, API keys, and private configuration. Users should be aware of:

### Bundle Contents

- **Full profile** bundles may contain secrets (API keys, tokens, credentials)
- Always use `--encrypt-pass` when exporting bundles that include credentials
- Delete `.bcz` files after successful migration

### Encryption

- BundleClaw uses **AES-256-GCM** with **PBKDF2-SHA256** key derivation (200,000 iterations)
- Encryption is optional and must be explicitly enabled via `--encrypt-pass`
- Choose strong, unique passphrases for bundle encryption

### Transport

- Use secure channels (SCP, SFTP) when transferring bundles between machines
- The built-in `transfer` command uses SCP by default
- Never transfer unencrypted bundles containing credentials over untrusted networks

### Storage

- Do not commit `.bcz` files to version control (already in `.gitignore`)
- Store encrypted bundles if long-term retention is needed
- Purge temporary bundles from `/tmp` after migration
