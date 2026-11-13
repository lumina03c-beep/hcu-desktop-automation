#!/usr/bin/env python3
"""Compute task-level metrics from Dynamic UI RPA Workspace files.

Metric semantics:
- Missing telemetry stays `null`; real zero is reported only when the event
  stream explicitly shows zero calls. Coverage is reported per metric kind.
- `agent_claimed_success` mirrors the Workspace result status. `task_success`
  requires an independent verifier and is always `null` here; produce it with
  `scripts/workspace_to_v2.py` instead of trusting the Workspace claim.
- Token usage is split into input/output/cached sums; `total_tokens` prefers
  the split fields and falls back to the legacy `tokens` field.
- Recovery episodes are counted from explicit `kind == "recovery"` events:
  `eligible` (unless explicitly false), `recovered`, `safe_stopped`, and
  `failed` stay separate denominators and outcomes.
- Handoff latency is segmented: prepare (prepare_started_at -> target_ready_at),
  target ready (created_at -> target_ready_at), reobserve
  (target_ready_at -> reobserve_completed_at), and total
  (created_at -> completed_at).

Input robustness: UTF-8 BOM is tolerated on read, output stays BOM-free,
Workspaces are validated against `schemas/workspace.schema.json`, and
timestamps must be timezone-aware ISO 8601; negative durations are errors,
never silently clamped to zero.
"""

from __future__ import annotations

import argparse
import glob
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

TERMINAL_STATES = {"completed", "failed", "aborted", "safe_stopped"}
ENGINE_CALLS = ("browser", "desktop", "auxiliary")
ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "workspace.schema.json"
TIMESTAMP_FIELDS = {
    "timestamps": ("created_at", "updated_at"),
    "lifecycle": ("started_at", "completed_at"),
    "event": ("at",),
    "handoff": ("created_at", "completed_at", "prepare_started_at", "target_ready_at", "reobserve_completed_at"),
    "mutation": ("created_at", "updated_at"),
    "artifact": ("created_at",),
}


def section_items(document: dict[str, Any], section: str) -> list[dict[str, Any]]:
    value = document.get(section)
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def validate_timestamps(document: dict[str, Any]) -> None:
    for section, fields in TIMESTAMP_FIELDS.items():
        for item in section_items(document, section):
            for field in fields:
                if item.get(field) is not None:
                    parse_time(item[field])


def parse_time(value: Any) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"timestamp must be a non-empty ISO 8601 string, got {value!r}")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp must carry a timezone offset: {value!r}")
    return parsed


def elapsed_ms(start: datetime, end: datetime) -> int:
    delta = int((end - start).total_seconds() * 1000)
    if delta < 0:
        raise ValueError(f"duration must not be negative: {start.isoformat()} -> {end.isoformat()}")
    return delta


def optional_elapsed_ms(start: Any, end: Any) -> int | None:
    if start is None or end is None:
        return None
    return elapsed_ms(parse_time(start), parse_time(end))


