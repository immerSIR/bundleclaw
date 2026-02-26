# BundleClaw

**BundleClaw** makes OpenClaw agent migration simple: export your current state, transfer it, and bootstrap a new server in one flow.

Supports both ecosystems:
- **Node CLI** (`npm`, `npx`)
- **Python CLI** (`pip`, `uv`)

Both implementations use the same `.bcz` bundle format, so exports/imports are fully interoperable.

---

## What it does

- **export**: package OpenClaw state (memory, config, identity, credentials, workspace)
- **import**: restore a bundle onto a target `~/.openclaw`
- **verify**: run quick integrity checks after restore
- **transfer**: copy bundles to remote hosts via `scp`
- **bootstrap**: import + verify + optional gateway restart + health checks

### Export profiles

- `full` (default): everything needed for full migration
- `no-credentials`: excludes credentials/identity
- `memory-only`: personality + memory-focused transfer

### Security

- Optional bundle encryption via `--encrypt-pass`
- Backup is created before import/bootstrap restore
- Use encrypted storage/transport for full bundles (they may include secrets)

---

## Quick start

### Node (npm/npx)

```bash
npx bundleclaw export \
  --source ~/.openclaw \
  --workspace ~/.openclaw/workspace \
  --profile full \
  --encrypt-pass 'strong-pass' \
  --out agent-state.bcz

npx bundleclaw transfer \
  --bundle agent-state.bcz \
  --to user@host:/tmp/agent-state.bcz

npx bundleclaw bootstrap \
  --bundle agent-state.bcz \
  --encrypt-pass 'strong-pass' \
  --target ~/.openclaw
```

### Python (pip/uv)

```bash
uvx bundleclaw export \
  --source ~/.openclaw \
  --workspace ~/.openclaw/workspace \
  --profile full \
  --encrypt-pass 'strong-pass' \
  --out agent-state.bcz

uvx bundleclaw transfer \
  --bundle agent-state.bcz \
  --to user@host:/tmp/agent-state.bcz

uvx bundleclaw bootstrap \
  --bundle agent-state.bcz \
  --encrypt-pass 'strong-pass' \
  --target ~/.openclaw
```

---

## Repository layout

- `spec/` — shared bundle format docs
- `node-cli/` — Node implementation (npm/npx)
- `python-cli/` — Python implementation (pip/uv)
- `.github/workflows/` — CI + release automation

---
