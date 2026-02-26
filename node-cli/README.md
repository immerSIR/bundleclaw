<div align="center">

# BundleClaw — Node CLI

[![npm version](https://img.shields.io/npm/v/bundleclaw?logo=npm&color=CB3837)](https://www.npmjs.com/package/bundleclaw)
[![Node.js](https://img.shields.io/badge/Node.js-%E2%89%A518-339933?logo=node.js&logoColor=white)](https://nodejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](../LICENSE)

TypeScript implementation of the BundleClaw migration CLI.

</div>

---

## Install

```bash
# Global install
npm install -g bundleclaw

# Or run directly
npx bundleclaw --help
```

## Usage

```bash
# Export agent state
npx bundleclaw export \
  --source ~/.openclaw \
  --workspace ~/.openclaw/workspace \
  --profile full \
  --encrypt-pass 'strong-passphrase' \
  --out agent-state.bcz

# Import on target machine
npx bundleclaw import \
  --bundle agent-state.bcz \
  --target ~/.openclaw \
  --encrypt-pass 'strong-passphrase'

# Verify integrity
npx bundleclaw verify --target ~/.openclaw

# Transfer via SCP
npx bundleclaw transfer \
  --bundle agent-state.bcz \
  --to user@host:/tmp/agent-state.bcz

# Full bootstrap (import + verify + restart + health check)
npx bundleclaw bootstrap \
  --bundle agent-state.bcz \
  --encrypt-pass 'strong-passphrase' \
  --target ~/.openclaw
```

## Development

```bash
npm install
npm run dev -- --help        # Run without compiling
npm run build                # Compile TypeScript to dist/
```

### Tech Stack

- **TypeScript** (ES2022, strict mode)
- **Commander.js** for CLI argument parsing
- **adm-zip** for ZIP archive handling
- **Node crypto** for AES-256-GCM encryption

## Interoperability

Bundles created with this CLI are fully compatible with the [Python CLI](../python-cli/). The shared `.bcz` format is documented in [`spec/FORMAT.md`](../spec/FORMAT.md).

## License

[MIT](../LICENSE)