def count(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def p90(values: list[Any]) -> float | int | None:
    present = [value for value in values if isinstance(value, (int, float)) and not isinstance(value, bool)]
    if not present:
        return None
    ordered = sorted(present)
    rank = 0.9 * (len(ordered) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def token_sums(events: list[dict[str, Any]]) -> tuple[int | None, int | None, int | None, int | None, str]:
    sums = {"input_tokens": 0, "output_tokens": 0, "cached_input_tokens": 0, "tokens": 0}
    seen = {key: False for key in sums}
    for event in events:
        for key in sums:
            value = event.get(key)
            if value is not None:
                seen[key] = True
                sums[key] += count(value)
    if seen["input_tokens"] or seen["output_tokens"]:
        total: int | None = sums["input_tokens"] + sums["output_tokens"]
    elif seen["tokens"]:
        total = sums["tokens"]
    else:
        total = None
    model_events = [event for event in events if event.get("kind") == "model_call"]
    model_tokens_present = sum(
        1
        for event in model_events
        if event.get("input_tokens") is not None or event.get("output_tokens") is not None
    )
    if not model_events or not any(seen.values()):
        coverage = "missing"
    elif model_tokens_present == len(model_events):
        coverage = "complete"
    else:
        coverage = "partial"
    return (
        sums["input_tokens"] if seen["input_tokens"] else None,
        sums["output_tokens"] if seen["output_tokens"] else None,
        sums["cached_input_tokens"] if seen["cached_input_tokens"] else None,
        total,
        coverage,
    )


def recovery_episodes(events: list[dict[str, Any]]) -> tuple[str, dict[str, int | None]]:
    episodes = [event for event in events if event.get("kind") == "recovery"]
    if not episodes:
        return "missing", {
            "recovery_eligible": None,
            "recovered": None,
            "safe_stopped": None,
            "recovery_failed": None,
            "recovery_unresolved": None,
            "recovery_rate": None,
        }
    eligible_events = [event for event in episodes if event.get("eligible") is not False]
    eligible = len(eligible_events)
    outcomes = {"recovered": 0, "safe_stopped": 0, "failed": 0, "unresolved": 0}
    for event in eligible_events:
        outcome = event.get("outcome")
        if outcome == "recovered":
            outcomes["recovered"] += 1
        elif outcome == "safe_stopped":
            outcomes["safe_stopped"] += 1
        elif outcome == "failed":
            outcomes["failed"] += 1
        else:
            outcomes["unresolved"] += 1
    resolved = outcomes["recovered"] + outcomes["safe_stopped"] + outcomes["failed"]
    if eligible:
        rate = outcomes["recovered"] / eligible
    else:
        rate = None
    return "complete", {
        "recovery_eligible": eligible,
        "recovered": outcomes["recovered"],
        "safe_stopped": outcomes["safe_stopped"],
        "recovery_failed": outcomes["failed"],
        "recovery_unresolved": outcomes["unresolved"],
        "recovery_rate": rate,
        "recovery_resolved": resolved,
    }


def handoff_segments(handoffs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    segments = []
    for handoff in handoffs:
        if not isinstance(handoff, dict):
            continue
        segments.append(
            {
                "handoff_id": handoff.get("handoff_id"),
                "prepare_ms": optional_elapsed_ms(handoff.get("prepare_started_at"), handoff.get("target_ready_at")),
                "target_ready_ms": optional_elapsed_ms(handoff.get("created_at"), handoff.get("target_ready_at")),
                "reobserve_ms": optional_elapsed_ms(handoff.get("target_ready_at"), handoff.get("reobserve_completed_at")),
                "total_ms": optional_elapsed_ms(handoff.get("created_at"), handoff.get("completed_at")),
            }
        )
    return segments


def workspace_metrics(workspace: dict[str, Any]) -> dict[str, Any]:
    lifecycle = workspace.get("lifecycle") or {}
    timestamps = workspace.get("timestamps") or {}
    result = workspace.get("result") or {}
    events = [event for event in workspace.get("events") or [] if isinstance(event, dict)]

    engine_events = [event for event in events if event.get("engine") in ENGINE_CALLS]
    round_trips = {name: 0 for name in ENGINE_CALLS}
    for event in engine_events:
        round_trips[event["engine"]] += count(event.get("round_trips"))
    tool_calls_present = bool(engine_events)

    model_events = [event for event in events if event.get("kind") == "model_call"]
    model_calls = sum(count(event.get("round_trips")) or 1 for event in model_events)
    model_calls_present = bool(model_events)

    input_tokens, output_tokens, cached_tokens, total_tokens, token_coverage = token_sums(events)
    recovery_coverage, recovery = recovery_episodes(events)

    handoffs = workspace.get("handoffs") or []
    segments = handoff_segments(handoffs if isinstance(handoffs, list) else [])
    totals = [segment["total_ms"] for segment in segments if segment["total_ms"] is not None]
    prepare_values = [segment["prepare_ms"] for segment in segments if segment["prepare_ms"] is not None]
    ready_values = [segment["target_ready_ms"] for segment in segments if segment["target_ready_ms"] is not None]
    reobserve_values = [segment["reobserve_ms"] for segment in segments if segment["reobserve_ms"] is not None]

    status = lifecycle.get("status")
    started = parse_time(lifecycle.get("started_at") or timestamps.get("created_at"))
    finished = parse_time(lifecycle.get("completed_at")) if lifecycle.get("completed_at") else None
    e2e = elapsed_ms(started, finished) if status in TERMINAL_STATES and finished else None

    claimed = result.get("status") == "completed"
    return {
        "workspace_id": workspace.get("workspace_id"),
        "goal": (workspace.get("task") or {}).get("goal"),
        "status": status,
        "agent_claimed_success": claimed,
        "task_success": None,
        "end_to_end_latency_ms": e2e,
        "model_calls": model_calls if model_calls_present else None,
        "tool_round_trips": sum(round_trips.values()) if tool_calls_present else None,
        "tool_round_trips_by_engine": round_trips,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_input_tokens": cached_tokens,
        "total_tokens": total_tokens,
        "telemetry_coverage": {
            "tool_calls": "complete" if tool_calls_present else "missing",
            "model_calls": "complete" if model_calls_present else "missing",
            "tokens": token_coverage,
            "recovery": recovery_coverage,
        },
        **recovery,
        "handoff_count": len(totals),
        "handoff_prepare_ms": prepare_values,
        "handoff_target_ready_ms": ready_values,
        "handoff_reobserve_ms": reobserve_values,
        "handoff_latency_ms": totals,
        "median_handoff_latency_ms": statistics.median(totals) if totals else None,
    }


def median_of(tasks: list[dict[str, Any]], key: str) -> float | int | None:
    values = [
        task.get(key)
        for task in tasks
        if isinstance(task.get(key), (int, float)) and not isinstance(task.get(key), bool)
    ]
    return statistics.median(values) if values else None


def coverage_rate(tasks: list[dict[str, Any]], key: str) -> float | None:
    if not tasks:
        return None
    return sum(1 for task in tasks if task.get(key) is not None) / len(tasks)


def aggregate(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    claimed = sum(task.get("agent_claimed_success") is True for task in tasks)
    recovered = sum(task.get("recovered") or 0 for task in tasks)
    safe_stopped = sum(task.get("safe_stopped") or 0 for task in tasks)
    failed = sum(task.get("recovery_failed") or 0 for task in tasks)
    eligible = sum(task.get("recovery_eligible") or 0 for task in tasks)
    e2e_values = [
        task["end_to_end_latency_ms"]
        for task in tasks
        if isinstance(task.get("end_to_end_latency_ms"), (int, float))
    ]
    handoff_totals = [value for task in tasks for value in task.get("handoff_latency_ms", [])]
    return {
        "tasks": len(tasks),
        "agent_claimed_successes": claimed,
        "agent_claimed_success_rate": claimed / len(tasks) if tasks else None,
        "task_success": None,
        "task_success_note": "Independent verification is required; run scripts/workspace_to_v2.py with a verifier result.",
        "agent_claimed_end_to_end_latency_ms": e2e_values,
        "median_end_to_end_latency_ms": median_of(tasks, "end_to_end_latency_ms"),
        "p90_end_to_end_latency_ms": p90(e2e_values),
        "median_model_calls": median_of(tasks, "model_calls"),
        "p90_model_calls": p90([task.get("model_calls") for task in tasks]),
        "median_tool_round_trips": median_of(tasks, "tool_round_trips"),
        "telemetry_coverage": {
            "model_calls": coverage_rate(tasks, "model_calls"),
            "tool_calls": coverage_rate(tasks, "tool_round_trips"),
            "tokens": coverage_rate(tasks, "total_tokens"),
            "recovery": sum(
                1 for task in tasks if task.get("telemetry_coverage", {}).get("recovery") == "complete"
            )
            / len(tasks)
            if tasks
            else None,
        },
        "median_input_tokens": median_of(tasks, "input_tokens"),
        "median_output_tokens": median_of(tasks, "output_tokens"),
        "median_total_tokens": median_of(tasks, "total_tokens"),
        "recovery_eligible": eligible,
        "recovered": recovered,
        "safe_stopped": safe_stopped,
        "recovery_failed": failed,
        "recovery_rate": recovered / eligible if eligible else None,
        "handoff_count": len(handoff_totals),
        "median_handoff_latency_ms": statistics.median(handoff_totals) if handoff_totals else None,
        "p90_handoff_latency_ms": p90(handoff_totals),
    }


def load_workspaces(patterns: list[str]) -> list[dict[str, Any]]:
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError as exc:
        raise ValueError(
            "jsonschema is required to validate Workspaces; install requirements-dev.txt"
        ) from exc
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8-sig"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    paths: list[Path] = []
    for pattern in patterns:
        matches = [Path(value) for value in glob.glob(pattern)]
        if not matches and Path(pattern).is_file():
            matches = [Path(pattern)]
        paths.extend(matches)
    unique = sorted(set(paths), key=lambda path: str(path))
    if not unique:
        raise ValueError("No Workspace files matched")
    workspaces = []
    for path in unique:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(value, dict) or "lifecycle" not in value:
            raise ValueError(f"Not a Workspace document: {path}")
        errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
        if errors:
            details = "; ".join(f"{list(error.path)}: {error.message}" for error in errors[:5])
            raise ValueError(f"Workspace failed schema validation: {path}: {details}")
        try:
            validate_timestamps(value)
        except ValueError as exc:
            raise ValueError(f"Invalid timestamp in {path}: {exc}") from exc
        workspaces.append(value)
    return workspaces


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspaces", nargs="+", help="Workspace JSON files or glob patterns")
    parser.add_argument("--output", type=Path, help="Write the metrics JSON to a file")
    args = parser.parse_args()
    try:
        tasks = [workspace_metrics(workspace) for workspace in load_workspaces(args.workspaces)]
        payload = {
            "schema_version": "2.0",
            "per_task": tasks,
            "aggregate": aggregate(tasks),
        }
        rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
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
