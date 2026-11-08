# HCU availability, installation, and client setup

Use this reference only when `AX`/`GUI` are unavailable, the user asks to install
HCU, or the client cannot connect. Do not reinstall when the tools already work.

## Agent-assisted onboarding

1. Run the read-only doctor from the skill root:

   ```bash
   python3 scripts/hcu_setup.py doctor
   ```

   On Windows, use `python` when `python3` is unavailable. The bootstrapper
   requires Python 3.10+ and only the standard library.

2. Explain the detected OS, missing dependencies, source destination, selected
   clients, network download, native build, and config files that will change.
   Obtain user approval before any mutation. Do not silently use sudo, change OS
   permissions, remove another MCP server, or start a second desktop driver.

3. After approval, install and configure, for example:

   ```bash
   python3 scripts/hcu_setup.py install --client opencode --yes
   ```

   `--yes` records that the preceding user approval covers the printed changes;
   it is not permission to skip dependency, permission, or verification errors.

4. Restart or reconnect the agent. Confirm the client exposes `AX` and `GUI`,
   then call `AX {"mode":"apps"}` or take a GUI screenshot. A successful clone,
   build, smoke test, config write, or MCP handshake alone is not desktop proof.

5. If setup fails, report the exact failed stage and manual next step. Never
   substitute another computer-use package or claim that HCU is ready.

## What the installer does

`scripts/hcu_setup.py` uses only the Python standard library. It:

- detects Windows, macOS, and Linux plus build/runtime prerequisites;
- clones `https://github.com/microsoft/Hybrid-Computer-Use.git` at the stable
  `v1.0.0` tag by default (`--ref main` opts into the current branch);
- builds through the official platform build path and runs the official MCP
  smoke test requiring exactly `AX` and `GUI`;
- runs `computer-use doctor` and distinguishes native desktop warnings from
  protocol/build success;
- merges only the selected HCU config entry, preserves unrelated settings, and
  creates a timestamped backup beside every existing config it modifies;
- prints a restart/reconnect and live-verification requirement.

An existing source tree is reused, not recloned. `--update` permits only a
fast-forward pull of a clean tree. The script does not install prebuilt binaries:
the upstream `v1.0.0` release contains source archives, not platform executables.

## Build prerequisites

| Platform | Build requirements | Native runtime |
| --- | --- | --- |
| Windows 10/11 | Git, Python 3.10+, Go 1.22+, .NET 8 SDK, PowerShell 7+ (`pwsh`) | Unlocked interactive session and matching integrity level |
| macOS 14+ | Git, Python 3.10+, Go 1.22+, Swift 6.2+, macOS SDK, make | Graphical login; Accessibility and Screen Recording consent |
| Linux | Git, Python 3.10+, Go 1.22+, make; official Linux build targets amd64 | Signed-in X11 session, PyGObject/AT-SPI/GTK typelibs, xdotool, wmctrl, x11-utils |

On Debian/Ubuntu, `--install-deps` explicitly runs the documented `apt-get`
runtime installation through `sudo`. It does not install the Go toolchain or
other build tools. Review the command before approving it. On other systems,
install missing dependencies using the official platform documentation.

Official manual build commands from the HCU source root:

```bash
make build-local       # Linux: artifacts/computer-use
make build-macos       # macOS: artifacts/macos/computer-use
make build-windows     # Windows: artifacts/windows/computer-use.exe (requires pwsh)
make smoke             # Linux protocol smoke test
```

Platform-specific verification:

```bash
artifacts/computer-use doctor
python3 scripts/smoke-mcp.py artifacts/computer-use

artifacts/macos/computer-use doctor
python3 scripts/smoke-mcp.py artifacts/macos/computer-use

./artifacts/windows/computer-use.exe doctor
python scripts/smoke-mcp.py artifacts/windows/computer-use.exe
```

Keep `ComputerUseProvider.app` beside the macOS executable and
`computer-use-windows-provider.exe` beside the Windows executable.

