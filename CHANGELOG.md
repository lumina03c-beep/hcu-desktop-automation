# Changelog

All notable changes to this project are documented here. The format follows Keep a Changelog principles and versions follow semantic versioning where practical.

## [5.3.0] - 2026-11-11

### Added

- Oracle classification in `references/task-contract.md` and outcome-first
  routing in `references/routing.md`: outcome-only stages take the shortest
  programmatic route (data API, direct file write, direct URL); UI engines
  serve process contracts or live-UI oracles.
- File-first creation path in `references/desktop-workflow.md`: create the file
  through auxiliary tools and open it with a launch argument instead of an
  in-app New-file dialog.
- Compound auxiliary scripts that print per-step results in
  `references/execution-policy.md`.
- In-page deterministic branching and structured terminal receipts in
  `references/browser-workflow.md`.
- `execution.next_action` one-line directive rule and relaxed intermediate
  write verification in `references/workspace-policy.md`.

### Changed

- `SKILL.md` Efficiency adds the outcome-first routing principle.
- Dropped a cross-task environment cache after adversarial review: negligible
  gain once preflight is batched, and it adds concurrency and invalidation
  risk.

## [5.2.0] - 2026-11-11

### Changed

- Condensed `SKILL.md` from 120 to 97 lines by merging scope and engines,
  tightening Workspace, routing, risk, and recovery rules, and keeping the full
  progressive-disclosure map.
- Removed duplicated rules and merged overlapping sections in
  `references/execution-policy.md`, `references/browser-workflow.md`,
  `references/desktop-workflow.md`, `references/environments.md`,
  `references/workspace-policy.md`, `references/recovery.md`, and
  `references/testing.md`; all behavioral rules remain covered.
- Merged the duplicate V2 and core metric tables in `references/testing.md` and
  folded observation guidance into the observation budget.

## [5.1.0] - 2026-11-10

### Added

- Efficiency contract in `SKILL.md`: one observation per stage, one stage script or batch, clipboard delivery for bulk text, and an environment cache before handoff.
- Observation budget, round-trip budget, and telemetry rules in `references/execution-policy.md`.
- Stage-script shape, page lifecycle, long-lived product handling, and user-control guidance in `references/browser-workflow.md`.
- Clipboard delivery for rich editors, mid-batch title-change recovery, and environment preflight in `references/desktop-workflow.md`.
- Environment preflight and cache guidance in `references/environments.md`, including redirected Desktop folders and non-standard application paths.
- Optional `environment` and `events` fields in the Workspace schema, with example telemetry in `examples/workspace.completed.json`.
- `scripts/workspace_metrics.py` and tests that compute Task Completion Rate, End-to-End Latency, Model Calls, Tool Round Trips, Token Cost, Recovery Rate, and Handoff Latency from Workspace files.
- Workspace telemetry mapping in `references/testing.md` and telemetry policy in `references/workspace-policy.md`.

### Changed

- `SKILL.md` remains within the 120-line project limit and now links the metrics script.
- Recovery guidance treats `user_control` as a normal ownership transfer and documents the interrupted-batch fallback.

## [5.0.0] - 2026-11-10

### Added

- Dual-engine Dynamic UI RPA orchestration: Browser (ego-browser), Desktop (HCU), and Hybrid staging.
- One authoritative Task Workspace per user task, with Draft 2020-12 schema, revision, lifecycle, handoff, mutation, artifact, and result contracts.
- Workspace examples for initial, running, handoff, blocked, and completed states.
- V2 evaluation result schema and synthetic Browser/Desktop/Hybrid example.
- Shared task contract, workspace policy, product scope, browser workflow, desktop workflow, hybrid workflow, and execution policy references.
- Stage-level dynamic routing with independent Browser and Desktop readiness.
- Unified Dynamic UI RPA recovery principles and dual-engine environment ownership boundaries.
- Development dependency for full JSON Schema validation and CI installation.
- Workspace schema, lifecycle, update, resume, handoff, mutation, safety, and evaluation tests.

### Changed

- `SKILL.md` is now a lightweight Dynamic UI RPA orchestrator and remains within the 120-line project limit.
- Routing now separates first-level Browser/Desktop/Hybrid routing from HCU's internal AX/GUI routing.
- README, Chinese README, and architecture documentation now describe the dual-engine and Workspace model.
- Offline validation now requires the V2 references, Workspace schema, and examples.
- CI installs the development dependency before running tests.

### Safety

- Browser element refs, HCU refs, `targetId`, GUI frames, old coordinates, and credentials are explicitly excluded from Workspace persistence.
- `effect_unknown` and `partial_input_possible` remain non-replayable without fresh observation.
- A safe stop remains a terminal state and is never counted as task success.
- No new runtime service, database, WebSocket, floating UI, or third UI engine was introduced.

## [4.0.0] - 2026-11-08

### Added

- Agent Skills metadata, portability requirements, and client compatibility gates.
- Consent-based HCU doctor, pinned source installation, official build/smoke execution, and native doctor checks.
- Client-independent default install output: build HCU and print a generic stdio MCP entry without writing client configuration.
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
