import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "summarize_results.py"
SPEC = importlib.util.spec_from_file_location("summarize_results", MODULE_PATH)
summarizer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(summarizer)


def run(run_id, condition="A", success=False, claimed=True, tokens=None):
    return {
        "run_id": run_id,
        "case_id": "case-1",
        "split": "holdout",
        "condition": condition,
        "synthetic": True,
        "task_success": success,
        "agent_claimed_success": claimed,
        "evidence_level": "L3" if success else "L1",
        "hcu_calls": 5,
        "shell_api_calls": 1,
        "model_turns": 4,
        "retries": 1,
        "wall_time_ms": 1000,
        "input_tokens": tokens,
        "output_tokens": tokens,
        "recovery": {"eligible": 1, "recovered": 1 if success else 0, "safe_stopped": 0, "failed": 0 if success else 1},
    }


def v2_run(run_id, condition="C", success=True, claimed=True):
    return {
        "schema_version": "2.0.0",
        "run_id": run_id,
        "case_id": "case-1",
        "split": "holdout",
        "condition": condition,
        "synthetic": True,
        "started_at": "2026-11-11T09:00:00Z",
        "platform": "windows",
        "client": "test-client",
        "model": "test-model",
        "skill_version": "5.4.0",
        "engine_profile": "hybrid",
        "task_success": success,
        "agent_claimed_success": claimed,
        "independent_verifier": "test-verifier",
        "evidence_level": "L3" if success else "L1",
        "metrics": {
            "model_calls": 10,
            "browser_calls": 5,
            "desktop_calls": 3,
            "auxiliary_calls": 1,
            "browser_snapshots": 4,
            "browser_screenshots": 0,
            "desktop_ax_calls": 2,
            "desktop_gui_calls": 1,
            "input_tokens": 1000,
            "output_tokens": 100,
            "wall_time_ms": 60000,
            "handoff_latency_ms": 40000,
            "duplicate_mutations": 0,
        },
        "recovery": {"eligible": 1, "recovered": 1 if success else 0, "safe_stopped": 0, "failed": 0 if success else 1},
        "error_codes": [],
    }


class SummarizerTests(unittest.TestCase):
    def test_false_success_is_independent_from_task_success(self):
        summary = summarizer.summarize("v1", [run("a", success=False, claimed=True)])
        group = summary["groups"][0]
        self.assertEqual(group["task_success_rate"], 0)
        self.assertEqual(group["false_successes"], 1)
        self.assertEqual(group["false_success_rate"], 1)

    def test_groups_and_medians(self):
        summary = summarizer.summarize("v1", [
            run("a", "A", False, True),
            run("b", "B", True, True, 100),
            run("c", "C", True, True, 200),
        ])
        self.assertEqual(summary["run_count"], 3)
        self.assertEqual([group["condition"] for group in summary["groups"]], ["A", "B", "C"])
        self.assertEqual(summary["groups"][1]["median_total_tokens"], 200)
        self.assertEqual(summary["groups"][0]["token_coverage"], 0)

    def test_loads_schema_object_and_rejects_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.json"
            path.write_text(json.dumps({"schema_version": "1.0", "runs": [run("a")]}))
            version, runs = summarizer.load_runs([str(path)])
            self.assertEqual(version, "v1")
            self.assertEqual(len(runs), 1)
            path.write_text(json.dumps({"runs": [run("a"), run("a")]}))
            with self.assertRaises(ValueError):
                summarizer.load_runs([str(path)])

    def test_v2_records_summarize_by_condition(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "v2.json"
            path.write_text(json.dumps([v2_run("v1", "A", success=False), v2_run("v2", "B", success=True)]))
            version, runs = summarizer.load_runs([str(path)])
        self.assertEqual(version, "v2")
        summary = summarizer.summarize(version, runs)
        self.assertEqual(summary["record_schema"], "v2")
        groups = summary["groups"]
        self.assertEqual([group["condition"] for group in groups], ["A", "B"])
        self.assertEqual(groups[0]["task_success_rate"], 0)
        self.assertEqual(groups[0]["false_successes"], 1)
        self.assertEqual(groups[0]["recovery_rate"], 0)
        self.assertEqual(groups[1]["median_model_calls"], 10)
        self.assertEqual(groups[1]["median_total_tokens"], 1100)
        self.assertEqual(groups[1]["duplicate_mutations"], 0)

    def test_mixed_v1_v2_batches_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mixed.json"
            path.write_text(json.dumps([run("a"), v2_run("b")]))
            with self.assertRaises(ValueError):
                summarizer.load_runs([str(path)])

    def test_v2_missing_metrics_fields_rejected(self):
        incomplete = v2_run("x")
        del incomplete["metrics"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "incomplete.json"
            path.write_text(json.dumps([incomplete]))
            with self.assertRaises(ValueError):
                summarizer.load_runs([str(path)])


if __name__ == "__main__":
    unittest.main()
