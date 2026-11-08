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


class SummarizerTests(unittest.TestCase):
    def test_false_success_is_independent_from_task_success(self):
        summary = summarizer.summarize([run("a", success=False, claimed=True)])
        group = summary["groups"][0]
        self.assertEqual(group["task_success_rate"], 0)
        self.assertEqual(group["false_successes"], 1)
        self.assertEqual(group["false_success_rate"], 1)

    def test_groups_and_medians(self):
        summary = summarizer.summarize([
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
            self.assertEqual(len(summarizer.load_runs([str(path)])), 1)
            path.write_text(json.dumps({"runs": [run("a"), run("a")]}))
            with self.assertRaises(ValueError):
                summarizer.load_runs([str(path)])


if __name__ == "__main__":
    unittest.main()
