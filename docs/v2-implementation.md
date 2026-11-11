# Dynamic UI RPA Skill V2 — Phase 1 implementation record

Date: 2026-11-10  
Baseline: `main` / `253c6594baf54c8fa9fed42eb35cfe869eb93a46`  
Phase: 1 — Main Skill, routing, and Workspace Prompt management

## Scope delivered

- Lightweight Dynamic UI RPA orchestrator in `SKILL.md`.
- Browser (ego-browser) / Desktop (HCU) / Hybrid stage-level routing.
- One authoritative Task Workspace per user task.
- Draft 2020-12 Workspace schema and five lifecycle examples.
- Shared Task Contract, Workspace policy, and execution policy.
- Browser, Desktop, and Hybrid workflow references.
- Workspace schema, lifecycle, update, resume, handoff, mutation, and safety tests.
- V2 evaluation schema and synthetic Browser/Desktop/Hybrid example.
- Updated evaluation protocol with V2 metrics and synthetic/real separation.
- CI and offline validation updates for the new structure, examples, and evaluation schema.

No implementation code for a Workspace runtime, daemon, database, WebSocket
service, floating UI, or third UI engine was added. The Workspace remains an
Agent-managed JSON document.

## Files added

- `references/product-scope.md`
- `references/task-contract.md`
- `references/workspace-policy.md`
- `references/browser-workflow.md`
- `references/desktop-workflow.md`
- `references/hybrid-workflow.md`
- `references/execution-policy.md`
- `schemas/workspace.schema.json`
- `examples/workspace.initial.json`
- `examples/workspace.running.json`
- `examples/workspace.handoff.json`
- `examples/workspace.blocked.json`
- `examples/workspace.completed.json`
- `requirements-dev.txt`
- `tests/workspace_support.py`
- `tests/test_workspace_schema.py`
- `tests/test_workspace_lifecycle.py`
- `tests/test_workspace_update.py`
- `tests/test_workspace_resume.py`
- `tests/test_workspace_handoff.py`
- `tests/test_workspace_mutations.py`
- `tests/test_workspace_safety.py`
- `tests/test_workspace_evaluation.py`
- `evaluations/v2/result.schema.json`
- `evaluations/v2/example-results.json`
- `docs/v2-implementation.md`

## Files modified

- `SKILL.md` — replaced the HCU-only entry point with the Dynamic UI RPA
  orchestrator. The file is exactly 120 lines.
- `references/routing.md` — added first-level Browser/Desktop/Hybrid routing,
  independent readiness, stage-level routing, and switch guardrails while
  preserving HCU's internal AX/GUI routing.
- `references/recovery.md` — added the shared Dynamic UI RPA recovery
  principles while preserving HCU's error and entry-point lifecycle.
- `references/contract.md` — clarified that it is the HCU-specific execution
  contract and that the shared contract and Workspace are separate.
- `references/environments.md` — added Browser/Desktop ownership and
  single-input-stream boundaries for the dual-engine model.
- `references/testing.md` — added the Dynamic UI RPA V2 evaluation protocol,
  metrics, and synthetic/real separation rules.
- `README.md` and `README.zh-CN.md` — updated the product description, engine
  boundary, capability list, repository layout, and validation instructions.
- `docs/ARCHITECTURE.md` — replaced the HCU-only layer diagram with the dual
  engine + Workspace architecture.
- `scripts/validate_skill.py` — requires the V2 references, Workspace schema,
  examples, and validates their JSON syntax and `schema_version`.
- `.github/workflows/validate.yml` — installs `requirements-dev.txt` before
  validation and tests.
- `CHANGELOG.md` — added the `5.0.0` Phase 1 entry.

No existing HCU capability, test, evaluation schema, or setup adapter was
removed.

## Validation commands

Executed locally:

```bash
python -m pip install "jsonschema>=4.23,<5"
python scripts/validate_skill.py
python -m unittest discover -s tests -v
python scripts/summarize_results.py evaluations/example-results.json
python scripts/hcu_setup.py --help
```

## Results

| Check | Result |
| --- | --- |
| `scripts/validate_skill.py` | PASS |
| `python -m unittest discover -s tests -v` | PASS — 73/73 tests |
| Original V1 setup/summarizer tests | PASS — 15/15 preserved |
| New Workspace tests | PASS — 58/58 |
| Workspace examples against Draft 2020-12 schema | PASS — 5/5 |
| `scripts/summarize_results.py` | PASS |
| `scripts/hcu_setup.py --help` | PASS |
| `SKILL.md` line limit | PASS — 120/120 |
| Local links and required resources | PASS |

## Status classification

- **PASS**: offline structure validation, all 67 unit tests, schema
  validation, result aggregation, setup CLI help, and the 120-line
  `SKILL.md` limit.
- **NOT RUN**: real ego-browser navigation, real HCU AX/GUI execution, real
  Browser → Desktop → Browser handoff, real workspace persistence across a
  client restart, live model-call/token telemetry, and performance
  comparison.
- **BLOCKED**: none identified in this phase.
- **FAIL**: none in this phase.

The Workspace update tests use a temporary-directory simulation of the
Agent's safe update procedure. They prove schema, revision, read-back, and
conflict semantics, not host-specific persistence durability.

## Safety and compatibility checks

- Original HCU references and setup adapters remain intact.
- Original 15 unit tests remain intact and pass.
- `workspace.json` is the only authoritative task-state file.
- Browser refs, HCU refs, `targetId`, GUI frames, old coordinates, and
  credentials are excluded by schema and tested.
- `effect_unknown` cannot claim verified evidence and is not blindly
  replayable.
- Safe stop remains separate from completed.
- Revision conflict and persistence failure are detected and reported.
- No unapproved configuration writes were performed.
- No git commit, push, or remote publication was performed.

## Remaining work

Phase 2 must connect the two engines through real execution:

1. Verify ego-browser guide loading and live TaskSpace behavior.
2. Verify HCU doctor, AX, GUI, and Desktop readiness.
3. Execute real Browser and Desktop smoke tasks.
4. Execute real Browser → Desktop → Browser hybrid tasks.
5. Measure model calls, tool round trips, observation calls, token cost,
   recovery rate, and handoff latency.
6. Keep every unverified item marked `NOT RUN` until it is actually executed.
