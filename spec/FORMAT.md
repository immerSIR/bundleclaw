# BundleClaw Bundle Format v1

> Specification for the `.bcz` portable agent state bundle.

## Overview

A `.bcz` file is a standard **ZIP archive** containing a JSON manifest and a payload directory with the agent's state files. Optionally, the entire ZIP can be wrapped in an AES-256-GCM encryption envelope.

```
┌─────────────────────────────────────────┐
│            .bcz file (ZIP)              │
│                                         │
│  manifest.json        ← metadata        │
│  payload/                               │
│  ├── openclaw.json    ← agent config    │
│  ├── credentials/     ← API keys, etc.  │
│  ├── identity/        ← agent identity  │
│  └── workspace/                         │
│      ├── *.md          ← all workspace  │
│      │                    markdown files │
│      ├── memory/       ← memory store   │
│      └── config/       ← workspace cfg  │
└─────────────────────────────────────────┘
```

---

## File Extension

**`.bcz`** — short for "BundleClaw Zip".

Implementations should use this extension by default but accept any filename.

---

## Manifest (`manifest.json`)

The manifest is always at the root of the ZIP archive.

```json
{
  "format": "bundleclaw.v1",
  "createdAt": "2026-02-26T12:00:00.000Z",
  "encrypted": false,
  "source": {
    "openclawHome": "~/.openclaw",
    "workspace": "~/.openclaw/workspace"
  },
  "includes": {
    "openclawJson": true,
    "credentials": true,
    "identity": true,
    "workspaceCore": true,
    "workspaceMemory": true,
    "workspaceConfig": true
  },
  "checksums": {
    "payload/openclaw.json": "sha256:e3b0c44298fc1c149afbf4c8996fb924..."
  }
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `format` | string | Yes | Must be `"bundleclaw.v1"` |
| `createdAt` | string | Yes | ISO 8601 timestamp of bundle creation |
| `encrypted` | boolean | No | `true` if the ZIP was encrypted before writing |
| `source.openclawHome` | string | Yes | Original OpenClaw home path |
| `source.workspace` | string | Yes | Original workspace path |
| `includes.*` | boolean | Yes | Flags indicating which components are present |
| `checksums` | object | Yes | Map of `payload/...` paths to `sha256:...` hex digests |

### Include Flags

| Flag | Contents |
|------|----------|
| `openclawJson` | Root agent configuration (`payload/openclaw.json`) |
| `credentials` | API keys, tokens, service credentials (`payload/credentials/`) |
| `identity` | Agent identity files (`payload/identity/`) |
| `workspaceCore` | All workspace files and directories (excluding `memory/` and `config/`) |
| `workspaceMemory` | Memory store (`payload/workspace/memory/`) |
| `workspaceConfig` | Workspace configuration (`payload/workspace/config/`) |

---

## Export Profiles

Profiles control which include flags are set:

| Profile | openclawJson | credentials | identity | workspaceCore | workspaceMemory | workspaceConfig |
|---------|:------------:|:-----------:|:--------:|:-------------:|:---------------:|:---------------:|
| `full` | Yes | Yes | Yes | Yes | Yes | Yes |
| `no-credentials` | Yes | No | No | Yes | Yes | Yes |
| `memory-only` | No | No | No | Yes | Yes | No |

---

## Checksums

- Algorithm: **SHA-256**
- Format: `sha256:<hex-digest>` (lowercase)
- Computed over the raw file content before compression
- Verified on import by reading the file from the archive and comparing digests

---

## Encryption Envelope

When `--encrypt-pass` is used, the ZIP archive is encrypted before writing to disk. The resulting file has the following binary layout:

```
┌───────────┬────────────┬──────────┬──────────┬─────────────────┐
│  MAGIC    │   SALT     │    IV    │   TAG    │   CIPHERTEXT    │
│  9 bytes  │  16 bytes  │ 12 bytes │ 16 bytes │   variable      │
└───────────┴────────────┴──────────┴──────────┴─────────────────┘
```

| Component | Size | Description |
|-----------|------|-------------|
| Magic | 9 bytes | ASCII string `BCLAWENC1` — identifies encrypted bundles |
| Salt | 16 bytes | Random salt for key derivation |
| IV | 12 bytes | Random initialization vector for AES-GCM |
| Tag | 16 bytes | GCM authentication tag |
| Ciphertext | variable | Encrypted ZIP archive |

### Key Derivation

| Parameter | Value |
|-----------|-------|
| Algorithm | PBKDF2 |
| Hash | SHA-256 |
| Iterations | 200,000 |
| Key length | 32 bytes (256 bits) |
| Salt | 16 bytes (random per bundle) |

### Encryption

| Parameter | Value |
|-----------|-------|
| Algorithm | AES-256-GCM |
| IV length | 12 bytes |
| Tag length | 16 bytes |
| Input | Complete ZIP archive bytes |

---

## Import Behavior

1. **Detect encryption**: Check for `BCLAWENC1` magic header. If present, decrypt first.
2. **Parse manifest**: Read `manifest.json` from the ZIP root.
3. **Validate format**: Reject if `format` is not `bundleclaw.v1` (unknown major versions must be rejected).
4. **Create backup**: Copy existing target directory to `<target>.bundleclaw-backup-<timestamp>/` (sibling directory, not inside target).
5. **Extract payload**: Restore files from `payload/` into the target directory, preserving relative paths.
6. **Verify checksums**: Compare SHA-256 digests against manifest checksums.

### Safety Rules

- **Never execute** arbitrary scripts or binaries from a bundle.
- **Always backup** the target state before overwriting.
- **Reject unknown** major format versions (`bundleclaw.v2`, etc.).
- **Ignore unknown** minor fields safely (forward compatibility).

---

## Versioning

The format version follows a simple major-version scheme:

- **`bundleclaw.v1`** — current version, described in this document
- Readers **must reject** bundles with an unrecognized major version
- New optional fields may be added without a version bump
- Breaking changes to the archive structure require a new major version
