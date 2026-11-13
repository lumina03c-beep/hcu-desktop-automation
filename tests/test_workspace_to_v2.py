import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "workspace_to_v2.py"
SPEC = importlib.util.spec_from_file_location("workspace_to_v2", MODULE_PATH)
adapter = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(adapter)

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import workspace_metrics as metrics  # noqa: E402

ROOT = Path(__file__).parents[1]
RUNTIME_METRICS = {
    "browser_snapshots": 6,
    "browser_screenshots": 1,
    "desktop_ax_calls": 5,
    "desktop_gui_calls": 1,
    "duplicate_mutations": 0,
}


class AdapterArgs:
    def __init__(self, **overrides):
        self.case_id = "case-1"
        self.run_id = None
        self.verified = "true"
        self.verifier = "test-verifier"
        self.platform = "windows"
        self.client = "test-client"
        self.model = "test-model"
        self.split = "development"
        self.condition = "C"
        self.synthetic = False
        self.evidence_level = None
        self.skill_version = None
        self.metrics_file = None
        self.notes = None
        for key, value in overrides.items():
            setattr(self, key, value)


class WorkspaceToV2Tests(unittest.TestCase):
    def setUp(self):
        self.workspace = json.loads(
            (ROOT / "examples" / "workspace.completed.json").read_text(encoding="utf-8")
        )
        self.task = metrics.workspace_metrics(self.workspace)

    def build(self, args=None):
        return adapter.build_record(args or AdapterArgs(), self.workspace, self.task)

    def test_happy_path_validates_against_v2_schema(self):
        record = self.build(AdapterArgs(metrics_file=RUNTIME_METRICS, synthetic=True))
        adapter.validate_record(record)
        self.assertTrue(record["task_success"])
        self.assertTrue(record["agent_claimed_success"])
        self.assertEqual(record["skill_version"], "5.4.0")
        self.assertEqual(record["engine_profile"], "hybrid")
        self.assertEqual(record["evidence_level"], "L3")
        self.assertEqual(record["metrics"]["browser_calls"], 5)
        self.assertEqual(record["metrics"]["input_tokens"], 12000)
        self.assertEqual(record["recovery"], {"eligible": 1, "recovered": 1, "safe_stopped": 0, "failed": 0})
        self.assertEqual(record["error_codes"], ["stale_ref"])

    def test_missing_independent_verification_is_refused(self):
        with self.assertRaises(ValueError):
            self.build(AdapterArgs(verified=None, metrics_file=RUNTIME_METRICS))

    def test_missing_runtime_metrics_are_reported_not_invented(self):
        with self.assertRaises(ValueError) as context:
            self.build()
        message = str(context.exception)
        for name in ("browser_snapshots", "desktop_ax_calls", "duplicate_mutations"):
            self.assertIn(name, message)

    def test_missing_recovery_telemetry_is_refused(self):
        workspace = json.loads(json.dumps(self.workspace))
        workspace["events"] = [event for event in workspace["events"] if event["kind"] != "recovery"]
        task = metrics.workspace_metrics(workspace)
        with self.assertRaises(ValueError) as context:
            adapter.build_record(AdapterArgs(metrics_file=RUNTIME_METRICS), workspace, task)
        self.assertIn("recovery", str(context.exception))

    def test_task_success_false_is_recorded_as_claimed_mismatch(self):
        record = self.build(AdapterArgs(verified="false", metrics_file=RUNTIME_METRICS))
        adapter.validate_record(record)
        self.assertFalse(record["task_success"])
        self.assertTrue(record["agent_claimed_success"])

    def test_no_telemetry_falls_back_to_metrics_file(self):
        workspace = json.loads(json.dumps(self.workspace))
        workspace["events"] = []
        task = metrics.workspace_metrics(workspace)
        supplied = {
            **RUNTIME_METRICS,
            "model_calls": 9,
            "browser_calls": 4,
            "desktop_calls": 2,
            "auxiliary_calls": 1,
            "wall_time_ms": 420000,
            "recovery": {"eligible": 0, "recovered": 0, "safe_stopped": 0, "failed": 0},
        }
        record = adapter.build_record(AdapterArgs(metrics_file=supplied), workspace, task)
        adapter.validate_record(record)
        self.assertIsNone(record["metrics"]["input_tokens"])
        self.assertEqual(record["metrics"]["model_calls"], 9)

    def test_cli_writes_valid_record_file(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace_path = Path(directory) / "workspace.json"
            metrics_path = Path(directory) / "metrics.json"
            output_path = Path(directory) / "record.json"
            workspace_path.write_text(json.dumps(self.workspace), encoding="utf-8")
            metrics_path.write_text(json.dumps(RUNTIME_METRICS), encoding="utf-8")
            argv = [
                str(MODULE_PATH),
                str(workspace_path),
                "--case-id", "case-1",
                "--verified", "true",
                "--verifier", "test-verifier",
                "--platform", "windows",
                "--client", "test-client",
                "--model", "test-model",
                "--synthetic",
                "--metrics-file", str(metrics_path),
                "--output", str(output_path),
            ]
            import subprocess
            result = subprocess.run([sys.executable, *argv], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            record = json.loads(output_path.read_text(encoding="utf-8"))
            adapter.validate_record(record)


if __name__ == "__main__":
    unittest.main()
