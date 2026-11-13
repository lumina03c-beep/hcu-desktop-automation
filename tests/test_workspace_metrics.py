import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "workspace_metrics.py"
SPEC = importlib.util.spec_from_file_location("workspace_metrics", MODULE_PATH)
metrics = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(metrics)

ROOT = Path(__file__).parents[1]


def load_completed():
    path = ROOT / "examples" / "workspace.completed.json"
    return json.loads(path.read_text(encoding="utf-8"))


def sparse_workspace():
    return {
        "workspace_id": "sparse",
        "timestamps": {
            "created_at": "2026-11-10T09:00:00Z",
            "updated_at": "2026-11-10T09:05:00Z",
        },
        "task": {"goal": "Sparse task"},
        "lifecycle": {
            "status": "failed",
            "started_at": "2026-11-10T09:00:00Z",
            "completed_at": None,
        },
        "result": {"status": "failed"},
        "handoffs": [],
        "events": [
            {
                "event_id": "event-001",
                "at": "2026-11-10T09:01:00Z",
                "engine": "desktop",
                "kind": "recovery",
                "round_trips": 1,
                "outcome": "failed",
            },
            {
                "event_id": "event-002",
                "at": "2026-11-10T09:02:00Z",
                "engine": "desktop",
                "kind": "engine_call",
                "round_trips": 2,
                "outcome": "failed",
            },
        ],
    }


def empty_events_workspace():
    workspace = sparse_workspace()
    workspace["events"] = []
    return workspace


