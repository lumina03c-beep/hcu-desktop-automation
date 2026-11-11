# Architecture

## Ownership boundaries

Dynamic UI RPA is a staged orchestration layer. It does not replace either
execution engine.

```text
┌────────────────────────────────────────────────────────────┐
│ Agent Skill / Orchestrator                                  │
│ Task contract · one Task Workspace · stage-level routing     │
│ risk · evidence · handoff · recovery · final verification    │
└──────────────────────────┬─────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
┌───────▼─────────────────┐       ┌──────────▼───────────────┐
│ Browser Engine          │       │ Desktop Engine           │
│ ego-browser             │       │ Microsoft HCU            │
│ TaskSpace · snapshot    │       │ AX · GUI · refs          │
│ actions · waits         │       │ batching · platform rules │
└─────────────────────────┘       └──────────────────────────┘
        │                                     │
        └──────────────────┬──────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│ Host, OS, applications, and real business state             │
│ Browser pages · native windows · files · external receipts │
└────────────────────────────────────────────────────────────┘
```

- Incorrect agent decisions belong in the Orchestrator.
- Incorrect Browser behavior belongs in ego-browser.
- Incorrect Desktop behavior belongs in HCU or the native provider.
- The skill never hides an upstream defect behind an extra rule.

## Portable policy and client adapters

`SKILL.md` and the execution references contain no client-specific
configuration. `scripts/hcu_setup.py` owns HCU installation and client
registration. The Workspace is a host-provided JSON file, not a service or
database.

## Decision pipeline

1. **Task contract** — extract goal, target, constraints, risk, and success
   oracle before acting.
2. **Workspace** — create or resume one authoritative `workspace.json`.
3. **Stage routing** — choose Browser, Desktop, or Hybrid for the next stage.
4. **Sufficient observation** — acquire the minimum state needed for the next
   decision.
5. **Risk-aware batch** — execute with `R0`/`R1`/`R2` discipline and the
   current engine's batching rules.
6. **Evidence and recovery** — verify with `L1`/`L2`/`L3`, update the
   Workspace, and recover without replaying uncertain effects.
7. **Handoff or termination** — cross engines semantically, or finish the
   task only after independent verification.

## Workspace model

- One user task → one Workspace.
- One Browser goal → one ego TaskSpace.
- One Workspace owner → the Main Agent.
- One authority → `workspace.json`.
- Engine workflows return structured results; they never write the
  Workspace directly.

## Browser and Desktop boundaries

- Browser owns web page state, browser sessions, and browser-visible
  business results.
- Desktop owns native windows, Office apps, system dialogs, settings, and
  pixel-only visual state.
- Programmatic tools support a UI task but never become a third UI engine.
- Browser readiness and Desktop readiness are independent.
- Hybrid tasks preserve one Workspace across every handoff.

## Setup pipeline

```text
Read-only doctor
  → user reviews OS/deps/source/client/config changes
  → consent
  → clone pinned official source (or reuse clean existing tree)
  → official native build
  → official MCP smoke test (exactly AX and GUI)
  → native computer-use doctor
  → backup and merge selected client entry
  → restart/reconnect
  → live AX apps or GUI screenshot
```

The pipeline uses distinct terminal states: `built`, `protocol_verified`,
`native_attention_required`, `configured`, and `desktop_verified`. Only the
last supports normal Desktop automation. The script reports these stages; it
does not collapse them into a misleading “ready” message.

## Evaluation boundary

Static/unit CI validates policy structure, configuration merging, Workspace
schema, and aggregation. It does not prove native desktop input or live
browser execution. Regression tasks test known rules; frozen holdouts test
generalization. Independent L3 verification prevents agent self-reports from
becoming false-success evidence.
