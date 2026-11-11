import json
import tempfile
import unittest
from pathlib import Path

from workspace_support import (
    WorkspaceConflict,
    WorkspacePersistenceError,
    WorkspaceValidationError,
    load_example,
    load_workspace,
    update_workspace,
    validate,
    write_workspace,
)


class WorkspaceUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.path = self.root / "task-workspaces" / "test" / "workspace.json"

    def tearDown(self):
        self.temporary.cleanup()

    def test_safe_update_increments_revision_and_persists(self):
        write_workspace(self.path, load_example("initial"))
        persisted = update_workspace(
            self.path,
            lambda data: data["lifecycle"].update(
                status="planned", current_phase="stage_planning"
            ),
            expected_revision=1,
        )
        self.assertEqual(persisted["revision"], 2)
        self.assertEqual(persisted["lifecycle"]["status"], "planned")
        self.assertEqual(load_workspace(self.path)["revision"], 2)

    def test_invalid_update_does_not_overwrite_last_good_state(self):
        write_workspace(self.path, load_example("initial"))
        before = self.path.read_text(encoding="utf-8")
        with self.assertRaises(WorkspaceValidationError):
            update_workspace(
                self.path,
                lambda data: data["lifecycle"].update(status="not_a_status"),
                expected_revision=1,
            )
        self.assertEqual(self.path.read_text(encoding="utf-8"), before)

    def test_revision_conflict_is_detected(self):
        data = load_example("initial")
        write_workspace(self.path, data)
        conflicting = dict(data)
        conflicting["revision"] = 2
        write_workspace(self.path, conflicting)
        with self.assertRaises(WorkspaceConflict):
            update_workspace(
                self.path,
                lambda data: None,
                expected_revision=1,
            )

    def test_unreadable_workspace_is_reported_not_hidden(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("{not-json", encoding="utf-8")
        before = self.path.read_text(encoding="utf-8")
        with self.assertRaises(WorkspacePersistenceError):
            load_workspace(self.path)
        self.assertEqual(self.path.read_text(encoding="utf-8"), before)

    def test_unsupported_schema_version_is_rejected(self):
        data = load_example("initial")
        data["schema_version"] = "0.9.0"
        with self.assertRaises(WorkspaceValidationError):
            validate(data)

    def test_write_requires_readback_success(self):
        data = load_example("initial")
        persisted = write_workspace(self.path, data)
        self.assertEqual(persisted["workspace_id"], data["workspace_id"])
        self.assertEqual(persisted["revision"], data["revision"])
        self.assertTrue(self.path.exists())


if __name__ == "__main__":
    unittest.main()
