---
name: hcu-desktop-automation
description: Use when a dynamic UI task needs Browser (ego-browser) or Desktop (HCU) execution, staged engine routing, a persistent Task Workspace, cross-engine handoff, verified outcomes, or safe recovery; covers web, desktop, Office, settings, dialogs, canvases, hybrid browser-desktop tasks, workspace resume, and unknown side effects.
license: MIT
compatibility: Agent Skills-compatible clients. Browser tasks require the installed ego-browser skill; Desktop tasks require Microsoft HCU with AX/GUI. Python 3.10+ is needed only for the setup, validation, and evaluation scripts.
metadata:
  version: "5.2"
  upstream: "https://github.com/microsoft/Hybrid-Computer-Use"
---

# Dynamic UI RPA

One orchestrator for dynamic UI work: one Task Workspace, stage-level routing
to Browser or Desktop, verified outcomes, and recovery that never replays an
uncertain side effect. It adds no third UI engine.

## Scope and engines

- Use when the truth lives in a browser page, a native desktop window, or both;
  Browser = ego-browser, Desktop = HCU, and shell/file/CLI tools stay auxiliary.
- Use programmatic tools for pure file, API, CLI, or data work; as auxiliary
  support they never become a UI engine or trigger re-routing.
- Not for fixed, headless, or scheduled workflows a dedicated platform handles.

## Task Workspace

- Exactly one authoritative `workspace.json` per complete user task; resume it
  across engine switches and never fork or merge tasks.
- Store semantic facts only: goal, plan, receipts, handoffs, artifacts, result.
- Never store refs, `targetId`, GUI frames, coordinates, credentials, or raw
  DOM/AX trees.
- Update at meaningful nodes only; verify writes at creation and termination by
  re-read, and intermediate writes by content on the next read.

See `references/workspace-policy.md`; schema in `schemas/workspace.schema.json`.

## Dynamic routing

- Route per stage, not per click; Browser-first for web, Desktop for native UI,
  Hybrid only when both are required.
- Judge Browser and Desktop readiness independently; a missing engine must not
  fail a task that does not need it.
- Re-route only when the target, ownership, or interaction changes materially.

See `references/routing.md`.

## Execution loop

1. Build the Task Contract.
2. Create or resume the Workspace and the stage plan.
3. Observe the minimum state the next decision needs.
4. Execute with the selected engine; batch deterministic steps where safe.
5. Verify with L1/L2/L3 evidence and update the Workspace.
6. Hand off, recover, or terminate according to the contract.

See `references/task-contract.md`, `references/execution-policy.md`,
`references/browser-workflow.md`, `references/desktop-workflow.md`, and
`references/hybrid-workflow.md`.

## Efficiency

- One orientation observation per stage; later reads return decision fields.
- One script or batch per stage: act, wait for the terminal state, verify.
- Move bulk content through the clipboard, not keystroke storms.
- Cache validated app paths and the real Desktop folder before a handoff.
- Outcome-only stages take the shortest programmatic route; UI engines serve
  process contracts or live-UI oracles.

## Risk and evidence

- `R0` read-only: batch narrowly; `R1` reversible: batch and read back.
- `R2` external or hard to reverse: isolate, preview, confirm, verify.
- `L1` delivery; `L2` application/UI state; `L3` user outcome or artifact.
  Only contract-satisfying evidence completes a task.

See `references/contract.md` for HCU-specific execution rules.

## Recovery

- Read failure fields; classify whether input may have landed.
- Never replay `effect_unknown` or `partial_input_possible` without a fresh
  observation.
- After two attempts without new evidence, change mechanism or stop safely.
- Keep `recovered`, `task_completed`, `safe_stopped`, and `failed` distinct.

See `references/recovery.md`.

## Progressive disclosure

- Scope: `references/product-scope.md`; contract: `references/task-contract.md`
- Workspace: `references/workspace-policy.md`; routing: `references/routing.md`
- Engines: `references/browser-workflow.md`,
  `references/desktop-workflow.md`, `references/hybrid-workflow.md`
- Modes: `references/execution-policy.md`; HCU:
  `references/contract.md`, `references/platforms.md`
- Environments: `references/environments.md`; recovery: `references/recovery.md`
- Evaluation: `references/testing.md`, `references/setup.md`,
  `scripts/workspace_metrics.py`
- Examples: `examples/`