## Client adapters

Repeat `--client` to configure multiple agents in one approved run:

```bash
python3 scripts/hcu_setup.py install \
  --client opencode --client codex --client claude-code \
  --client gemini-cli --client grok-build --yes
```

| Client | Automatic config target | Adapter details |
| --- | --- | --- |
| OpenCode | `${XDG_CONFIG_HOME:-~/.config}/opencode/opencode.json` or existing `opencode.jsonc` | Detects legacy `mcp.<name>` and current `mcp.servers.<name>`; current config sets `codemode:false` for direct AX/GUI tools |
| Codex | `${CODEX_HOME:-~/.codex}/config.toml` | Replaces only `[mcp_servers.computer_use]`; 60 s startup and 180 s tool timeout |
| Claude Code | `~/.claude.json` | Uses the official `claude_mcp_schema_adapter.py`; do not connect the raw binary directly |
| Gemini CLI | `${GEMINI_CLI_HOME:-~}/.gemini/settings.json` | Adds `mcpServers.computer-use`; leaves `trust:false` so confirmations are not bypassed |
| Grok Build | `${GROK_HOME:-~/.grok}/config.toml` | Replaces only `[mcp_servers.computer_use]` |
| Generic MCP | Printed only | stdio command `<absolute-path-to-computer-use> mcp` |

Use `--config CLIENT=/absolute/path` to override a selected client's default.
`configure` updates clients for an existing build without rebuilding;
`print-config` never writes files. Examples:

```bash
python3 scripts/hcu_setup.py configure --client codex --yes
python3 scripts/hcu_setup.py print-config --client generic
python3 scripts/hcu_setup.py print-config --client opencode
```

### OpenCode JSONC and version compatibility

The automatic writer supports JSON configuration and detects the existing
OpenCode schema. It deliberately refuses to rewrite JSONC because serializing it
would discard comments. For JSONC, run the official client command and then
merge the printed entry manually, preserving comments:

```bash
opencode mcp add computer-use --global -- /absolute/path/to/computer-use mcp
python3 scripts/hcu_setup.py print-config --client opencode
```

For current OpenCode, ensure the entry under `mcp.servers` has `codemode:false`.
For legacy OpenCode, the entry belongs directly under `mcp` and uses
`enabled:true`. Do not mix the two schemas.

### Other agents and full upstream profiles

The core skill follows the Agent Skills directory/frontmatter specification and
contains no OpenCode-specific execution instructions. Install the same directory
using each agent's skill discovery mechanism. MCP registration is independent
of skill installation.

HCU also ships `python3 -m hcu.render_agent_config` for complete Codex, Claude
Code, Gemini CLI, and Grok Build evaluation profiles. Those profiles involve
model/gateway/system-prompt choices and can generate multiple files; do not use
them as a silent default for ordinary user onboarding. See the official MCP
guide when a full isolated evaluation profile is required.

## Generic MCP compatibility gate

Registration alone does not prove that another agent is compatible. Verify that
the client:

1. preserves the GUI schema's `oneOf` rather than flattening it incorrectly;
2. forwards PNG bytes from normal and `isError:true` tool results to the model;
3. keeps one persistent MCP process per desktop session rather than spawning a
   new process for each call;
4. leaves MCP stdout exclusively for protocol messages and sends diagnostics to
   stderr.

If any requirement is unknown, mark the client unverified and test with a
read-only AX/GUI observation before attempting mutations.

## Official sources

Verified against upstream documentation on 2026-11-08:

- Repository and build: https://github.com/microsoft/Hybrid-Computer-Use
- MCP contract/config: https://github.com/microsoft/Hybrid-Computer-Use/blob/main/docs/MCP.md
- Native platforms: https://github.com/microsoft/Hybrid-Computer-Use/blob/main/docs/PLATFORMS.md
- OpenCode MCP: https://opencode.ai/docs/mcp-servers/
- Agent Skills specification: https://agentskills.io/specification
