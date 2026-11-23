"""Guard owner decisions and isolated follow-up scope."""
import unittest

import followup


class FollowupTests(unittest.TestCase):
    def setUp(self):
        self.plan = followup.read(followup.PLAN)
        self.items = {i["vocab_id"]: i for i in self.plan["items"]}

    def test_plan_has_100_ids_and_fixed_xor_query(self):
        items = self.plan["items"]
        self.assertEqual(len(items), 100)
        self.assertEqual(len(self.items), 100)
        self.assertEqual(sum(bool(i["fixed"]) for i in items), 67)  # 66 frozen + 066 amendment
        self.assertEqual(sum(bool(i["query"]) for i in items), 33)
        self.assertTrue(all(bool(i["fixed"]) != bool(i["query"]) for i in items))
        self.assertEqual(followup.sha(followup.EXPORT_COPY), self.plan["source_export_sha256"])

    def test_selected_and_reference_assets_are_intact(self):
        for item in self.plan["items"]:
            if item["fixed"]:
                followup.checked_asset(item["fixed"]["path"], item["fixed"]["sha256"])
            if item["a001_reference"]:
                followup.checked_asset(item["a001_reference"]["path"], item["a001_reference"]["sha256"])
        self.assertEqual(self.items["vocab-000081"]["fixed"]["source"], "INTERNAL_ONLY_TEMPORARY")
        self.assertEqual(self.items["vocab-000083"]["fixed"]["source"], "A001_OWNER_PASS")
        self.assertIsNone(self.items["vocab-000036"]["fixed"])
        self.assertIsNone(self.items["vocab-000057"]["fixed"])

    def test_owner_a001_note_amendment_is_applied_and_audited(self):
        item = self.items["vocab-000066"]
        self.assertEqual(item["fixed"]["source"], "A001_OWNER_NOTE")
        self.assertIsNone(item["query"])
        self.assertEqual(item["superseded_query"], "software application screen icon")
        audit = [a for a in self.plan["amendments"] if a["vocab_id"] == "vocab-000066"]
        self.assertEqual(len(audit), 1)
        self.assertIsNone(audit[0]["before"]["fixed"])

    def test_every_owner_a001_note_is_fixed_to_a001(self):
        for item in self.plan["items"]:
            note = item["owner_note"].replace(" ", "").upper()
            if "A001" in note and not item["prior_selected_candidate_id"]:
                self.assertIsNotNone(item["fixed"], item["vocab_id"])
                self.assertIn(item["fixed"]["source"], {"A001_OWNER_PASS", "A001_OWNER_NOTE"}, item["vocab_id"])

    def test_hard_to_icon_notes_use_scene_queries(self):
        for number in (42, 43, 47, 48):
            item = self.items[f"vocab-{number:06d}"]
            self.assertEqual(item["strategy"], "SCENE")
            self.assertFalse(item["query"].endswith(" icon"))

    def test_every_downloaded_candidate_hash_matches_including_previous_attempts(self):
        results = followup.read(followup.RESULTS)
        seen = set()
        for vid, result in results.items():
            for attempt in [result] + result.get("previous_attempts", []):
                for c in attempt["candidates"]:
                    if c["download_status"] == "SUCCESS":
                        self.assertNotIn(c["candidate_id"], seen)
                        seen.add(c["candidate_id"])
                        followup.checked_asset(c["raw_path"], c["raw_sha256"])
                        followup.checked_asset(c["jpeg_path"], c["jpeg_sha256"])

    def test_query_repairs_are_audited_and_searched_items_are_ranked(self):
        results = followup.read(followup.RESULTS)
        repairs = {a["vocab_id"]: a for a in self.plan["amendments"] if a["action"] == "QUERY_REPAIR"}
        self.assertEqual(set(repairs), {"vocab-000033", "vocab-000060", "vocab-000079", "vocab-000080"})
        for vid, audit in repairs.items():
            self.assertEqual(self.items[vid]["superseded_query"], audit["before"]["query"])
            self.assertEqual(results[vid]["query"], self.items[vid]["query"])
            self.assertEqual(len(results[vid]["previous_attempts"]), 1)
        for item in self.plan["items"]:
            if item["query"]:
                self.assertEqual(results[item["vocab_id"]]["status"], "RANKED", item["vocab_id"])

    def test_eat_prior_owner_reference_is_offered(self):
        choices = followup.prior_choices("vocab-000057")
        self.assertEqual(choices[0][0], "PRIOR_OWNER_REFERENCE")


if __name__ == "__main__":
    unittest.main()
