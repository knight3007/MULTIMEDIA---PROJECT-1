import json
import copy
import hashlib
import tempfile
import unittest
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import excel_multimedia_runner as runner
from content_pack_builder import validate_pack


class DualAudioTests(unittest.TestCase):
    def test_new_proposal_uses_only_scored_valid_candidate_in_its_item_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            item_id = "item-test"
            candidate = root / "image_candidates" / item_id / "01.jpg"
            candidate.parent.mkdir(parents=True)
            candidate.write_bytes(b"jpeg candidate")
            record = {"status": "PROPOSED", "proposed_candidate_id": f"{item_id}-01",
                      "candidates": [{"candidate_id": f"{item_id}-01", "status": "DOWNLOADED",
                                      "jpeg_path": str(candidate), "jpeg_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
                                      "score": 4.5, "rejection": None}]}
            self.assertEqual(runner.selected_image_candidate(record, root, item_id)["jpeg_path"], str(candidate))
            record["candidates"][0]["rejection"] = "near-uniform image"
            self.assertIsNone(runner.selected_image_candidate(record, root, item_id))
            record["candidates"][0]["rejection"] = None
            record["candidates"][0]["jpeg_path"] = str(root / "outside.jpg")
            with self.assertRaises(ValueError):
                runner.selected_image_candidate(record, root, item_id)

    def test_multiword_photo_fallback_after_frozen_policy_rejects_phrase(self):
        from query_generator import QueryGenerationError
        with patch.object(runner.policy, "classify_words", side_effect=QueryGenerationError(
                "concrete query must name the word and stay a photo query")):
            typed, fallback = runner.classify_import_word("traffic light", object())
        self.assertEqual((typed.route, typed.query, fallback),
                         ("PHOTO", "traffic light photo", "MULTIWORD_PHOTO_FALLBACK"))

    def test_english_and_japanese_are_independent(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            calls = []

            def synthesize(text, path, *, timeout, locale):
                calls.append((text, locale))
                path.write_bytes(b"audio")

            def validate(path):
                return type("Validation", (), {"ok": True, "size": path.stat().st_size,
                                                 "duration_seconds": 0.8, "reason": None})()

            with patch.object(runner, "synthesize_gtts_mp3", side_effect=synthesize), patch.object(runner, "validate_audio", side_effect=validate):
                en = runner.make_audio("item-test", "en", "apple", root, {})
                ja = runner.make_audio("item-test", "ja", "りんご", root, {})
                again = runner.make_audio("item-test", "en", "apple", root, {})
            self.assertEqual(calls, [("apple", "en"), ("りんご", "ja")])
            self.assertEqual((en["status"], ja["status"], again["status"]), ("GENERATED", "GENERATED", "GENERATED"))
            self.assertTrue(again["resume_reused"])
            self.assertNotEqual(en["path"], ja["path"])

    def test_legacy_pack_still_validates(self):
        pack = json.loads(Path("tests/fixtures/b001/content_pack_states.json").read_text(encoding="utf-8"))
        self.assertTrue(validate_pack(pack, Path("tests/fixtures/b001"))["valid"])

    def test_dual_mode_mapping_rejects_wrong_source_text(self):
        pack = copy.deepcopy(json.loads(Path("tests/fixtures/b001/content_pack_states.json").read_text(encoding="utf-8")))
        item = pack["items"][0]
        item["audio_english"] = item["audio"]
        item["audio_japanese"] = item["audio"]
        item["extensions"] = {"dual_audio_v1": {
            "en": {"locale": "en", "text": item["english"], "sha256": item["audio"]["sha256"]},
            "ja": {"locale": "ja", "text": item["japanese"], "sha256": item["audio"]["sha256"]}}}
        pack["extensions"] = {"language_modes": {
            "ENGLISH_TO_VIETNAMESE": {"source": "english", "translation": "vietnamese", "audio": "audio_english"},
            "JAPANESE_TO_VIETNAMESE": {"source": "japanese", "translation": "vietnamese", "audio": "audio_japanese"}}}
        self.assertTrue(validate_pack(pack, Path("tests/fixtures/b001"))["valid"])
        item["extensions"]["dual_audio_v1"]["en"]["text"] = item["japanese"]
        self.assertFalse(validate_pack(pack, Path("tests/fixtures/b001"))["valid"])

    def test_historical_no_suitable_image_is_preserved(self):
        self.assertIn("sometimes␟ときどき␟thỉnh thoảng", runner.historical_no_suitable())


if __name__ == "__main__":
    unittest.main()
