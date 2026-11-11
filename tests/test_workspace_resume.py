import unittest

from workspace_support import load_example, next_pending_step


class WorkspaceResumeTests(unittest.TestCase):
    def test_running_resume_targets_current_step(self):
        running = load_example("running")
        step = next_pending_step(running)
        self.assertIsNotNone(step)
        self.assertEqual(step["step_id"], "step-001")
        self.assertNotEqual(step["status"], "completed")

    def test_handoff_resume_preserves_completed_browser_step(self):
        handoff = load_example("handoff")
        completed = [step for step in handoff["steps"] if step["status"] == "completed"]
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0]["step_id"], "step-001")
        self.assertEqual(next_pending_step(handoff)["step_id"], "step-002")

    def test_blocked_resume_continues_from_unfinished_step(self):
        blocked = load_example("blocked")
        step = next_pending_step(blocked)
        self.assertEqual(step["step_id"], "step-002")
        self.assertEqual(step["status"], "blocked")
        self.assertIn("Desktop engine unavailable", blocked["execution"]["blockers"])

    def test_completed_workspace_has_no_pending_step(self):
        completed = load_example("completed")
        self.assertIsNone(next_pending_step(completed))

    def test_resume_keeps_browser_taskspace_identity(self):
        for name in ("running", "handoff", "blocked", "completed"):
            with self.subTest(example=name):
                data = load_example(name)
                self.assertEqual(data["engine_context"]["browser"]["space_id"], "7")

    def test_resume_does_not_reset_verified_steps(self):
        handoff = load_example("handoff")
        blocked = load_example("blocked")
        completed = load_example("completed")
        for data in (handoff, blocked, completed):
            verified = [
                step
                for step in data["steps"]
                if step["status"] == "completed"
            ]
            self.assertTrue(verified)
            for step in verified:
                self.assertEqual(step["verification"]["status"], "verified")
                self.assertIsNotNone(step["verification"]["summary"])


if __name__ == "__main__":
    unittest.main()