class WorkspaceMetricsTests(unittest.TestCase):
    def test_completed_example_metrics(self):
        task = metrics.workspace_metrics(load_completed())
        self.assertTrue(task["agent_claimed_success"])
        self.assertIsNone(task["task_success"])
        self.assertEqual(task["end_to_end_latency_ms"], 42 * 60 * 1000)
        self.assertEqual(task["model_calls"], 1)
        self.assertEqual(task["tool_round_trips_by_engine"], {"browser": 5, "desktop": 2, "auxiliary": 0})
        self.assertEqual(task["tool_round_trips"], 7)
        self.assertEqual(
            (task["input_tokens"], task["output_tokens"], task["cached_input_tokens"], task["total_tokens"]),
            (12000, 900, 6000, 12900),
        )
        self.assertEqual(task["telemetry_coverage"]["tokens"], "complete")
        self.assertEqual((task["recovered"], task["recovery_eligible"], task["safe_stopped"]), (1, 1, 0))
        self.assertEqual(task["handoff_count"], 2)
        self.assertEqual(task["handoff_prepare_ms"], [40000, 40000])
        self.assertEqual(task["handoff_target_ready_ms"], [40000, 50000])
        self.assertEqual(task["handoff_reobserve_ms"], [20000, 10000])
        self.assertEqual(task["handoff_latency_ms"], [60000, 60000])
        self.assertEqual(task["median_handoff_latency_ms"], 60000)

    def test_missing_telemetry_stays_null(self):
        task = metrics.workspace_metrics(sparse_workspace())
        self.assertFalse(task["agent_claimed_success"])
        self.assertIsNone(task["end_to_end_latency_ms"])
        self.assertIsNone(task["model_calls"])
        self.assertIsNone(task["input_tokens"])
        self.assertIsNone(task["output_tokens"])
        self.assertIsNone(task["total_tokens"])
        self.assertEqual(task["tool_round_trips"], 3)
        self.assertEqual(task["recovered"], 0)
        self.assertEqual(task["recovery_eligible"], 1)
        self.assertEqual(task["recovery_rate"], 0)
        self.assertEqual(task["telemetry_coverage"]["recovery"], "complete")

    def test_empty_events_report_missing_not_zero(self):
        task = metrics.workspace_metrics(empty_events_workspace())
        self.assertIsNone(task["tool_round_trips"])
        self.assertIsNone(task["model_calls"])
        self.assertEqual(task["telemetry_coverage"]["tool_calls"], "missing")
        self.assertEqual(task["telemetry_coverage"]["model_calls"], "missing")
        self.assertEqual(task["telemetry_coverage"]["tokens"], "missing")

    def test_zero_tool_calls_are_real_zero(self):
        workspace = load_completed()
        for event in workspace["events"]:
            event["round_trips"] = 0
        task = metrics.workspace_metrics(workspace)
        self.assertEqual(task["tool_round_trips"], 0)
        self.assertEqual(task["telemetry_coverage"]["tool_calls"], "complete")

    def test_explicit_ineligible_recovery_excluded(self):
        workspace = load_completed()
        workspace["events"].append(
            {
                "event_id": "event-010",
                "at": "2026-11-10T08:45:00Z",
                "engine": "desktop",
                "kind": "recovery",
                "round_trips": 1,
                "outcome": "safe_stopped",
                "eligible": False,
            }
        )
        task = metrics.workspace_metrics(workspace)
        self.assertEqual(task["recovery_eligible"], 1)
        self.assertEqual(task["safe_stopped"], 0)

    def test_naive_timestamp_rejected(self):
        workspace = load_completed()
        workspace["lifecycle"]["completed_at"] = "2026-11-10T08:44:00"
        with self.assertRaises(ValueError):
            metrics.workspace_metrics(workspace)

    def test_negative_duration_rejected(self):
        workspace = load_completed()
        workspace["lifecycle"]["completed_at"] = "2026-11-10T08:00:00Z"
        with self.assertRaises(ValueError):
            metrics.workspace_metrics(workspace)

    def test_legacy_tokens_fallback(self):
        workspace = load_completed()
        for event in workspace["events"]:
            event.pop("input_tokens", None)
            event.pop("output_tokens", None)
            event.pop("cached_input_tokens", None)
        workspace["events"][1]["tokens"] = 500
        task = metrics.workspace_metrics(workspace)
        self.assertEqual(task["total_tokens"], 500)
        self.assertEqual(task["telemetry_coverage"]["tokens"], "partial")

    def test_aggregate_rates_and_coverage(self):
        tasks = [
            metrics.workspace_metrics(load_completed()),
            metrics.workspace_metrics(sparse_workspace()),
        ]
        aggregate = metrics.aggregate(tasks)
        self.assertEqual(aggregate["agent_claimed_success_rate"], 0.5)
        self.assertIsNone(aggregate["task_success"])
        self.assertEqual(aggregate["median_model_calls"], 1)
        self.assertEqual(aggregate["telemetry_coverage"]["model_calls"], 0.5)
        self.assertEqual(aggregate["telemetry_coverage"]["tokens"], 0.5)
        self.assertEqual(aggregate["recovered"], 1)
        self.assertEqual(aggregate["recovery_eligible"], 2)
        self.assertEqual(aggregate["recovery_rate"], 0.5)
        self.assertEqual(aggregate["median_handoff_latency_ms"], 60000)
        self.assertEqual(aggregate["p90_end_to_end_latency_ms"], 2520000)

    def test_load_workspaces_requires_lifecycle(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workspace.json"
            path.write_text(json.dumps({"workspace_id": "x"}))
            with self.assertRaises(ValueError):
                metrics.load_workspaces([str(path)])

    def test_load_workspaces_accepts_globs_and_bom(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workspace.json"
            path.write_text(json.dumps(load_completed()), encoding="utf-8-sig")
            loaded = metrics.load_workspaces([str(Path(directory) / "*.json")])
            self.assertEqual(len(loaded), 1)

    def test_load_workspaces_rejects_schema_violations(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workspace.json"
            broken = load_completed()
            broken["events"].append({"unexpected": True})
            path.write_text(json.dumps(broken), encoding="utf-8")
            with self.assertRaises(ValueError):
                metrics.load_workspaces([str(path)])

    def test_load_workspaces_rejects_invalid_timestamp_format(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workspace.json"
            broken = load_completed()
            broken["lifecycle"]["completed_at"] = "not-a-date"
            path.write_text(json.dumps(broken), encoding="utf-8")
            with self.assertRaises(ValueError):
                metrics.load_workspaces([str(path)])


if __name__ == "__main__":
    unittest.main()
