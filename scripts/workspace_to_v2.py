#!/usr/bin/env python3
"""Convert a Dynamic UI RPA Workspace into a V2 evaluation run record.

The adapter is the explicit bridge from the Workspace telemetry to
`evaluations/v2/result.schema.json`; metric definitions come from
`scripts/workspace_metrics.py` and are never reinterpreted here.

Principles:
- `task_success` requires an independent verification verdict passed with
  `--verified` and a `--verifier` identifier. Without them the adapter
  refuses to run instead of copying the Workspace claim.
- Runtime-only observations (snapshots, AX/GUI calls, duplicate mutations)
  cannot be derived from Workspace events. Supply them with `--metrics-file`
  (a flat JSON object using the V2 metric field names, plus an optional
  `recovery` object with eligible/recovered/safe_stopped/failed); missing
  required fields are reported, never invented as zero.
- The final record is validated against the V2 schema before output.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
V2_SCHEMA_PATH = ROOT / "evaluations" / "v2" / "result.schema.json"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import workspace_metrics as metrics  # noqa: E402

DERIVED_METRICS = (
    "model_calls",
    "browser_calls",
    "desktop_calls",
    "auxiliary_calls",
    "input_tokens",
    "output_tokens",
    "handoff_latency_ms",
    "wall_time_ms",
)
RUNTIME_ONLY_METRICS = (
    "browser_snapshots",
    "browser_screenshots",
    "desktop_ax_calls",
    "desktop_gui_calls",
    "duplicate_mutations",
)


def skill_version() -> str:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.strip().startswith("version:"):
            return line.split(":", 1)[1].strip().strip('"')
    raise ValueError("SKILL.md frontmatter has no version field")


def evidence_level(workspace: dict[str, Any], override: str | None) -> str:
    if override:
        return override
    levels = [
        (step.get("verification") or {}).get("evidence_level")
        for step in workspace.get("steps") or []
        if isinstance(step, dict)
        and (step.get("verification") or {}).get("status") == "verified"
    ]
    ordered = [level for level in levels if level in {"L1", "L2", "L3"}]
    return max(ordered, key=lambda level: {"L1": 1, "L2": 2, "L3": 3}[level]) if ordered else "L1"


def error_codes(workspace: dict[str, Any]) -> list[str]:
    codes: list[str] = []
    for event in workspace.get("events") or []:
        if not isinstance(event, dict):
            continue
        code = event.get("failure_code")
        if isinstance(code, str) and code and code not in codes:
            codes.append(code)
    return codes


def build_record(args: argparse.Namespace, workspace: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    if getattr(args, "verified", None) not in {"true", "false"}:
        raise ValueError(
            "independent verification is required: pass --verified true|false with a --verifier identifier; "
            "the Workspace claim is never copied into task_success"
        )
    coverage = task.get("telemetry_coverage") or {}
    supplied: dict[str, Any] = {}
    if isinstance(args.metrics_file, dict):
        supplied = args.metrics_file
    elif args.metrics_file:
        supplied = json.loads(Path(args.metrics_file).read_text(encoding="utf-8-sig"))
        if not isinstance(supplied, dict):
            raise ValueError("--metrics-file must contain a JSON object")

    derived: dict[str, Any] = {
        "model_calls": task.get("model_calls"),
        "input_tokens": task.get("input_tokens"),
        "output_tokens": task.get("output_tokens"),
        "handoff_latency_ms": task.get("median_handoff_latency_ms"),
        "wall_time_ms": task.get("end_to_end_latency_ms"),
    }
    engine_calls = task.get("tool_round_trips_by_engine") or {}
    if coverage.get("tool_calls") == "complete":
        derived["browser_calls"] = engine_calls.get("browser", 0)
        derived["desktop_calls"] = engine_calls.get("desktop", 0)
        derived["auxiliary_calls"] = engine_calls.get("auxiliary", 0)

    missing: list[str] = []
    values: dict[str, Any] = {}
    for name in (*DERIVED_METRICS, *RUNTIME_ONLY_METRICS):
        if name in supplied:
            values[name] = supplied[name]
        elif name in derived:
            values[name] = derived[name]
        else:
            missing.append(name)
    if missing:
        raise ValueError(
            "V2 record requires fields the Workspace cannot derive: "
            + ", ".join(sorted(missing))
            + "; supply them via --metrics-file"
        )
    for name, value in values.items():
        if value is None and name in RUNTIME_ONLY_METRICS:
            raise ValueError(f"{name} must be a non-negative integer")
        if value is None and name in {"wall_time_ms", "browser_calls", "desktop_calls", "auxiliary_calls"}:
            raise ValueError(f"{name} is unknown; supply it via --metrics-file")

    recovery = supplied.get("recovery")
    if not isinstance(recovery, dict):
        if coverage.get("recovery") == "complete":
            recovery = {
                "eligible": task.get("recovery_eligible", 0),
                "recovered": task.get("recovered", 0),
                "safe_stopped": task.get("safe_stopped", 0),
                "failed": task.get("recovery_failed", 0),
            }
        else:
            raise ValueError(
                "recovery telemetry is missing; supply an eligible/recovered/safe_stopped/failed object via --metrics-file"
            )

    record: dict[str, Any] = {
        "schema_version": "2.0.0",
        "run_id": args.run_id or task.get("workspace_id"),
        "case_id": args.case_id,
        "split": args.split,
        "condition": args.condition,
        "synthetic": args.synthetic,
        "started_at": (workspace.get("lifecycle") or {}).get("started_at"),
        "platform": args.platform,
        "client": args.client,
        "model": args.model,
        "skill_version": args.skill_version or skill_version(),
        "engine_profile": (workspace.get("routing") or {}).get("mode"),
        "task_success": args.verified == "true",
        "agent_claimed_success": task.get("agent_claimed_success"),
        "independent_verifier": args.verifier,
        "evidence_level": evidence_level(workspace, args.evidence_level),
        "metrics": {name: values[name] for name in (*DERIVED_METRICS, *RUNTIME_ONLY_METRICS)},
        "recovery": recovery,
        "error_codes": error_codes(workspace),
    }
    if args.notes:
        record["notes"] = args.notes
    if record["started_at"] is None:
        raise ValueError("workspace lifecycle.started_at is required for a V2 record")
    if record["engine_profile"] is None:
        raise ValueError("workspace routing.mode is required for a V2 record")
    return record


def validate_record(record: dict[str, Any]) -> None:
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError as exc:
        raise ValueError(
            "jsonschema is required to validate the V2 record; install requirements-dev.txt"
        ) from exc
    schema = json.loads(V2_SCHEMA_PATH.read_text(encoding="utf-8-sig"))
    errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(record), key=lambda error: list(error.path))
    if errors:
        details = "; ".join(f"{list(error.path)}: {error.message}" for error in errors[:5])
        raise ValueError(f"V2 record failed schema validation: {details}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", help="Workspace JSON file")
    parser.add_argument("--case-id", required=True, help="Evaluation case identifier")
    parser.add_argument("--run-id", help="Run identifier; defaults to the workspace_id")
    parser.add_argument("--verified", required=True, choices=["true", "false"], help="Independent verification verdict")
    parser.add_argument("--verifier", required=True, help="Independent verifier identifier")
    parser.add_argument("--platform", required=True, choices=["windows", "macos", "linux"])
    parser.add_argument("--client", required=True, help="Agent client identifier")
    parser.add_argument("--model", required=True, help="Model identifier")
    parser.add_argument("--split", choices=["development", "validation", "holdout"], default="development")
    parser.add_argument("--condition", choices=["A", "B", "C"], default="C")
    parser.add_argument("--synthetic", action="store_true", help="Mark the record synthetic")
    parser.add_argument("--evidence-level", choices=["L1", "L2", "L3"], help="Override the derived evidence level")
    parser.add_argument("--skill-version", help="Override the version read from SKILL.md")
    parser.add_argument("--metrics-file", help="JSON object with runtime-only metrics")
    parser.add_argument("--notes", help="Free-form note stored with the record")
    parser.add_argument("--output", type=Path, help="Write the record JSON to a file")
    args = parser.parse_args()
    try:
        workspace = metrics.load_workspaces([args.workspace])[0]
        task = metrics.workspace_metrics(workspace)
        record = build_record(args, workspace, task)
        validate_record(record)
        rendered = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
