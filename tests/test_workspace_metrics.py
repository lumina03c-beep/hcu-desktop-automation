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


class WorkspaceMetricsTests(unittest.TestCase):
    def test_completed_example_metrics(self):
        task = metrics.workspace_metrics(load_completed())
        self.assertTrue(task["task_success"])
        self.assertEqual(task["end_to_end_latency_ms"], 42 * 60 * 1000)
        self.assertEqual(task["model_calls"], 1)
        self.assertEqual(task["tool_round_trips_by_engine"], {"browser": 5, "desktop": 2, "auxiliary": 0})
        self.assertEqual(task["tool_round_trips"], 7)
        self.assertIsNone(task["token_cost"])
        self.assertEqual((task["recovered"], task["recovery_eligible"]), (1, 1))
        self.assertEqual(task["handoff_count"], 2)
        self.assertEqual(task["median_handoff_latency_ms"], 60000)

    def test_missing_telemetry_stays_null(self):
        task = metrics.workspace_metrics(sparse_workspace())
        self.assertFalse(task["task_success"])
        self.assertIsNone(task["end_to_end_latency_ms"])
        self.assertIsNone(task["model_calls"])
        self.assertIsNone(task["token_cost"])
        self.assertEqual(task["recovery_rate"], 0)

    def test_aggregate_rates_and_coverage(self):
        tasks = [
            metrics.workspace_metrics(load_completed()),
            metrics.workspace_metrics(sparse_workspace()),
        ]
        aggregate = metrics.aggregate(tasks)
        self.assertEqual(aggregate["task_completion_rate"], 0.5)
        self.assertEqual(aggregate["median_model_calls"], 1)
        self.assertEqual(aggregate["model_call_coverage"], 0.5)
        self.assertEqual(aggregate["token_coverage"], 0)
        self.assertEqual(aggregate["recovered"], 1)
        self.assertEqual(aggregate["recovery_eligible"], 2)
        self.assertEqual(aggregate["recovery_rate"], 0.5)
        self.assertEqual(aggregate["median_handoff_latency_ms"], 60000)

    def test_load_workspaces_requires_lifecycle(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workspace.json"
            path.write_text(json.dumps({"workspace_id": "x"}))
            with self.assertRaises(ValueError):
                metrics.load_workspaces([str(path)])

    def test_load_workspaces_accepts_globs(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workspace.json"
            path.write_text(json.dumps(load_completed()), encoding="utf-8")
            loaded = metrics.load_workspaces([str(Path(directory) / "*.json")])
            self.assertEqual(len(loaded), 1)


if __name__ == "__main__":
    unittest.main()
