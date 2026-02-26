# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-02-26

### Fixed

- Backup path created as sibling directory instead of inside target, preventing self-copy recursion error on existing targets
- Export now includes all workspace files, not just hardcoded core files (e.g., `TASKS_DONE.md` now migrates)

## [0.1.0] - 2026-02-26

### Added

- Node CLI implementation (TypeScript) — installable via `npm` / `npx`
- Python CLI implementation (Typer) — installable via `pip` / `uvx`
- Shared `.bcz` bundle format v1 (ZIP container with JSON manifest)
- Five CLI commands: `export`, `import`, `verify`, `transfer`, `bootstrap`
- Export profiles: `full`, `no-credentials`, `memory-only`
- Optional AES-256-GCM bundle encryption with PBKDF2 key derivation
- SHA-256 integrity checksums in bundle manifest
- Automatic timestamped backups before import/restore
- SCP-based remote transfer via `transfer` command
- Bootstrap command with health checks (`openclaw doctor`, `openclaw status`)
- CI pipeline for both runtimes (GitHub Actions)
- Automated release publishing to npm and PyPI on git tags

[Unreleased]: https://github.com/immerSIR/bundleclaw/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/immerSIR/bundleclaw/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/immerSIR/bundleclaw/releases/tag/v0.1.0
