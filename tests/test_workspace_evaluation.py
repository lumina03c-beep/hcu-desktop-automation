import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "evaluations" / "v2" / "result.schema.json"
EXAMPLE_PATH = ROOT / "evaluations" / "v2" / "example-results.json"


class WorkspaceEvaluationSchemaTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.validator = Draft202012Validator(self.schema, format_checker=FormatChecker())
        self.runs = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))

    def test_example_runs_validate_against_v2_schema(self):
        self.assertEqual(len(self.runs), 2)
        for run in self.runs:
            with self.subTest(run=run["run_id"]):
                self.assertTrue(self.validator.is_valid(run))

    def test_all_example_runs_are_synthetic(self):
        self.assertTrue(all(run["synthetic"] is True for run in self.runs))

    def test_false_success_is_represented(self):
        baseline = next(run for run in self.runs if run["condition"] == "A")
        self.assertFalse(baseline["task_success"])
        self.assertTrue(baseline["agent_claimed_success"])

    def test_verified_run_reports_l3(self):
        candidate = next(run for run in self.runs if run["condition"] == "B")
        self.assertTrue(candidate["task_success"])
        self.assertEqual(candidate["evidence_level"], "L3")

    def test_metric_fields_exist(self):
        for run in self.runs:
            with self.subTest(run=run["run_id"]):
                metrics = run["metrics"]
                for field in (
                    "model_calls",
                    "browser_calls",
                    "desktop_calls",
                    "auxiliary_calls",
                    "input_tokens",
                    "output_tokens",
                    "wall_time_ms",
                    "handoff_latency_ms",
                    "duplicate_mutations",
                ):
                    self.assertIn(field, metrics)

    def test_v2_schema_rejects_extra_fields(self):
        run = dict(self.runs[0])
        run["unexpected_field"] = "not allowed"
        self.assertFalse(self.validator.is_valid(run))


if __name__ == "__main__":
    unittest.main()
