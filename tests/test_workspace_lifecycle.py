import copy
import unittest

from workspace_support import load_example, validator


class WorkspaceLifecycleTests(unittest.TestCase):
    def test_examples_share_one_workspace_identity(self):
        ids = {
            load_example(name)["workspace_id"]
            for name in ("initial", "running", "handoff", "blocked", "completed")
        }
        self.assertEqual(len(ids), 1)

    def test_revision_increases_across_lifecycle(self):
        revisions = [
            load_example(name)["revision"]
            for name in ("initial", "running", "handoff", "blocked", "completed")
        ]
        self.assertEqual(revisions, sorted(revisions))
        self.assertEqual(len(set(revisions)), len(revisions))

    def test_expected_lifecycle_statuses(self):
        expected = {
            "initial": "created",
            "running": "running",
            "handoff": "running",
            "blocked": "blocked",
            "completed": "completed",
        }
        for name, status in expected.items():
            with self.subTest(example=name):
                self.assertEqual(load_example(name)["lifecycle"]["status"], status)

    def test_result_status_matches_terminal_lifecycle(self):
        blocked = load_example("blocked")
        completed = load_example("completed")
        self.assertEqual(blocked["result"]["status"], "blocked")
        self.assertEqual(completed["result"]["status"], "completed")

    def test_running_example_has_active_browser_stage(self):
        running = load_example("running")
        self.assertEqual(running["routing"]["active_engine"], "browser")
        self.assertEqual(routing_stage_status(running, "stage-001"), "in_progress")

    def test_handoff_preserves_browser_taskspace(self):
        handoff = load_example("handoff")
        self.assertEqual(handoff["routing"]["active_engine"], "desktop")
        self.assertEqual(handoff["engine_context"]["browser"]["status"], "active")
        self.assertIsNotNone(handoff["engine_context"]["browser"]["space_id"])

    def test_blocked_example_records_reason_and_blocker(self):
        blocked = load_example("blocked")
        self.assertEqual(blocked["lifecycle"]["status"], "blocked")
        self.assertIn("Desktop engine unavailable", blocked["execution"]["blockers"])
        self.assertIsNotNone(blocked["lifecycle"]["stop_reason"])

    def test_completed_example_has_final_timestamp_and_summary(self):
        completed = load_example("completed")
        self.assertEqual(completed["lifecycle"]["status"], "completed")
        self.assertIsNotNone(completed["lifecycle"]["completed_at"])
        self.assertIsNotNone(completed["result"]["verification_summary"])
        self.assertTrue(
            all(step["status"] in {"completed", "skipped"} for step in completed["steps"])
        )

    def test_safe_stop_is_not_completion(self):
        data = copy.deepcopy(load_example("completed"))
        data["lifecycle"]["status"] = "safe_stopped"
        data["lifecycle"]["stop_reason"] = "Uncertain external side effect"
        data["result"]["status"] = "safe_stopped"
        self.assertTrue(validator().is_valid(data))
        self.assertNotEqual(data["lifecycle"]["status"], "completed")
        self.assertNotEqual(data["result"]["status"], "completed")


def routing_stage_status(data, stage_id):
    for stage in data["routing"]["planned_stages"]:
        if stage["stage_id"] == stage_id:
            return stage["status"]
    raise AssertionError(f"Stage {stage_id} not found")


if __name__ == "__main__":
    unittest.main()
