<div align="center">

# BundleClaw

**Migrate OpenClaw agent state between machines in seconds.**

[![CI](https://github.com/immerSIR/bundleclaw/actions/workflows/ci.yml/badge.svg)](https://github.com/immerSIR/bundleclaw/actions/workflows/ci.yml)
[![npm version](https://img.shields.io/npm/v/bundleclaw?logo=npm&color=CB3837)](https://www.npmjs.com/package/bundleclaw)
[![PyPI version](https://img.shields.io/pypi/v/bundleclaw?logo=pypi&logoColor=white&color=3775A9)](https://pypi.org/project/bundleclaw/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Node.js](https://img.shields.io/badge/Node.js-%E2%89%A518-339933?logo=node.js&logoColor=white)](https://nodejs.org/)
[![Python](https://img.shields.io/badge/Python-%E2%89%A53.10-3776AB?logo=python&logoColor=white)](https://www.python.org/)

Export, transfer, and bootstrap your OpenClaw agent's complete state — memory, config, identity, credentials, and workspace — with a single command. Ships as **two fully interoperable implementations** (Node & Python) that share the same `.bcz` bundle format.

[Quick Start](#quick-start) · [Commands](#commands) · [Bundle Format](spec/FORMAT.md) · [Contributing](CONTRIBUTING.md)

</div>

---

## Highlights

- **One-step migration** — `export` on source, `bootstrap` on target. Done.
- **Dual runtime** — Use whichever ecosystem you prefer: `npx` or `uvx`. Bundles are 100% cross-compatible.
- **AES-256-GCM encryption** — Optional passphrase-based encryption with PBKDF2 key derivation (200k iterations).
- **Export profiles** — Ship everything (`full`), skip secrets (`no-credentials`), or transfer just personality (`memory-only`).
- **Automatic backups** — Every import creates a timestamped backup of the existing state before overwriting.
- **Integrity verification** — SHA-256 checksums embedded in the bundle manifest, verified on import.
- **Built-in transfer** — Copy bundles to remote hosts via SCP without leaving the CLI.
- **Health checks** — Bootstrap runs `openclaw doctor` and `openclaw status` after restore.

---

## Quick Start

### Install

Choose your runtime:

```bash
# Node.js (npm)
npm install -g bundleclaw

# Python (pip)
pip install bundleclaw
```

Or run directly without installing:

```bash
# Node.js
npx bundleclaw --help

# Python
uvx bundleclaw --help
```

### Export & Migrate

```bash
# 1. Export agent state (on source machine)
bundleclaw export \
  --source ~/.openclaw \
  --workspace ~/.openclaw/workspace \
  --profile full \
  --encrypt-pass 'strong-passphrase' \
  --out agent-state.bcz

# 2. Transfer to target machine
bundleclaw transfer \
  --bundle agent-state.bcz \
  --to user@target-host:/tmp/agent-state.bcz

# 3. Bootstrap on target (import + verify + restart)
bundleclaw bootstrap \
  --bundle /tmp/agent-state.bcz \
  --encrypt-pass 'strong-passphrase' \
  --target ~/.openclaw
```

---

## Commands

### `export`

Package OpenClaw state into a `.bcz` bundle.

```bash
bundleclaw export \
  --source <openclaw-home> \
  --workspace <workspace-path> \
  --out <output-file> \
  --profile <full|no-credentials|memory-only> \
  --encrypt-pass <passphrase>          # optional
```

| Flag | Default | Description |
|------|---------|-------------|
| `--source` | `~/.openclaw` | Path to OpenClaw home directory |
| `--workspace` | `~/.openclaw/workspace` | Path to agent workspace |
| `--out` | `agent-state.bcz` | Output bundle filename |
| `--profile` | `full` | Export profile (see below) |
| `--encrypt-pass` | — | Encrypt bundle with AES-256-GCM |

### `import`

Restore a bundle onto the target machine.

```bash
bundleclaw import \
  --bundle <bcz-file> \
  --target <openclaw-home> \
  --encrypt-pass <passphrase>          # if encrypted
```

> A timestamped backup of the existing state is created automatically before restore.

### `verify`

Run integrity checks after import.

```bash
bundleclaw verify --target <openclaw-home>
```

Checks for: `openclaw.json`, `workspace/SOUL.md`, `workspace/memory/` directory.

### `transfer`

Copy a bundle to a remote host via SCP.

```bash
bundleclaw transfer \
  --bundle <bcz-file> \
  --to <user@host:/path> \
  --scp-bin <scp>                      # optional, defaults to "scp"
```

### `bootstrap`

All-in-one: import + verify + optional service restart + health checks.

```bash
bundleclaw bootstrap \
  --bundle <bcz-file> \
  --target <openclaw-home> \
  --encrypt-pass <passphrase>          # if encrypted
  --restart-cmd <command>              # default: "openclaw gateway restart"
  --skip-restart                       # skip service restart
```

---

## Export Profiles

| Profile | Config | Credentials | Identity | Workspace | Memory |
|---------|:------:|:-----------:|:--------:|:---------:|:------:|
| `full` | Yes | Yes | Yes | Yes | Yes |
| `no-credentials` | Yes | No | No | Yes | Yes |
| `memory-only` | No | No | No | Yes | Yes |

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     BundleClaw                           │
├────────────────────────┬─────────────────────────────────┤
│     Node CLI           │         Python CLI              │
│  (TypeScript/npm)      │      (Typer/pip)                │
├────────────────────────┴─────────────────────────────────┤
│              Shared .bcz Bundle Format v1                │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ manifest.json│  │  payload/    │  │  AES-256-GCM   │  │
│  │  - checksums │  │  - config    │  │  encryption    │  │
│  │  - profile   │  │  - identity  │  │  (optional)    │  │
│  │  - metadata  │  │  - workspace │  │                │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## Security

BundleClaw handles sensitive agent state. Follow these guidelines:

- **Always encrypt** bundles that contain credentials (`--encrypt-pass`).
- **Use secure transport** (SCP/SFTP) when transferring bundles between machines.
- **Use `no-credentials`** profile when encryption isn't feasible.
- **Delete bundles** after successful migration — they may contain secrets.
- **Review the bundle format** specification at [`spec/FORMAT.md`](spec/FORMAT.md).

### Encryption Details

| Property | Value |
|----------|-------|
| Algorithm | AES-256-GCM |
| Key Derivation | PBKDF2-SHA256, 200,000 iterations |
| Salt | 16 bytes (random) |
| IV | 12 bytes (random) |
| Magic Header | `BCLAWENC1` (9 bytes) |

---

## Repository Layout

```
bundleclaw/
├── node-cli/              # Node.js implementation (TypeScript)
│   ├── src/index.ts       # CLI entry point
│   ├── package.json
│   └── tsconfig.json
├── python-cli/            # Python implementation (Typer)
│   ├── bundleclaw/
│   │   ├── __init__.py
│   │   └── cli.py         # CLI entry point
│   └── pyproject.toml
├── spec/
│   └── FORMAT.md          # Bundle format v1 specification
├── .github/
│   └── workflows/
│       ├── ci.yml         # Build verification on push/PR
│       └── release.yml    # Auto-publish to npm + PyPI on tags
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE                # MIT
├── SECURITY.md
└── README.md              # You are here
```

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Setting up the development environment
- Code style and conventions
- Submitting pull requests
- Reporting issues

---

## License

[MIT](LICENSE) &copy; 2026 [immersir](https://github.com/immerSIR)
