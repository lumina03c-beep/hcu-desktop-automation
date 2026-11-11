import copy
import unittest

from workspace_support import load_example, validator


class WorkspaceSchemaTests(unittest.TestCase):
    def test_bundled_examples_validate(self):
        for name in ("initial", "running", "handoff", "blocked", "completed"):
            with self.subTest(example=name):
                self.assertTrue(validator().is_valid(load_example(name)))

    def test_missing_required_top_level_field_is_invalid(self):
        data = load_example("initial")
        del data["workspace_id"]
        self.assertFalse(validator().is_valid(data))

    def test_extra_top_level_property_is_invalid(self):
        data = load_example("initial")
        data["password"] = "not-allowed"
        self.assertFalse(validator().is_valid(data))

    def test_illegal_lifecycle_status_is_invalid(self):
        data = load_example("running")
        data["lifecycle"]["status"] = "semi_finished"
        self.assertFalse(validator().is_valid(data))

    def test_artifact_path_must_stay_under_artifacts(self):
        data = load_example("completed")
        data["artifacts"][0]["relative_path"] = "files/outside.json"
        self.assertFalse(validator().is_valid(data))

    def test_prepared_handoff_must_not_have_completion_time(self):
        data = load_example("handoff")
        data["handoffs"][0]["completed_at"] = "2026-11-10T08:24:00Z"
        self.assertFalse(validator().is_valid(data))

    def test_completed_step_requires_verified_evidence(self):
        data = load_example("completed")
        data["steps"][0]["verification"]["status"] = "not_verified"
        self.assertFalse(validator().is_valid(data))

    def test_completed_task_requires_verification_summary(self):
        data = load_example("completed")
        data["result"]["verification_summary"] = None
        self.assertFalse(validator().is_valid(data))

    def test_safe_stop_requires_stop_reason(self):
        data = load_example("completed")
        data["lifecycle"]["status"] = "safe_stopped"
        data["result"]["status"] = "safe_stopped"
        data["lifecycle"]["stop_reason"] = None
        self.assertFalse(validator().is_valid(data))

    def test_unknown_mutation_cannot_claim_verified_evidence(self):
        data = copy.deepcopy(load_example("blocked"))
        data["mutations"][1]["effect_state"] = "unknown"
        data["mutations"][1]["verification"]["status"] = "verified"
        data["mutations"][1]["verification"]["evidence_summary"] = "not allowed"
        self.assertFalse(validator().is_valid(data))


if __name__ == "__main__":
    unittest.main()
