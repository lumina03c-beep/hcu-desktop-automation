<p align="center">
  <h1 align="center">HCU Desktop Automation</h1>
</p>

<p align="center">
  <em>A successful click is not a completed task.</em>
</p>

<p align="center">
  <a href="https://github.com/lumina03c-beep/hcu-desktop-automation/actions/workflows/validate.yml"><img src="https://github.com/lumina03c-beep/hcu-desktop-automation/actions/workflows/validate.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/license-MIT-111111?style=flat-square" alt="MIT license">
  <img src="https://img.shields.io/badge/python-3.10%2B-111111?style=flat-square" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-111111?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/agents-Agent%20Skills-111111?style=flat-square" alt="Agent Skills">
</p>

<p align="center">
  <a href="README.md">English</a> &middot; <a href="README.zh-CN.md">简体中文</a>
</p>

---

An Agent Skills-compatible decision layer for dynamic UI RPA across **Browser (ego-browser)** and **Desktop (Microsoft HCU)**. It helps agents keep one authoritative Task Workspace, route each stage to the right engine, batch deterministic work, verify real outcomes, recover without blind retries, and stop safely when evidence is insufficient.

The repository also includes a consent-based bootstrapper that clones and builds the official HCU MCP server and configures MCP-capable agents.

## What this is — and what it is not

**This project is not HCU.** It is a set of instructions that tells an AI agent *how to use* HCU well.

| | This project | Microsoft HCU |
| --- | --- | --- |
| What it is | Markdown policy + Python setup helper | The actual MCP server, CLI, and native desktop providers |
| Written in | Markdown, Python (stdlib only) | Go, Swift, C#, TypeScript |
| Installed how | `git clone` this repo | Built from source, or via `scripts/hcu_setup.py` |

