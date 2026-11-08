#!/usr/bin/env python3
"""Install, diagnose, and configure Microsoft Hybrid Computer Use (HCU).

The default command is read-only. Installation and configuration require --yes
in non-interactive use. Python 3.10+ and only the standard library are required.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

UPSTREAM = "https://github.com/microsoft/Hybrid-Computer-Use.git"
DEFAULT_REF = "v1.0.0"
CLIENTS = ("opencode", "codex", "claude-code", "gemini-cli", "grok-build", "generic")


class SetupError(RuntimeError):
    pass


def system_name() -> str:
    value = platform.system().lower()
    if value not in {"windows", "darwin", "linux"}:
        raise SetupError(f"Unsupported operating system: {platform.system()}")
    return value


def default_source() -> Path:
    if os.environ.get("HCU_SOURCE"):
        return Path(os.environ["HCU_SOURCE"]).expanduser()
    home = Path.home()
    system = system_name()
    if system == "windows":
        base = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        return base / "HCU" / "Hybrid-Computer-Use"
    if system == "darwin":
        return home / "Library" / "Application Support" / "HCU" / "Hybrid-Computer-Use"
    base = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
    return base / "hcu" / "Hybrid-Computer-Use"


def binary_path(source: Path, system: str | None = None) -> Path:
    system = system or system_name()
    if system == "windows":
        return source / "artifacts" / "windows" / "computer-use.exe"
    if system == "darwin":
        return source / "artifacts" / "macos" / "computer-use"
    return source / "artifacts" / "computer-use"


def run_capture(command: list[str], cwd: Path | None = None, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )


def run_checked(command: list[str], cwd: Path | None = None, timeout: int = 1200) -> None:
    print("+", " ".join(str(part) for part in command), flush=True)
    result = subprocess.run(command, cwd=str(cwd) if cwd else None, timeout=timeout, check=False)
    if result.returncode:
        raise SetupError(f"Command failed with exit code {result.returncode}: {command[0]}")


def version_at_least(output: str, pattern: str, minimum: tuple[int, int]) -> bool | None:
    match = re.search(pattern, output)
    if not match:
        return None
    try:
        return (int(match.group(1)), int(match.group(2))) >= minimum
    except (ValueError, IndexError):
        return None


def tool_report(system: str) -> dict[str, dict[str, Any]]:
    names = ["git", "go", "python3"] if system != "windows" else ["git", "go", "pwsh", "dotnet"]
    if system == "darwin":
        names += ["make", "swift", "xcrun"]
    if system == "linux":
        names += ["make", "xdotool", "wmctrl", "xwininfo", "gdbus"]
    report: dict[str, dict[str, Any]] = {}
    for name in names:
        executable = shutil.which(name)
        item: dict[str, Any] = {"available": bool(executable), "path": executable}
        if executable and name == "go":
            result = run_capture([executable, "version"])
            item["version_ok"] = version_at_least(result.stdout, r"go(\d+)\.(\d+)", (1, 22))
            item["version_output"] = result.stdout.strip()
        elif executable and name == "dotnet":
            result = run_capture([executable, "--version"])
            item["version_ok"] = version_at_least(result.stdout.strip(), r"^(\d+)\.(\d+)", (8, 0))
            item["version_output"] = result.stdout.strip()
        elif executable and name == "swift":
            result = run_capture([executable, "--version"])
            item["version_ok"] = version_at_least(result.stdout, r"Swift version (\d+)\.(\d+)", (6, 2))
            item["version_output"] = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
        report[name] = item
    if system != "windows":
        report["python3"] = {
            "available": True,
            "path": sys.executable,
            "version_ok": sys.version_info >= (3, 10),
            "version_output": platform.python_version(),
        }
    return report


def linux_gi_available() -> bool:
    result = run_capture([
        sys.executable,
        "-c",
        'import gi; gi.require_version("Atspi", "2.0"); from gi.repository import Atspi',
    ])
    return result.returncode == 0


def dependency_problems(system: str, report: dict[str, dict[str, Any]]) -> list[str]:
    problems: list[str] = []
    if system == "linux" and platform.machine().lower() not in {"amd64", "x86_64"}:
        problems.append(f"official local Linux build targets amd64, found {platform.machine()}")
    for name, item in report.items():
        if not item["available"]:
            problems.append(f"missing command: {name}")
        elif item.get("version_ok") is False:
            problems.append(f"unsupported {name} version: {item.get('version_output', 'unknown')}")
    if system == "linux" and not linux_gi_available():
        problems.append("Python PyGObject/AT-SPI is unavailable")
    return problems


def desktop_report(system: str) -> dict[str, Any]:
    if system == "linux":
        names = ("DISPLAY", "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS")
        return {
            "kind": "signed-in X11 session required",
            "environment": {name: bool(os.environ.get(name)) for name in names},
        }
    if system == "darwin":
        return {"kind": "macOS 14+ graphical login; Accessibility and Screen Recording consent"}
    return {"kind": "Windows 10/11 unlocked interactive session; matching integrity level"}


def config_path(client: str) -> Path:
    home = Path.home()
    if client == "opencode":
        base = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config")) / "opencode"
        json_path = base / "opencode.json"
        jsonc_path = base / "opencode.jsonc"
        if jsonc_path.exists() and not json_path.exists():
            return jsonc_path
        return json_path
    if client == "codex":
        return Path(os.environ.get("CODEX_HOME", home / ".codex")) / "config.toml"
    if client == "claude-code":
        return home / ".claude.json"
    if client == "gemini-cli":
        return Path(os.environ.get("GEMINI_CLI_HOME", home)) / ".gemini" / "settings.json"
    if client == "grok-build":
        return Path(os.environ.get("GROK_HOME", home / ".grok")) / "config.toml"
    raise SetupError(f"No default config path for {client}")


def backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    target = path.with_name(f"{path.name}.hcu-backup-{stamp}")
    counter = 1
    while target.exists():
        target = path.with_name(f"{path.name}.hcu-backup-{stamp}-{counter}")
        counter += 1
    shutil.copy2(path, target)
    return target


def atomic_write(path: Path, content: str) -> Path | None:
    path.parent.mkdir(parents=True, exist_ok=True)
    saved = backup(path)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    try:
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return saved


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return {}
    if path.suffix.lower() == ".jsonc":
        raise SetupError(
            f"JSONC needs a guided update: {path}. Use the client's MCP add command or "
            "copy the generated entry from print-config; the script will not discard comments."
        )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SetupError(f"Cannot parse {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SetupError(f"Expected a JSON object in {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> Path | None:
    return atomic_write(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def opencode_entry(binary: Path, version: str) -> dict[str, Any]:
    if version == "v1":
        return {"type": "local", "command": [str(binary), "mcp"], "enabled": True, "timeout": 60000}
    return {
        "type": "local",
        "command": [str(binary), "mcp"],
        "disabled": False,
        "codemode": False,
        "timeout": {"startup": 60000, "catalog": 30000, "execution": 180000},
    }


def configure_opencode(binary: Path, path: Path) -> Path | None:
    config = load_json(path)
    mcp = config.setdefault("mcp", {})
    if not isinstance(mcp, dict):
        raise SetupError(f"OpenCode mcp must be an object in {path}")
    v2_global_keys = {"timeout"}
    if isinstance(mcp.get("servers"), dict) or not mcp or all(key in v2_global_keys for key in mcp):
        version = "v2"
    else:
        version = "v1"
    if version == "v2":
        servers = mcp.setdefault("servers", {})
        servers["computer-use"] = opencode_entry(binary, "v2")
    else:
        mcp["computer-use"] = opencode_entry(binary, "v1")
    print(f"OpenCode configuration schema: {version}")
    return write_json(path, config)


def configure_gemini(binary: Path, path: Path) -> Path | None:
    config = load_json(path)
    servers = config.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        raise SetupError(f"Gemini mcpServers must be an object in {path}")
    servers["computer-use"] = {
        "command": str(binary),
        "args": ["mcp"],
        "timeout": 180000,
        "trust": False,
    }
    return write_json(path, config)


def configure_claude(binary: Path, source: Path, path: Path) -> Path | None:
    adapter = source / "osworld" / "guest_files" / "claude_mcp_schema_adapter.py"
    if not adapter.is_file():
        raise SetupError(f"Official Claude schema adapter is missing: {adapter}")
    config = load_json(path)
    servers = config.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        raise SetupError(f"Claude mcpServers must be an object in {path}")
    servers["computer_use"] = {
        "type": "stdio",
        "command": str(Path(sys.executable).resolve()),
        "args": [str(adapter.resolve()), str(binary.resolve()), "mcp"],
    }
    return write_json(path, config)


def toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def replace_toml_table(content: str, table: str, block: str) -> str:
    header = f"[{table}]"
    pattern = re.compile(rf"(?m)^\[{re.escape(table)}\]\s*(?:#.*)?$")
    match = pattern.search(content)
    if not match:
        separator = "" if not content or content.endswith("\n\n") else ("\n" if content.endswith("\n") else "\n\n")
        return content + separator + block
    next_header = re.compile(r"(?m)^\[.+\]\s*(?:#.*)?$")
    following = next_header.search(content, match.end())
    end = following.start() if following else len(content)
    return content[:match.start()] + block + ("\n" if end < len(content) else "") + content[end:]


def configure_toml(client: str, binary: Path, path: Path) -> Path | None:
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    table = "mcp_servers.computer_use"
    if client == "codex":
        block = (
            f"[{table}]\n"
            f"command = {toml_string(str(binary.resolve()))}\n"
            'args = ["mcp"]\n'
            "required = true\n"
            "startup_timeout_sec = 60\n"
            "tool_timeout_sec = 180\n"
        )
    elif client == "grok-build":
        block = (
            f"[{table}]\n"
            f"command = {toml_string(str(binary.resolve()))}\n"
            'args = ["mcp"]\n'
            "enabled = true\n"
            "startup_timeout_sec = 60\n"
            "tool_timeout_sec = 180\n"
        )
    else:
        raise SetupError(f"Unsupported TOML client: {client}")
    return atomic_write(path, replace_toml_table(content, table, block))


def generic_config(client: str, binary: Path, source: Path) -> dict[str, Any]:
    if client == "opencode":
        return {"mcp": {"servers": {"computer-use": opencode_entry(binary, "v2")}}}
    if client == "claude-code":
        adapter = source / "osworld" / "guest_files" / "claude_mcp_schema_adapter.py"
        return {"mcpServers": {"computer_use": {
            "type": "stdio", "command": str(Path(sys.executable).resolve()),
            "args": [str(adapter.resolve()), str(binary.resolve()), "mcp"],
        }}}
    if client == "gemini-cli":
        return {"mcpServers": {"computer-use": {
            "command": str(binary.resolve()), "args": ["mcp"], "timeout": 180000, "trust": False,
        }}}
    if client in {"codex", "grok-build"}:
        table = "mcp_servers.computer_use"
        return {"toml": (
            f"[{table}]\ncommand = {toml_string(str(binary.resolve()))}\n"
            'args = ["mcp"]\nstartup_timeout_sec = 60\ntool_timeout_sec = 180\n'
        )}
    return {"mcpServers": {"computer-use": {
        "type": "stdio", "command": str(binary.resolve()), "args": ["mcp"],
    }}}


def configure_client(client: str, source: Path, binary: Path, override: Path | None = None) -> None:
    if client == "generic":
        print(json.dumps(generic_config(client, binary, source), indent=2, ensure_ascii=False))
        return
    path = override or config_path(client)
    if client == "opencode":
        saved = configure_opencode(binary, path)
    elif client == "gemini-cli":
        saved = configure_gemini(binary, path)
    elif client == "claude-code":
        saved = configure_claude(binary, source, path)
    else:
        saved = configure_toml(client, binary, path)
    print(f"Configured {client}: {path}")
    if saved:
        print(f"Backup: {saved}")


def parse_overrides(values: list[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise SetupError("--config must be CLIENT=PATH")
        client, raw_path = value.split("=", 1)
        if client not in CLIENTS or client == "generic":
            raise SetupError(f"Invalid client in --config: {client}")
        result[client] = Path(raw_path).expanduser().resolve()
    return result


def validate_source(source: Path) -> None:
    required = ("Makefile", "computer-use", "scripts/smoke-mcp.py")
    missing = [name for name in required if not (source / name).exists()]
    if missing:
        raise SetupError(f"Not an HCU source tree: {source}; missing {', '.join(missing)}")


def install_system_deps() -> None:
    if system_name() != "linux":
        raise SetupError("--install-deps currently supports Debian/Ubuntu Linux only")
    if not shutil.which("apt-get"):
        raise SetupError("apt-get is unavailable; install the documented native dependencies manually")
    packages = [
        "python3", "python3-gi", "gir1.2-atspi-2.0", "gir1.2-gtk-3.0",
        "gir1.2-gdkpixbuf-2.0", "gir1.2-ibus-1.0", "ibus", "ibus-gtk",
        "ibus-gtk3", "xdotool", "wmctrl", "x11-utils",
    ]
    run_checked(["sudo", "apt-get", "update"])
    run_checked(["sudo", "apt-get", "install", "-y", *packages])


def build_hcu(source: Path, system: str) -> Path:
    validate_source(source)
    if system == "windows":
        pwsh = shutil.which("pwsh")
        if not pwsh:
            raise SetupError("PowerShell 7+ (pwsh) is required")
        run_checked([
            pwsh, "-NoProfile", "-File", str(source / "computer-use/native/windows/build.ps1"),
            "-OutputDirectory", str(source / "artifacts/windows"),
        ], cwd=source)
    else:
        target = "build-macos" if system == "darwin" else "build-local"
        run_checked(["make", target], cwd=source)
    binary = binary_path(source, system)
    if not binary.is_file():
        raise SetupError(f"Build finished without the expected binary: {binary}")
    run_checked([sys.executable, str(source / "scripts/smoke-mcp.py"), str(binary)], cwd=source, timeout=180)
    return binary


def confirm(args: argparse.Namespace, source: Path, clients: list[str]) -> None:
    if args.yes:
        return
    if not sys.stdin.isatty():
        raise SetupError("Refusing changes without confirmation; rerun with --yes after user approval")
    print(f"Upstream: {UPSTREAM}\nSource: {source}\nClients: {', '.join(clients)}")
    print("This may download source, build native code, and update the selected MCP config entries.")
    answer = input("Continue? [y/N] ").strip().lower()
    if answer not in {"y", "yes"}:
        raise SetupError("Cancelled")


def command_doctor(args: argparse.Namespace) -> int:
    system = system_name()
    source = args.source.expanduser().resolve()
    binary = binary_path(source, system)
    tools = tool_report(system)
    result = {
        "platform": system,
        "architecture": platform.machine(),
        "source": str(source),
        "source_present": source.is_dir(),
        "binary": str(binary),
        "binary_present": binary.is_file(),
        "tools": tools,
        "dependency_problems": dependency_problems(system, tools),
        "desktop": desktop_report(system),
    }
    if binary.is_file():
        doctor = run_capture([str(binary), "doctor"])
        result["hcu_doctor"] = {"returncode": doctor.returncode, "output": doctor.stdout.strip()}
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result["dependency_problems"]:
            print("\nResolve build/runtime dependencies before installation.", file=sys.stderr)
        elif not binary.is_file():
            print("\nHCU is not built. Run install with user approval.", file=sys.stderr)
    return 1 if result["dependency_problems"] else 0


def command_install(args: argparse.Namespace) -> int:
    system = system_name()
    source = args.source.expanduser().resolve()
    clients = args.client or []
    confirm(args, source, clients)
    if args.install_deps:
        install_system_deps()
    problems = dependency_problems(system, tool_report(system))
    if problems:
        raise SetupError("Dependency preflight failed: " + "; ".join(problems))
    if not source.exists():
        source.parent.mkdir(parents=True, exist_ok=True)
        run_checked(["git", "clone", "--depth", "1", "--branch", args.ref, UPSTREAM, str(source)])
    else:
        validate_source(source)
        if args.update:
            status = run_capture(["git", "status", "--porcelain"], cwd=source)
            if status.returncode or status.stdout.strip():
                raise SetupError("Refusing to update a source tree with local changes")
            run_checked(["git", "pull", "--ff-only"], cwd=source)
        print(f"Using existing HCU source: {source}")
    binary = build_hcu(source, system)
    version = run_capture([str(binary), "--version"])
    print(version.stdout.strip())
    doctor = run_capture([str(binary), "doctor"])
    print(doctor.stdout.strip())
    if doctor.returncode:
        print("WARNING: native desktop checks need attention; installation is not readiness.", file=sys.stderr)
    if not args.skip_config:
        overrides = parse_overrides(args.config)
        for client in clients:
            configure_client(client, source, binary, overrides.get(client))
    print("\nNEXT: restart or reconnect the selected agent, then run AX apps or a GUI screenshot.")
    print("Do not treat a successful build or config write as proof of desktop readiness.")
    return 0


def command_configure(args: argparse.Namespace) -> int:
    source = args.source.expanduser().resolve()
    validate_source(source)
    binary = binary_path(source)
    if not binary.is_file():
        raise SetupError(f"Build HCU first; binary not found: {binary}")
    confirm(args, source, args.client)
    overrides = parse_overrides(args.config)
    for client in args.client:
        configure_client(client, source, binary, overrides.get(client))
    return 0


def command_print_config(args: argparse.Namespace) -> int:
    source = args.source.expanduser().resolve()
    binary = binary_path(source)
    for client in args.client:
        print(f"# {client}")
        print(json.dumps(generic_config(client, binary, source), indent=2, ensure_ascii=False))
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--source", type=Path, default=default_source(), help="HCU source directory")
    sub = result.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor", help="Read-only dependency and runtime report")
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(func=command_doctor)
    for name, function in (("install", command_install), ("configure", command_configure)):
        command = sub.add_parser(name, help=f"{name} HCU and selected clients")
        command.add_argument("--client", action="append", choices=CLIENTS, required=(name == "configure"))
        command.add_argument("--config", action="append", default=[], metavar="CLIENT=PATH")
        command.add_argument("--yes", action="store_true", help="Confirm changes after explicit user approval")
        if name == "install":
            command.add_argument("--ref", default=DEFAULT_REF, help="Git ref for a fresh clone")
            command.add_argument("--update", action="store_true", help="Fast-forward an existing clean clone")
            command.add_argument("--install-deps", action="store_true", help="Use sudo apt-get on Debian/Ubuntu")
            command.add_argument("--skip-config", action="store_true")
        command.set_defaults(func=function)
    print_config = sub.add_parser("print-config", help="Print client entries without writing files")
    print_config.add_argument("--client", action="append", choices=CLIENTS, required=True)
    print_config.set_defaults(func=command_print_config)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        return args.func(args)
    except (SetupError, subprocess.TimeoutExpired, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
