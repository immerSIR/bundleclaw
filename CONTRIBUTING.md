# Contributing to BundleClaw

Thank you for your interest in contributing to BundleClaw! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)
- [Style Guide](#style-guide)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

BundleClaw is a dual-runtime project with implementations in both Node.js (TypeScript) and Python. Changes to CLI behavior should be reflected in **both** implementations to maintain interoperability.

### Key Principle

Both CLIs must produce and consume identical `.bcz` bundles. If you change the bundle format, update **both** implementations and the [format specification](spec/FORMAT.md).

## Development Setup

### Prerequisites

- Node.js >= 18
- Python >= 3.10
- Git

### Node CLI

```bash
cd node-cli
npm install
npm run dev -- --help        # Run in development mode
npm run build                # Compile TypeScript
```

### Python CLI

```bash
cd python-cli
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install -e .
bundleclaw --help            # Run the CLI
```

## Making Changes

1. **Fork** the repository and create your branch from `main`.
2. **Make your changes** in the appropriate directory (`node-cli/`, `python-cli/`, or `spec/`).
3. **Keep parity** — if you change CLI behavior, update both implementations.
4. **Update the spec** — if you change the bundle format, update `spec/FORMAT.md`.
5. **Update the changelog** — add your changes under `[Unreleased]` in `CHANGELOG.md`.
6. **Test your changes** manually with real OpenClaw state or mock directories.

### Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feat/<short-description>` | `feat/export-compression` |
| Bug fix | `fix/<short-description>` | `fix/checksum-validation` |
| Docs | `docs/<short-description>` | `docs/encryption-guide` |
| Chore | `chore/<short-description>` | `chore/update-deps` |

## Pull Request Process

1. Ensure your PR description clearly explains the **what** and **why**.
2. Link any related issues (e.g., `Closes #12`).
3. Verify that CI passes (both Node and Python builds).
4. Keep PRs focused — one feature or fix per PR.
5. Be responsive to review feedback.

### PR Checklist

- [ ] Both implementations updated (if applicable)
- [ ] `spec/FORMAT.md` updated (if bundle format changed)
- [ ] `CHANGELOG.md` updated
- [ ] CI passes
- [ ] No secrets or credentials committed

## Reporting Issues

### Bug Reports

Please include:

- **Runtime**: Node or Python (and version)
- **OS**: Operating system and version
- **Steps to reproduce**: Minimal commands to trigger the bug
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Error output**: Full error messages or stack traces

### Feature Requests

Please include:

- **Problem**: What problem does this solve?
- **Proposed solution**: How should it work?
- **Alternatives considered**: What other approaches did you think of?
- **Scope**: Does this affect one or both runtimes?

## Style Guide

### TypeScript (Node CLI)

- Strict mode enabled (`"strict": true` in `tsconfig.json`)
- ES modules (`"type": "module"`)
- Use `const` by default, `let` when reassignment is needed
- Prefer early returns over nested conditionals

### Python (Python CLI)

- Python 3.10+ syntax (use `|` union types, `match` where appropriate)
- Type hints on function signatures
- Follow PEP 8 conventions
- Use `pathlib.Path` instead of `os.path`

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add gzip compression to export
fix: handle missing workspace directory gracefully
docs: update encryption section in README
chore: bump typescript to 5.9
```

---

Thank you for helping make BundleClaw better!