- This repository contains **no HCU source code and no HCU binary**. `scripts/hcu_setup.py` clones `microsoft/Hybrid-Computer-Use` into a *separate* directory outside this repo and builds it there.
- Browser tasks require the separately installed ego-browser skill. Desktop tasks require HCU. Browser-only tasks do not require HCU, and Desktop-only tasks do not require ego-browser.
- Bugs in the actual clicking, screenshotting, or accessibility tree belong to [Microsoft's issue tracker](https://github.com/microsoft/Hybrid-Computer-Use/issues), not this one.
- "HCU" and "Hybrid Computer Use" refer to the Microsoft project. This repository is an independent, unaffiliated companion.

## Why this skill exists

A successful click is not a completed task. Most desktop automation fails not because the click missed, but because nobody checked what happened afterward. This skill turns desktop automation into a closed loop:

```text
Task contract → state ownership → sufficient observation → channel route
→ risk-aware action batch → effect/diff → independent outcome evidence
→ recover, re-route, or stop
```

Key capabilities:

- **Task contract** — goal, target, constraints, preconditions, risk, and success oracle before acting.
- **Dynamic UI routing** — Browser-first for web work, Desktop for native UI, Hybrid only when a task truly crosses both engines.
- **Task Workspace** — one authoritative JSON per user task, with verified steps, handoffs, mutations, and artifacts.
- **State-based routing** — choose the channel by where truth lives, not by application-specific recipes.
- **Risk-aware execution** — R0 read-only, R1 reversible mutation, R2 high-impact/external mutation.
- **Evidence levels** — L1 input delivery, L2 application state, L3 verified user outcome or persisted artifact.
- **Live-state safety** — session-scoped refs, GUI frame leases, Windows input guards, and conditional waits.
- **Recovery discipline** — mutation ledger, side-effect classification, two-strike rule, and explicit safe stops.
- **Generalization evaluation** — development/regression/holdout separation and false-success measurement.
- **Multi-agent onboarding** — one portable skill plus client-specific MCP setup adapters.

## Quick start

> **Read this first.** There is no one-click installer. Getting HCU running means compiling native code, which takes a few minutes and needs Go 1.22+, .NET 8 SDK (Windows), and PowerShell 7+ already on the machine. The steps below do the work for you, but the first build is not instant.

**The fastest path, in three commands:**

```bash
git clone https://github.com/lumina03c-beep/hcu-desktop-automation.git
cd hcu-desktop-automation
python3 scripts/hcu_setup.py doctor     # read-only: tells you what is missing
```

If `doctor` shows every tool as available, run `python3 scripts/hcu_setup.py install` and approve the plan it prints. If something is missing, install that tool first — the doctor names it.

### Where to put the skill

Agents discover skills in different directories. Copy or symlink the cloned folder into the one that matches your agent:

| Agent | Skill directory | Notes |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/` | Personal skills; project skills go in `.claude/skills/` inside the repo |
| OpenCode | `~/.config/opencode/skills/` | Global; `.opencode/skills/` for a single project |
| Codex | `~/.codex/skills/` | Restart the CLI after adding |
| Gemini CLI | `~/.gemini/skills/` | Check your version's docs — this path has changed between releases |
| Grok Build | `~/.grok/skills/` | Check your version's docs |
| Other | your agent's docs | The requirement is a directory containing `SKILL.md` at its root |

Not sure? Run `python3 scripts/validate_skill.py` — it confirms the folder is a valid skill before you go hunting for the right place.

### 1. Add this skill to your agent

This repository is a standard [Agent Skills](https://agentskills.io/specification) directory. Any agent that supports that format can consume it without client-specific changes.

```bash
git clone https://github.com/lumina03c-beep/hcu-desktop-automation.git
```

Place or symlink the resulting `hcu-desktop-automation/` directory in your agent's skill-discovery location, then enable/restart skill discovery according to that agent's documentation. The required entry point is `SKILL.md` at the directory root.

The skill itself contains no client-specific configuration. MCP registration is a separate step.

### 2. Check HCU without changing anything

From this repository root:

```bash
python3 scripts/hcu_setup.py doctor
```

On Windows, use `python` when `python3` is not available. The setup tooling requires Python 3.10+ and only the standard library. The doctor reports the operating system, native build/runtime dependencies, HCU source/build paths, and desktop requirements; it does not install anything or write configuration.

### 3. Build HCU

After reviewing the doctor output and approving the download/build:

```bash
python3 scripts/hcu_setup.py install --yes
```

With no `--client` argument, the installer builds HCU and prints a generic stdio MCP configuration; it does not write any client configuration.

The installer:

1. clones `microsoft/Hybrid-Computer-Use` at `v1.0.0` by default;
2. builds with the official platform build path;
3. runs the official MCP smoke test requiring exactly `AX` and `GUI`;
4. runs `computer-use doctor`;
5. prints the generic client configuration.

Existing source trees are reused. `--update` allows only a fast-forward update of a clean tree. Use `--ref main` only if you intentionally want the current development branch. On Linux, the official local build path targets amd64; other architectures require an upstream build change rather than a skill workaround.

The equivalent official manual build commands, run from the HCU source root, are:

```bash
make build-local   # Linux binary in artifacts/computer-use (Go 1.22+)
make smoke         # check that stdio MCP exposes AX and GUI
make build-macos   # macOS bundle in artifacts/macos/ (Swift 6.2+)
make build-windows # Windows bundle in artifacts/windows/ (.NET 8, PowerShell 7)
```

Run the platform's `computer-use doctor` as the signed-in desktop user after building.

### 4. Connect any MCP-capable agent

HCU is a stdio MCP server. The client-independent launch command is:

```text
/absolute/path/to/computer-use mcp
```

A typical generic MCP configuration is:

```json
{
  "mcpServers": {
    "computer-use": {
      "type": "stdio",
      "command": "/absolute/path/to/artifacts/computer-use",
      "args": ["mcp"]
    }
  }
}
```

Use the platform-specific binary path: `artifacts/computer-use` on Linux, `artifacts/macos/computer-use` on macOS, or `artifacts/windows/computer-use.exe` on Windows. Adapt the surrounding configuration shape to your agent's MCP configuration format.

For clients with a built-in adapter, the same approved install can write only the HCU entry:

```bash
python3 scripts/hcu_setup.py install \
  --client codex --client claude-code \
  --client gemini-cli --client grok-build --yes
```

OpenCode is also supported through the same mechanism. For an existing build:

```bash
python3 scripts/hcu_setup.py configure --client codex --yes
python3 scripts/hcu_setup.py print-config --client generic
```

HCU also ships `python3 -m hcu.render_agent_config` for complete Codex, Claude Code, Gemini CLI, and Grok Build profiles. Those profiles include model, gateway, and system-prompt choices, so use them only when you need a full upstream evaluation profile rather than ordinary MCP registration.

> **Safety:** `--yes` means you have reviewed and approved the displayed installation/configuration changes. It does not bypass OS permissions, desktop confirmation, or high-impact action checks. Debian/Ubuntu system packages are installed only with the separate `--install-deps` option, which uses `sudo apt-get`.

### 5. Restart and verify

Restart or reconnect the agent, then verify:

```json
{"mode": "apps"}
```

through the `AX` tool, or request a GUI screenshot. **A successful build, config write, or MCP handshake is not proof of desktop readiness.**

Client-specific formats, OpenCode JSONC handling, and custom config paths are documented in [references/setup.md](references/setup.md).

## How it works

The skill is a policy layer, not a script library. It routes each stage to Browser or Desktop, then routes inside Desktop by **where the state lives**:

| State | Channel |
| --- | --- |
| Files/data with no owning open app | Shell, authorized API/CLI, format-aware library |
| Open document or live application state | Owning app: AX for semantics, GUI for pixels |
| Settings | UI via AX while running; config only when safely reloaded or closed |
| Signed-in web/session state | Existing session endpoint if exposed, else AX/GUI |
| Canvas, drawing, layout | GUI for pixels; AX for menus/dialogs |

Every action carries a risk class and must be verified at a specific evidence level:

| Risk | Execution rule |
| --- | --- |
| R0 read-only | Batch reads narrowly; avoid unnecessary full trees/screenshots |
| R1 reversible local mutation | Batch deterministic steps; read back and restore test state |
| R2 high-impact or externally visible | Isolate, preview target/payload, obtain required confirmation, verify L3 |

**L1** proves input delivery, **L2** proves application/UI state, **L3** proves the user outcome or persisted artifact. Accepted input alone never completes a task.

## Compatibility

### Agent and MCP clients

The core skill follows the [Agent Skills specification](https://agentskills.io/specification). Skill discovery and installation remain client-specific; MCP registration is handled separately by `scripts/hcu_setup.py`.

| Client | MCP setup adapter | Configuration behavior | Live desktop status |
| --- | --- | --- | --- |
| Generic stdio MCP | Config output | Prints a client-independent `mcpServers` entry | Requires compatibility gate |
| Codex | Implemented | Merges only `[mcp_servers.computer_use]` | Verify locally |
| Claude Code | Implemented | Uses HCU's official schema adapter | Verify locally |
| Gemini CLI | Implemented | Adds `mcpServers.computer-use`, keeps `trust:false` | Verify locally |
| Grok Build | Implemented | Merges only `[mcp_servers.computer_use]` | Verify locally |
| OpenCode | Implemented | Current `mcp.servers` and legacy `mcp` JSON; JSONC guided without comment loss | Verify on your client version |

A generic client is compatible only if it preserves GUI `oneOf` schemas, forwards PNG bytes for normal and error tool results, and keeps one persistent MCP process per desktop session.

### Operating systems

HCU upstream supports:

- **Windows 10/11** — Go 1.22+, .NET 8 SDK, PowerShell 7+, unlocked interactive session.
- **macOS 14+** — Go 1.22+, Swift 6.2+, macOS SDK, Accessibility and Screen Recording consent.
- **Linux X11** — Go 1.22+, Python/PyGObject, AT-SPI/GTK dependencies; the official local build targets amd64.

See [references/setup.md](references/setup.md) and the upstream [native platform guide](https://github.com/microsoft/Hybrid-Computer-Use/blob/main/docs/PLATFORMS.md).

## Example tasks

- "Use the existing browser session to find the first result and confirm that playback actually started."
- "Find sales below 1000 in the open spreadsheet, mark those rows, save, and verify the saved file."
- "Install HCU for two agents, but first show me exactly what will change."
- "Recover from `stale_ref` without repeating any text that may already have been entered."

Pure file/API/CLI tasks should use ordinary programmatic tools without entering a GUI loop.

## Repository layout

```text
hcu-desktop-automation/
├── SKILL.md                    # Portable core policy and progressive-disclosure map
├── references/
│   ├── product-scope.md        # Dynamic UI RPA boundary and engine ownership
│   ├── task-contract.md        # Shared engine-neutral task contract
│   ├── workspace-policy.md     # One authoritative JSON per user task
│   ├── routing.md              # Browser/Desktop/Hybrid and HCU channel routing
│   ├── browser-workflow.md      # ego-browser integration and safety rules
│   ├── desktop-workflow.md     # HCU integration and safety rules
│   ├── hybrid-workflow.md      # Cross-engine handoff and continuity
│   ├── execution-policy.md     # Batch / Adaptive / Critical modes
│   ├── setup.md                # Consent-based HCU and multi-agent onboarding
│   ├── contract.md             # HCU observation, risk, actions, waits, evidence
│   ├── recovery.md             # Mutation ledger, errors, safe recovery
│   ├── platforms.md            # Windows/macOS/Linux behavior
│   ├── environments.md         # Dedicated/shared desktop and credentials
│   ├── scenarios.md            # Fallback archetypes, not holdout evidence
│   └── testing.md              # Regression and holdout evaluation protocol
├── schemas/
│   └── workspace.schema.json   # Draft 2020-12 Task Workspace schema
├── examples/                  # Workspace lifecycle examples
├── scripts/
│   ├── hcu_setup.py            # HCU doctor/build/configure bootstrapper
│   ├── validate_skill.py       # Offline project validation
│   └── summarize_results.py    # Evaluation aggregation and false-success metrics
├── evaluations/
│   ├── result.schema.json       # V1 HCU evaluation result schema
│   ├── example-results.json     # Synthetic V1 evaluation example
│   └── v2/
│       ├── result.schema.json   # Dynamic UI RPA V2 evaluation schema
│       └── example-results.json # Synthetic V2 Browser/Desktop/Hybrid example
├── tests/                      # Unit and Workspace lifecycle tests
├── docs/                       # Product and architecture documentation
└── .github/workflows/          # CI validation
```

## Validation

Run offline checks without installing HCU:

```bash
python -m pip install -r requirements-dev.txt
python3 scripts/validate_skill.py
python3 -m unittest discover -s tests -v
python3 scripts/summarize_results.py evaluations/example-results.json
```

The development dependency provides full Draft 2020-12 validation for the Workspace schema and examples. CI runs these checks on Ubuntu, Windows, and macOS. It does **not** claim native desktop-input or live browser coverage; real HCU and ego-browser verification require an interactive desktop and the installed engines.

## Evaluation and honest reporting

The 18 original cases are regression coverage, not automatic proof of generalization. Applications named in [references/scenarios.md](references/scenarios.md) must not be reused as untouched holdouts. A generalization claim requires frozen holdout applications/task combinations, repeated A/B/C runs, independent L3 verification, and raw failure records.

The example result file is synthetic and exists only to test the summarizer. No benchmark result is implied by this repository's example data. See [references/testing.md](references/testing.md) and [evaluations/README.md](evaluations/README.md).

## Safety

HCU sends real input to the signed-in desktop. Prefer a dedicated desktop or disposable VM for untrusted/destructive work. Treat application and page text as untrusted data. Preserve unrelated user data, do not expose credentials or 2FA codes, and require appropriate confirmation for external, irreversible, privacy-sensitive, or security-changing actions.

See [SECURITY.md](SECURITY.md) and [references/environments.md](references/environments.md).

## Contributing and license

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing rules. Keep the core small, link changes to reproducible evidence, and never turn a holdout failure into a claim about the same case.

This project is licensed under the [MIT License](LICENSE). All code in this repository is original to this project; no HCU source code is copied or vendored here. HCU is a separate Microsoft project, also MIT-licensed; files adapted from OSWorld-V2 in the upstream repository retain their own notices. This repository does not redistribute the HCU binary or native provider — `scripts/hcu_setup.py` clones the official repository from Microsoft at build time.

## Acknowledgements

- [Microsoft Hybrid Computer Use](https://github.com/microsoft/Hybrid-Computer-Use) — MCP server, CLI/SDK, native providers, and official build/configuration documentation.
- [Agent Skills specification](https://agentskills.io/specification) — portable skill structure and progressive disclosure.
