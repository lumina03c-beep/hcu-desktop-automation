import tempfile
import unittest
import uuid
from pathlib import Path

from workspace_support import load_example, update_workspace, write_workspace


class WorkspaceHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_handoff_record_is_prepared_semantically(self):
        handoff = load_example("handoff")["handoffs"][0]
        self.assertEqual(handoff["from_engine"], "browser")
        self.assertEqual(handoff["to_engine"], "desktop")
        self.assertEqual(handoff["status"], "prepared")
        self.assertIsNone(handoff["completed_at"])
        self.assertIn("Customer record created", handoff["last_verified_state"])
        self.assertIn("native desktop application", handoff["pending_action"])

    def test_handoff_updates_active_engine_and_stage(self):
        data = load_example("handoff")
        self.assertEqual(data["routing"]["active_engine"], "desktop")
        self.assertEqual(data["routing"]["active_stage_id"], "stage-002")
        self.assertEqual(data["routing"]["last_handoff_id"], "handoff-001")

    def test_browser_taskspace_survives_temporary_handoff(self):
        data = load_example("handoff")
        self.assertEqual(data["engine_context"]["browser"]["status"], "active")
        self.assertEqual(data["engine_context"]["browser"]["space_id"], "7")
        self.assertEqual(data["engine_context"]["desktop"]["status"], "ready")

    def test_completed_example_contains_two_handoffs(self):
        data = load_example("completed")
        self.assertEqual(len(data["handoffs"]), 2)
        self.assertTrue(all(item["status"] == "completed" for item in data["handoffs"]))
        self.assertEqual(data["routing"]["active_engine"], "browser")
        self.assertEqual(data["routing"]["last_handoff_id"], "handoff-002")

    def test_handoff_completion_is_persisted_without_new_workspace(self):
        path = self.root / "task-workspaces" / "case" / "workspace.json"
        write_workspace(path, load_example("handoff"))
        persisted = update_workspace(
            path,
            lambda data: data["handoffs"][0].update(
                status="completed", completed_at="2026-11-10T08:24:00Z"
            ),
            expected_revision=7,
        )
        self.assertEqual(persisted["workspace_id"], load_example("handoff")["workspace_id"])
        self.assertEqual(persisted["revision"], 8)
        self.assertEqual(persisted["handoffs"][0]["status"], "completed")
        self.assertEqual(persisted["routing"]["last_handoff_id"], "handoff-001")

    def test_separate_tasks_use_separate_workspaces(self):
        first = load_example("initial")
        second = load_example("initial")
        second["workspace_id"] = str(uuid.uuid4())
        first_path = self.root / "task-workspaces" / "first" / "workspace.json"
        second_path = self.root / "task-workspaces" / "second" / "workspace.json"
        write_workspace(first_path, first)
        write_workspace(second_path, second)
        self.assertNotEqual(first_path, second_path)
        self.assertNotEqual(first["workspace_id"], second["workspace_id"])


if __name__ == "__main__":
    unittest.main()
