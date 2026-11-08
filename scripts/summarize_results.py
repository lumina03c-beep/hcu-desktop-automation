#!/usr/bin/env python3
"""Aggregate HCU skill evaluation runs without third-party dependencies."""

from __future__ import annotations

import argparse
import glob
import json
import statistics
import sys
from pathlib import Path
from typing import Any

REQUIRED = {
    "run_id", "case_id", "split", "condition", "synthetic", "task_success",
    "agent_claimed_success", "evidence_level", "hcu_calls", "model_turns",
    "wall_time_ms", "input_tokens", "output_tokens", "recovery",
}


def load_runs(patterns: list[str]) -> list[dict[str, Any]]:
    paths: list[Path] = []
    for pattern in patterns:
        matches = [Path(value) for value in glob.glob(pattern)]
        if not matches and Path(pattern).is_file():
            matches = [Path(pattern)]
        paths.extend(matches)
    unique = sorted(set(paths), key=lambda path: str(path))
    if not unique:
        raise ValueError("No result files matched")
    runs: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for path in unique:
        value = json.loads(path.read_text(encoding="utf-8"))
        items = value.get("runs") if isinstance(value, dict) else value
        if not isinstance(items, list):
            raise ValueError(f"Expected a run array or an object with runs: {path}")
        for run in items:
            if not isinstance(run, dict):
                raise ValueError(f"Non-object run in {path}")
            missing = sorted(REQUIRED - set(run))
            if missing:
                raise ValueError(f"Run {run.get('run_id', '<unknown>')} missing: {', '.join(missing)}")
            if run["run_id"] in seen_ids:
                raise ValueError(f"Duplicate run_id: {run['run_id']}")
            seen_ids.add(run["run_id"])
            runs.append(run)
    return runs


def median(values: list[Any]) -> float | int | None:
    present = [value for value in values if isinstance(value, (int, float)) and not isinstance(value, bool)]
    return statistics.median(present) if present else None


def ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def summarize_group(runs: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(runs)
    successes = sum(run["task_success"] is True for run in runs)
    false_successes = sum(
        run["agent_claimed_success"] is True and run["task_success"] is False for run in runs
    )
    eligible = sum(run["recovery"]["eligible"] for run in runs)
    recovered = sum(run["recovery"]["recovered"] for run in runs)
    known_tokens = [run for run in runs if run["input_tokens"] is not None and run["output_tokens"] is not None]
    first = runs[0]
    return {
        "split": first["split"],
        "condition": first["condition"],
        "runs": count,
        "synthetic_runs": sum(run["synthetic"] is True for run in runs),
        "task_successes": successes,
        "task_success_rate": ratio(successes, count),
        "false_successes": false_successes,
        "false_success_rate": ratio(false_successes, count),
        "median_hcu_calls": median([run["hcu_calls"] for run in runs]),
        "median_shell_api_calls": median([run.get("shell_api_calls") for run in runs]),
        "median_model_turns": median([run["model_turns"] for run in runs]),
        "median_retries": median([run.get("retries") for run in runs]),
        "median_wall_time_ms": median([run["wall_time_ms"] for run in runs]),
        "recovery_eligible": eligible,
        "recovered": recovered,
        "recovery_rate": ratio(recovered, eligible),
        "safe_stopped": sum(run["recovery"]["safe_stopped"] for run in runs),
        "recovery_failed": sum(run["recovery"]["failed"] for run in runs),
        "token_coverage": ratio(len(known_tokens), count),
        "median_input_tokens": median([run["input_tokens"] for run in known_tokens]),
        "median_output_tokens": median([run["output_tokens"] for run in known_tokens]),
        "median_total_tokens": median([
            run["input_tokens"] + run["output_tokens"] for run in known_tokens
        ]),
    }


def summarize(runs: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for run in runs:
        grouped.setdefault((run["split"], run["condition"]), []).append(run)
    groups = [summarize_group(grouped[key]) for key in sorted(grouped)]
    return {
        "schema_version": "1.0",
        "run_count": len(runs),
        "synthetic_run_count": sum(run["synthetic"] is True for run in runs),
        "groups": groups,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", nargs="+", help="Result JSON files or glob patterns")
    parser.add_argument("--output", type=Path, help="Write summary JSON instead of stdout only")
    args = parser.parse_args()
    try:
        summary = summarize(load_runs(args.results))
        rendered = json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
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
