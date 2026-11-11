import copy
import unittest

from workspace_support import load_example, mutation_requires_reobservation


class WorkspaceMutationTests(unittest.TestCase):
    def test_running_mutation_is_prepared_not_confirmed(self):
        mutation = load_example("running")["mutations"][0]
        self.assertEqual(mutation["effect_state"], "prepared")
        self.assertEqual(mutation["verification"]["status"], "not_verified")

    def test_handoff_confirmed_mutation_has_verified_evidence(self):
        mutation = load_example("handoff")["mutations"][0]
        self.assertEqual(mutation["effect_state"], "confirmed")
        self.assertEqual(mutation["verification"]["status"], "verified")
        self.assertIsNotNone(mutation["verification"]["evidence_summary"])

    def test_blocked_mutation_does_not_claim_confirmation(self):
        mutations = load_example("blocked")["mutations"]
        self.assertEqual(mutations[1]["effect_state"], "prepared")
        self.assertEqual(mutations[1]["verification"]["status"], "not_verified")

    def test_completed_mutations_are_all_confirmed(self):
        mutations = load_example("completed")["mutations"]
        self.assertEqual(len(mutations), 3)
        for mutation in mutations:
            with self.subTest(mutation=mutation["mutation_id"]):
                self.assertEqual(mutation["effect_state"], "confirmed")
                self.assertEqual(mutation["verification"]["status"], "verified")
                self.assertIsNotNone(mutation["verification"]["evidence_summary"])

    def test_unknown_mutation_requires_reobservation(self):
        mutation = copy.deepcopy(load_example("blocked")["mutations"][1])
        mutation["effect_state"] = "unknown"
        mutation["verification"]["status"] = "unknown"
        self.assertTrue(mutation_requires_reobservation(mutation))

    def test_dispatched_unverified_mutation_requires_reobservation(self):
        mutation = copy.deepcopy(load_example("running")["mutations"][0])
        mutation["effect_state"] = "dispatched"
        self.assertTrue(mutation_requires_reobservation(mutation))

    def test_confirmed_mutation_does_not_require_reobservation(self):
        mutation = load_example("completed")["mutations"][0]
        self.assertFalse(mutation_requires_reobservation(mutation))

    def test_risk_levels_are_engine_neutral(self):
        mutations = load_example("completed")["mutations"]
        self.assertIn(mutations[0]["risk_level"], {"R0", "R1", "R2"})
        self.assertIn(mutations[1]["risk_level"], {"R0", "R1", "R2"})
        self.assertIn(mutations[2]["risk_level"], {"R0", "R1", "R2"})


if __name__ == "__main__":
    unittest.main()
