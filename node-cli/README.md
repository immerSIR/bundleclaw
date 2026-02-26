# bundleclaw (Node CLI)

```bash
npx bundleclaw export --source ~/.openclaw --workspace ~/.openclaw/workspace --profile full --encrypt-pass 'strong-pass' --out agent-state.bcz
npx bundleclaw transfer --bundle agent-state.bcz --to user@host:/tmp/agent-state.bcz
npx bundleclaw bootstrap --bundle agent-state.bcz --encrypt-pass 'strong-pass' --target ~/.openclaw
```
