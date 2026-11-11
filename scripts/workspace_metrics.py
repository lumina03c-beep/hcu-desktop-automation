#!/usr/bin/env python3
"""Compute task-level metrics from Dynamic UI RPA Workspace files.

Metrics follow the V2 definitions: completion, end-to-end latency, model calls,
tool round trips, token cost, recovery rate, and handoff latency. Missing
telemetry stays null instead of being estimated.
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
ENGINE_CALLS = {"browser", "desktop", "auxiliary"}


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def elapsed_ms(start: datetime | None, end: datetime | None) -> int | None:
    if start is None or end is None:
        return None
    return max(0, int((end - start).total_seconds() * 1000))


def count(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def workspace_metrics(workspace: dict[str, Any]) -> dict[str, Any]:
    lifecycle = workspace.get("lifecycle") or {}
    timestamps = workspace.get("timestamps") or {}
    result = workspace.get("result") or {}
    events = workspace.get("events") or []
    round_trips = {"browser": 0, "desktop": 0, "auxiliary": 0, "agent": 0}
    model_calls = 0
    model_seen = False
    tokens = 0
    token_seen = False
    eligible = 0
    recovered = 0
    for event in events:
        if not isinstance(event, dict):
            continue
        engine = event.get("engine")
        kind = event.get("kind")
        trips = count(event.get("round_trips"))
        if engine in round_trips:
            round_trips[engine] += trips
        if kind == "model_call":
            model_seen = True
            model_calls += trips or 1
        value = event.get("tokens")
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            tokens += value
            token_seen = True
        if kind == "recovery":
            eligible += 1
            if event.get("outcome") == "recovered":
                recovered += 1
    handoff_latencies = []
    for handoff in workspace.get("handoffs") or []:
        if isinstance(handoff, dict):
            latency = elapsed_ms(
                parse_time(handoff.get("created_at")),
                parse_time(handoff.get("completed_at")),
            )
            if latency is not None:
                handoff_latencies.append(latency)
    status = lifecycle.get("status")
    started = parse_time(lifecycle.get("started_at")) or parse_time(timestamps.get("created_at"))
    finished = parse_time(lifecycle.get("completed_at"))
    e2e = elapsed_ms(started, finished) if status in TERMINAL_STATES else None
    engine_trips = {name: round_trips[name] for name in ENGINE_CALLS}
    return {
        "workspace_id": workspace.get("workspace_id"),
        "goal": (workspace.get("task") or {}).get("goal"),
        "status": status,
        "task_success": result.get("status") == "completed",
        "end_to_end_latency_ms": e2e,
        "model_calls": model_calls if model_seen else None,
        "tool_round_trips": sum(engine_trips.values()),
        "tool_round_trips_by_engine": engine_trips,
        "token_cost": tokens if token_seen else None,
        "recovery_eligible": eligible,
        "recovered": recovered,
        "recovery_rate": recovered / eligible if eligible else None,
        "handoff_count": len(handoff_latencies),
        "handoff_latency_ms": handoff_latencies,
        "median_handoff_latency_ms": statistics.median(handoff_latencies) if handoff_latencies else None,
    }


def median_of(tasks: list[dict[str, Any]], key: str) -> float | int | None:
    values = [
        task.get(key)
        for task in tasks
        if isinstance(task.get(key), (int, float)) and not isinstance(task.get(key), bool)
    ]
    return statistics.median(values) if values else None


def aggregate(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    successes = sum(task.get("task_success") is True for task in tasks)
    eligible = sum(task.get("recovery_eligible", 0) for task in tasks)
    recovered = sum(task.get("recovered", 0) for task in tasks)
    handoffs = [value for task in tasks for value in task.get("handoff_latency_ms", [])]
    return {
        "tasks": len(tasks),
        "task_successes": successes,
        "task_completion_rate": successes / len(tasks) if tasks else None,
        "median_end_to_end_latency_ms": median_of(tasks, "end_to_end_latency_ms"),
        "median_model_calls": median_of(tasks, "model_calls"),
        "median_tool_round_trips": median_of(tasks, "tool_round_trips"),
        "model_call_coverage": (
            sum(task.get("model_calls") is not None for task in tasks) / len(tasks) if tasks else None
        ),
        "median_token_cost": median_of(tasks, "token_cost"),
        "token_coverage": (
            sum(task.get("token_cost") is not None for task in tasks) / len(tasks) if tasks else None
        ),
        "recovery_eligible": eligible,
        "recovered": recovered,
        "recovery_rate": recovered / eligible if eligible else None,
        "handoff_count": len(handoffs),
        "median_handoff_latency_ms": statistics.median(handoffs) if handoffs else None,
    }


def load_workspaces(patterns: list[str]) -> list[dict[str, Any]]:
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
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or "lifecycle" not in value:
            raise ValueError(f"Not a Workspace document: {path}")
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
            "schema_version": "1.0",
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
