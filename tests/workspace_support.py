"""Shared helpers for Dynamic UI RPA Workspace tests.

This module is test support only. It emulates the Agent's safe update procedure
so the tests can prove revision, persistence, and conflict semantics without
adding a production Workspace runtime.
"""

from __future__ import annotations

import copy
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "workspace.schema.json"
EXAMPLES_DIR = ROOT / "examples"


class WorkspaceError(Exception):
    """Base error for Workspace test support."""


class WorkspaceValidationError(WorkspaceError):
    """Raised when a Workspace document fails schema validation."""


class WorkspaceConflict(WorkspaceError):
    """Raised when the on-disk revision does not match the expected revision."""


class WorkspacePersistenceError(WorkspaceError):
    """Raised when a Workspace write cannot be confirmed."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_schema() -> Dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validator() -> Draft202012Validator:
    return Draft202012Validator(load_schema(), format_checker=FormatChecker())


def validate(data: Dict[str, Any]) -> None:
    errors = sorted(validator().iter_errors(data), key=lambda error: list(error.path))
    if errors:
        details = "\n".join(f"{list(error.path)}: {error.message}" for error in errors)
        raise WorkspaceValidationError(f"Workspace schema violation:\n{details}")


def load_example(name: str) -> Dict[str, Any]:
    path = EXAMPLES_DIR / f"workspace.{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_workspace(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkspacePersistenceError(f"Workspace unreadable: {exc}") from exc
    validate(data)
    return data


def write_workspace(path: Path, data: Dict[str, Any]) -> Dict[str, Any]:
    validate(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)
    persisted = load_workspace(path)
    if persisted.get("revision") != data.get("revision"):
        raise WorkspacePersistenceError("Workspace revision changed during write")
    return persisted


def update_workspace(
    path: Path,
    mutate: Callable[[Dict[str, Any]], None],
    expected_revision: Optional[int] = None,
) -> Dict[str, Any]:
    """Apply one safe Workspace update and return the persisted document."""

    current = load_workspace(path)
    revision = current.get("revision")
    if expected_revision is not None and revision != expected_revision:
        raise WorkspaceConflict(
            f"Workspace revision conflict: expected {expected_revision}, found {revision}"
        )

    candidate = copy.deepcopy(current)
    mutate(candidate)
    candidate["revision"] = int(revision) + 1
    candidate["timestamps"]["updated_at"] = utc_now()
    return write_workspace(path, candidate)


def next_pending_step(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for step in data.get("steps", []):
        if step.get("status") not in {"completed", "skipped"}:
            return step
    return None


def iter_keys(data: Any, prefix: str = "") -> Iterable[str]:
    if isinstance(data, dict):
        for key, value in data.items():
            location = f"{prefix}.{key}" if prefix else str(key)
            yield location
            yield from iter_keys(value, location)
    elif isinstance(data, list):
        for index, value in enumerate(data):
            location = f"{prefix}[{index}]"
            yield from iter_keys(value, location)


def mutation_requires_reobservation(mutation: Dict[str, Any]) -> bool:
    effect_state = mutation.get("effect_state")
    verification_status = mutation.get("verification", {}).get("status")
    if effect_state in {"unknown", "dispatched"} and verification_status != "verified":
        return True
    if effect_state == "prepared" and verification_status != "verified":
        return True
    return False
