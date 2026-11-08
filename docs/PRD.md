# HCU Desktop Automation Skill — Product Requirements

## Product

- **Name:** `hcu-desktop-automation`
- **Version:** 4.0 development line
- **Form:** Agent Skills-compatible directory plus standard-library setup/evaluation tooling
- **Upstream:** Microsoft Hybrid Computer Use MCP
- **License:** MIT

## Mission

Help agents complete desktop goals by understanding the task, selecting the channel where state lives, executing with explicit risk and state contracts, and finishing with independent evidence. Make failure visible, recoverable when safe, and bounded when not.

## Users

- **Agent users:** install once, use natural-language desktop tasks, and see honest outcomes.
- **Automation engineers:** maintain portable rules rather than application-specific click recipes.
- **Reviewers/security owners:** inspect risk boundaries, evidence, configuration changes, and reproducible evaluation.

## Goals

1. Support unseen applications through state ownership and evidence-based routing.
2. Separate action success from application state and persisted/business outcomes.
3. Reduce model round trips without batching across uncertainty or high-impact boundaries.
4. Make refs, GUI frames, waits, native input guards, and recovery fields explicit.
5. Provide consent-based HCU source installation and configuration for multiple MCP clients.
6. Measure regression and generalization separately, including false success.

## Non-goals

- Reimplement HCU, native providers, or another desktop automation server.
- Promise 100% task success or unattended operation on a shared signed-in desktop.
- Install dependencies, elevate privileges, or rewrite client configuration without consent.
- Treat successful build/config/MCP handshake as proof of desktop readiness.
- Maintain an application whitelist or convert every failure into a private app recipe.
- Publish unredacted user desktop evidence.

## Functional requirements

### FR-1 Portable skill

Use a valid Agent Skills `SKILL.md`, progressive disclosure, and relative resource paths. Keep client configuration outside the core execution policy.

### FR-2 Task contract

Before acting, derive goal, targets, constraints, method constraints, state owner, preconditions, unsaved work, mutation risk, cleanup, and minimum evidence. Observe or ask when missing information affects side effects.

### FR-3 Channel routing

Support Programmatic, AX, and GUI throughout the task. Record primary/fallback/evidence channels and switch conditions. Prefer authorized typed endpoints when they preserve the requested session and outcome.

### FR-4 Execution contract

Support live refs/frames, scoped observation, conditional waits, effect/diff reads, native platform guards, and same-window deterministic batching. Split at evidence-dependent decisions, window changes, uncertain mutations, and R2 actions.

### FR-5 Evidence

Use L1 for delivery, L2 for application state, and L3 for verified outcome/persistence. Saving, deletion, sending, purchasing, publishing, and security changes require L3.

### FR-6 Recovery

Read side-effect fields first, maintain a mutation ledger, and never replay uncertain input. After two attempts without new evidence, change mechanism/channel or stop. Distinguish recovered, completed, safe-stopped, and failed.

### FR-7 Setup

Provide read-only doctor, pinned official source clone, official native build and smoke test, native doctor, config backup/merge, generic config output, and explicit restart/live-verification guidance.

### FR-8 Client adapters

Support OpenCode current/legacy JSON, guided OpenCode JSONC, Codex TOML, Claude Code with the official adapter, Gemini CLI JSON, Grok Build TOML, and generic stdio MCP output. Preserve unrelated settings.

### FR-9 Evaluation

Keep an 18-row regression matrix and require at least six frozen holdout cases for generalization claims. Compare no skill, previous/basic skill, and candidate skill under controlled budgets with at least five runs per condition.

## Non-functional requirements

- **Portability:** setup and tests use Python standard library only.
- **Safety:** no silent installs, sudo, trust bypass, credential exposure, or config loss.
- **Efficiency:** avoid unnecessary full trees/screenshots and repeated model turns.
- **Honesty:** distinguish implemented adapters, static tests, protocol verification, and native desktop verification.
- **Reproducibility:** preserve raw failures, platform/client/model/build metadata, and machine-readable results.
- **Maintainability:** core principles remain small; detailed behavior lives in focused references.

## Metrics

| Metric | Definition |
| --- | --- |
| Task Success Rate | Independently verified completions / runs |
| False Success Rate | Claimed success but independent verification failed / runs |
| Interaction Count | HCU calls; shell/API calls reported separately |
| Model Turn Count | Model decision rounds |
| Completion Latency | Wall time to a verified terminal state |
| Token Consumption | Input/output tokens or explicit unknown |
| Recovery Rate | Recovered episodes / eligible failed episodes |
| Safe Stop Rate | Correctly stopped unsafe/unknown tasks / applicable tasks |

## Acceptance criteria

### Repository/static

- Valid skill metadata and resource references.
- Offline validator, unit tests, evaluation schema, and multi-OS CI pass.
- README documents installation, compatibility limits, safety, and verification.
- Setup doctor and config output perform no writes.
- Config writers preserve unrelated entries and create backups.

### Native/client

- Official smoke test exposes exactly `AX` and `GUI` on each built platform.
- `computer-use doctor` passes or its unresolved native warnings are reported.
- Each client passes schema, image forwarding, and persistent-session checks.
- A live read-only AX and GUI observation succeeds before mutation.
- Holdout claims include raw, independently verified results; synthetic examples are never presented as benchmarks.

## Delivery status

Version 4.0 implements the repository/static scope and client configuration adapters. Native provider behavior and every client adapter still require local interactive-desktop verification on the user's exact OS/client versions. The repository intentionally does not convert earlier PRD run counts into new v4.0 benchmark claims without the underlying result records.

## Roadmap

1. Validate all client adapters on their current stable releases.
2. Add automated native read-only smoke runs to disposable Windows/macOS/Linux workers.
3. Publish a versioned holdout suite with independently checked results.
4. Add optional local telemetry, off by default, with redaction and no desktop content collection.
