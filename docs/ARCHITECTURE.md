# Architecture

## Ownership boundaries

```text
┌────────────────────────────────────────────────────────────┐
│ L3: Agent Skill                                            │
│ Task contract · state routing · risk · batching · evidence │
│ recovery · reporting · client-independent policy           │
└──────────────────────────┬─────────────────────────────────┘
                           │ MCP: AX / GUI
┌──────────────────────────▼─────────────────────────────────┐
│ L2: Microsoft Hybrid Computer Use                          │
│ Go core · refs · canonical AX snapshot · GUI layout lease  │
│ action validation · waits · diffs · native provider bridge │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│ L1: OS and applications                                    │
│ Windows UIA/Win32 · macOS AXUIElement/CoreGraphics         │
│ Linux AT-SPI2/X11 · real application and filesystem state  │
└────────────────────────────────────────────────────────────┘
```

The skill does not reimplement HCU. Incorrect agent decisions belong in L3; incorrect refs, guards, tool results, or native behavior belong in L2/L1 and should be reproduced upstream rather than hidden by a skill rule.

## Portable policy and client adapters

`SKILL.md` and the execution references contain no client-specific configuration. `scripts/hcu_setup.py` owns installation and client registration. This separation lets multiple agents share the same decision policy while respecting different MCP config formats and schema requirements.

Claude Code is intentionally different: its adapter is provided by HCU and must remain in the launch command. OpenCode current versions use direct native tools (`codemode:false`). Generic clients must pass the documented schema/image/session compatibility gate before mutation.

## Decision pipeline

### 1. Task contract

Extract the business goal, target objects, explicit method versus outcome-only intent, state owner, constraints, unsaved work, risk, cleanup, and minimum success evidence. Missing information that affects side effects triggers observation or a user question.

### 2. Sufficient observation

Read only what the next decision needs, but do not confuse “one read” with “enough state.” Establish target identity, ownership, current value, actionability, live ref/frame, and evidence source. Partial coverage is unknown, not absence.

### 3. Route record

Record primary channel, fallback, evidence channel, and switch condition. Re-route when state ownership, addressability, visual necessity, or evidence needs change. Programmatic tools remain available throughout; they are not a one-time preflight choice.

### 4. Risk-aware batch

- R0 reads: narrow and inexpensive.
- R1 reversible mutations: deterministic same-window batches with readback.
- R2 high-impact/external mutations: isolated target/payload preview, required confirmation, and L3 verification.

Batch limits are tool constraints, not targets. Split at evidence-dependent decisions, window changes, uncertain state, and R2 boundaries.

### 5. Evidence and recovery

L1 delivery and L2 application state do not replace L3 user outcomes. Every mutation sequence maintains a ledger of requested action, payload, possible input, observed effect, unknowns, next safe read, and restoration. Two attempts without new evidence require a mechanism/channel change or a stop.

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

The pipeline uses distinct terminal states: `built`, `protocol_verified`, `native_attention_required`, `configured`, and `desktop_verified`. Only the last supports normal automation. The script reports these stages; it does not collapse them into a misleading “ready” message.

## Evaluation boundary

Static/unit CI validates policy structure, configuration merging, and aggregation. It does not prove native desktop input. Regression tasks test known rules; frozen holdouts test generalization. Independent L3 verification prevents agent self-reports from becoming false-success evidence.
