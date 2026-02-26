<div align="center">

# BundleClaw — Python CLI

[![PyPI version](https://img.shields.io/pypi/v/bundleclaw?logo=pypi&logoColor=white&color=3775A9)](https://pypi.org/project/bundleclaw/)
[![Python](https://img.shields.io/badge/Python-%E2%89%A53.10-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](../LICENSE)

Python implementation of the BundleClaw migration CLI.

</div>

---

## Install

```bash
# pip
pip install bundleclaw

# uv
uv pip install bundleclaw

# Or run directly
uvx bundleclaw --help
```

## Usage

```bash
# Export agent state
bundleclaw export \
  --source ~/.openclaw \
  --workspace ~/.openclaw/workspace \
  --profile full \
  --encrypt-pass 'strong-passphrase' \
  --out agent-state.bcz

# Import on target machine
bundleclaw import \
  --bundle agent-state.bcz \
  --target ~/.openclaw \
  --encrypt-pass 'strong-passphrase'

# Verify integrity
bundleclaw verify --target ~/.openclaw

# Transfer via SCP
bundleclaw transfer \
  --bundle agent-state.bcz \
  --to user@host:/tmp/agent-state.bcz

# Full bootstrap (import + verify + restart + health check)
bundleclaw bootstrap \
  --bundle agent-state.bcz \
  --encrypt-pass 'strong-passphrase' \
  --target ~/.openclaw
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
bundleclaw --help
```

### Tech Stack

- **Typer** for CLI argument parsing (Click-based)
- **cryptography** for AES-256-GCM encryption
- **zipfile** (stdlib) for ZIP archive handling
- **hashlib** (stdlib) for SHA-256 checksums

## Interoperability

Bundles created with this CLI are fully compatible with the [Node CLI](../node-cli/). The shared `.bcz` format is documented in [`spec/FORMAT.md`](../spec/FORMAT.md).

## License

[MIT](../LICENSE)
