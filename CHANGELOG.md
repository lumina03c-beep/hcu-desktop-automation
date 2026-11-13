# Changelog

All notable changes to this project are documented here. The format follows Keep a Changelog principles and versions follow semantic versioning where practical.

## [5.4.0] - 2026-11-11

### Added

- Workspace telemetry schema extensions: `input_tokens`, `output_tokens`, and
  `cached_input_tokens` per event; recovery episode fields (`eligible`,
  `strategy`, `input_may_have_landed`, `failure_code`); a `safe_stopped` event
  outcome; and handoff segmentation timestamps (`prepare_started_at`,
  `target_ready_at`, `reobserve_completed_at`).
- `scripts/workspace_to_v2.py`, the explicit Workspace to V2 evaluation
  adapter; it refuses to fabricate `task_success` without an independent
  verification verdict, requires runtime-only metrics (snapshots, AX/GUI
  calls, duplicate mutations) via `--metrics-file`, and validates the record
  against `evaluations/v2/result.schema.json`.
- V2 summarization in `scripts/summarize_results.py`: records with
  `schema_version: "2.0.0"` are the primary evaluation format; V1 stays
  readable as a deprecated compatibility format and mixed V1/V2 batches are
  rejected.
- `telemetry_coverage` reporting in `scripts/workspace_metrics.py`: missing
  tool, model, token, and recovery telemetry stays `null` and is never
  reported as zero; a real zero requires an event stream that shows zero
  calls.
- Version consistency gate: `scripts/validate_skill.py` now fails when the
  `SKILL.md` frontmatter version differs from the latest CHANGELOG entry.
- CI now exercises Workspace metrics, V2 aggregation, and the Workspace to V2
  adapter on bundled examples.

### Changed

- `scripts/workspace_metrics.py` separates `agent_claimed_success` (Workspace
  claim) from `task_success` (independent verification; always `null` in
  Workspace metrics), splits token totals into input/output/cached sums
  (`total_tokens` replaces `token_cost`), counts recovery episodes with
  explicit `eligible`, `recovered`, `safe_stopped`, and `failed` outcomes, and
  reports handoff latency segments (prepare, target ready, reobserve, total)
  plus P90 aggregates and per-metric coverage.
- Workspace input robustness in `scripts/workspace_metrics.py`: BOM-tolerant
  reads (output stays BOM-free), schema validation against
  `schemas/workspace.schema.json`, explicit timezone-aware timestamp checks,
  and negative durations are errors instead of being clamped to zero.
- `evaluations/result.schema.json` (V1) is marked deprecated; new evaluation
  data must use `evaluations/v2/result.schema.json`.

### Safety

- `task_success` cannot be derived from a Workspace claim:
  `scripts/workspace_to_v2.py` requires `--verified` and `--verifier` and
  fails otherwise.
- No behavioral change to task execution, routing, or recovery rules.

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
