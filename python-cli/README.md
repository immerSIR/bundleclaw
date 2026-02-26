# bundleclaw (Python CLI)

```bash
uvx bundleclaw export --source ~/.openclaw --workspace ~/.openclaw/workspace --profile full --encrypt-pass 'strong-pass' --out agent-state.bcz
uvx bundleclaw transfer --bundle agent-state.bcz --to user@host:/tmp/agent-state.bcz
uvx bundleclaw bootstrap --bundle agent-state.bcz --encrypt-pass 'strong-pass' --target ~/.openclaw
```
