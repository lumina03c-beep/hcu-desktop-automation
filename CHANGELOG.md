# Changelog

All notable changes to this project are documented here. The format follows Keep a Changelog principles and versions follow semantic versioning where practical.

## [4.0.0] - 2026-11-08

### Added

- Agent Skills metadata, portability requirements, and client compatibility gates.
- Consent-based HCU doctor, pinned source installation, official build/smoke execution, and native doctor checks.
- Configuration adapters for OpenCode, Codex, Claude Code, Gemini CLI, Grok Build, and generic stdio MCP clients.
- Configuration backups, custom config paths, existing-tree reuse, and clean fast-forward updates.
- Mandatory task contract, observation sufficiency gate, route record, and R0/R1/R2 execution classes.
- L1/L2/L3 evidence model, mutation ledger, and explicit recovery outcomes.
- Frozen holdout methodology, A/B/C repeated runs, false-success measurement, result schema, and aggregation script.
- GitHub documentation, MIT license, security/contributing guidance, offline validation, unit tests, and multi-OS CI.

### Changed

- Channel routing now applies Programmatic-first reasoning to authorized service/client endpoints as well as files.
- Batching now splits at evidence-dependent decisions, window changes, uncertain state, and high-impact actions.
- Scenario recipes are explicitly fallback development examples rather than proof of generalization.
- Installation readiness now requires client restart/reconnect and a live AX/GUI observation.

### Safety

- Setup performs no changes by default and never silently elevates privileges.
- OpenCode JSONC is not automatically serialized or stripped of comments.
- Gemini configuration retains `trust:false`; no client approval bypass is introduced.
- Claude Code uses the official HCU schema adapter.
