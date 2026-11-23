"""Offline regression checks for the frozen A-004R experiment router."""
import importlib.util
import unittest
from pathlib import Path


RUNNER = Path(__file__).with_name("run_a004r.py")
SPEC = importlib.util.spec_from_file_location("run_a004r", RUNNER)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class RoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        values = runner.verify_inputs()
        cls.frozen, cls.matrix, cls.queries, cls.old = values[1:5]
        cls.approved, cls.no_image, cls.internal = values[5:8]
        cls.routes = runner.build_routes(*values[1:8])
        cls.by_id = {row["vocab_id"]: row for row in cls.routes}

    def row(self, number):
        return self.by_id[f"vocab-{number:06d}"]

    def test_all_ids_are_unique_and_required(self):
        self.assertEqual(len(self.routes), len(self.by_id), 100)
        for altered in (self.frozen[:-1], self.frozen + self.frozen[:1]):
            with self.assertRaises(ValueError):
                runner.build_routes(altered, self.matrix, self.queries, self.old,
                                    self.approved, self.no_image, self.internal)

    def test_concrete_and_verified_icon_queries(self):
        for number in (1, 11, 28):
            self.assertEqual(self.row(number)["routing_strategy"], "NORMAL")
            self.assertFalse(self.row(number)["experimental_search_query"].endswith(" icon"))
        for number in (53, 56, 65):
            row = self.row(number)
            self.assertEqual(row["routing_strategy"], "ICON")
            self.assertEqual(row["experimental_search_query"], row["english"] + " icon")
            self.assertEqual(row["execution_source"], "NEW_RETRIEVAL")

    def test_eat_and_owner_references_are_preserved(self):
        self.assertEqual(self.row(57)["routing_strategy"], "NORMAL")
        self.assertEqual(self.row(57)["execution_source"], "OWNER_REFERENCE")
        self.assertEqual(sum(r["execution_source"] == "OWNER_REFERENCE" for r in self.routes), 6)
        for row in self.routes:
            if row["execution_source"] == "OWNER_REFERENCE":
                item = self.approved[row["vocab_id"]]
                self.assertEqual(row["owner_candidate_id"], item["candidate_id"])
                self.assertEqual(row["owner_image_sha256"], item["image_sha256"])
                self.assertEqual(runner.sha(runner.ROOT / row["owner_image_path"]), item["image_sha256"])
                self.assertFalse(row["new_retrieval_needed"])

    def test_special_restrictions(self):
        self.assertEqual(self.row(81)["execution_source"], "INTERNAL_OVERRIDE")
        self.assertEqual(self.row(81)["usage_restriction"], "INTERNAL_ONLY_TEMPORARY")
        self.assertEqual(self.row(83)["execution_source"], "NO_SUITABLE_IMAGE")
        self.assertFalse(self.row(83)["new_retrieval_needed"])

    def test_fix001_and_isolation(self):
        scorer = runner.SiglipImageScorer.score_batch
        self.assertIs(scorer.__globals__["flatten_to_rgb"], runner.flatten_to_rgb)
        self.assertIs(runner.image.normalize_image_to_jpeg.__globals__["flatten_to_rgb"],
                      runner.flatten_to_rgb)
        self.assertEqual(runner.RESULTS.parent, runner.HERE)
        self.assertEqual(runner.ROUTES.parent, runner.HERE)
        self.assertNotEqual(runner.HERE, runner.A004)
        self.assertTrue(all(r["execution_source"] != "A004_REUSE" or
                            r["experimental_search_query"] == self.old[r["vocab_id"]]["query"]
                            for r in self.routes))


if __name__ == "__main__":
    unittest.main()
