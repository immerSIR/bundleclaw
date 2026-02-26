# BundleClaw Bundle Format v1

Extension: `.bcz` (zip container)

## Archive structure

```text
manifest.json
payload/
  openclaw.json
  credentials/...
  identity/...
  workspace/
    AGENTS.md
    SOUL.md
    USER.md
    TOOLS.md
    IDENTITY.md
    MEMORY.md
    HEARTBEAT.md
    memory/...
    config/...
```

## manifest.json

```json
{
  "format": "bundleclaw.v1",
  "createdAt": "2026-02-26T12:00:00Z",
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
    "payload/openclaw.json": "sha256:..."
  }
}
```

## Compatibility

- v1 readers must reject unknown major versions.
- Minor fields may be ignored safely.

## Import behavior

- Create backup of target before restore (`target/.bundleclaw-backup-<timestamp>/`).
- Restore files preserving relative paths.
- Never execute arbitrary scripts from bundle.
