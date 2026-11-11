import copy
import unittest

from workspace_support import iter_keys, load_example, validator


FORBIDDEN_KEY_TOKENS = (
    "password",
    "token",
    "cookie",
    "secret",
    "credential",
    "api_key",
    "element_ref",
    "browser_ref",
    "hcu_ref",
    "targetid",
    "gui_frame",
    "ax_tree",
    "raw_dom",
    "coordinate",
)


class WorkspaceSafetyTests(unittest.TestCase):
    def test_examples_do_not_store_sensitive_or_engine_local_state(self):
        for name in ("initial", "running", "handoff", "blocked", "completed"):
            with self.subTest(example=name):
                locations = [location.lower() for location in iter_keys(load_example(name))]
                for token in FORBIDDEN_KEY_TOKENS:
                    self.assertFalse(
                        any(token in location for location in locations),
                        f"Forbidden token {token!r} found in {name}",
                    )

    def test_artifacts_use_relative_paths(self):
        for name in ("handoff", "blocked", "completed"):
            with self.subTest(example=name):
                for artifact in load_example(name)["artifacts"]:
                    self.assertTrue(artifact["relative_path"].startswith("artifacts/"))
                    self.assertFalse(artifact["relative_path"].startswith("/"))
                    self.assertFalse(":" in artifact["relative_path"])

    def test_safe_stop_cannot_be_reported_as_completed(self):
        data = copy.deepcopy(load_example("completed"))
        data["lifecycle"]["status"] = "safe_stopped"
        data["lifecycle"]["stop_reason"] = "Uncertain external side effect"
        self.assertFalse(validator().is_valid(data))
        self.assertNotEqual(data["lifecycle"]["status"], "completed")

    def test_completed_workspace_has_no_unknown_mutations(self):
        completed = load_example("completed")
        self.assertTrue(
            all(mutation["effect_state"] != "unknown" for mutation in completed["mutations"])
        )

    def test_completed_workspace_has_no_unresolved_steps(self):
        completed = load_example("completed")
        self.assertTrue(
            all(step["status"] in {"completed", "skipped"} for step in completed["steps"])
        )
        self.assertFalse(completed["execution"]["blockers"])

    def test_workspace_examples_do_not_embed_large_raw_payloads(self):
        for name in ("initial", "running", "handoff", "blocked", "completed"):
            with self.subTest(example=name):
                for step in load_example(name)["steps"]:
                    self.assertNotIn("dom", step)
                    self.assertNotIn("ax_tree", step)
                    self.assertNotIn("screenshot_bytes", step)

    def test_engine_context_only_keeps_safe_browser_identity(self):
        for name in ("running", "handoff", "blocked", "completed"):
            with self.subTest(example=name):
                browser = load_example(name)["engine_context"]["browser"]
                self.assertIn("space_id", browser)
                self.assertNotIn("targetId", browser)
                self.assertNotIn("refs", browser)


if __name__ == "__main__":
    unittest.main()
