"""Offline tests for isolated owner-approved image staging."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

import imagecollector as image
from collector_common import CollectionError
from stage_image_replacements import main, stage_replacements


def approved_records():
    return {"records": [
        {"vocab_id": "vocab-000004", "english": "rice",
         "japanese": {"reading": "ごはん"}, "vietnamese": "cơm",
         "target_sense": "cooked rice", "review_status": "approved",
         "image": {"effective_search_query": "cooked rice", "status": "needs_review"}},
        {"vocab_id": "vocab-000009", "english": "chicken",
         "japanese": {"reading": "とりにく"}, "vietnamese": "thịt gà",
         "target_sense": "chicken meat", "review_status": "approved",
         "image": {"effective_search_query": "chicken meat", "status": "needs_review"}},
    ]}


class StagingTests(unittest.TestCase):
    def test_chicken_only_selection_does_not_query_rice(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calls = []

            def fake_process(word, query_text, **kwargs):
                calls.append((word, query_text))
                Image.new("RGB", (16, 12), "blue").save(image.IMAGE_DIR / "chicken.jpg")
                image.save_metadata(word, query_text,
                                    {"provider": "duckduckgo",
                                     "image_url": "https://example.test/chicken.jpg"},
                                    {"method": "siglip2", "model": "test", "score": 0.4},
                                    "human_approved")
                return image.ImageResult(True, word, query_text, "downloaded",
                                         selected_image="https://example.test/chicken.jpg")

            with patch("stage_image_replacements.build_dataset", return_value=approved_records()), \
                 patch.object(image, "process_word", side_effect=fake_process):
                first, result = stage_replacements(root, run_id="only-chicken",
                                                    vocab_id="vocab-000009",
                                                    rate_limit_delay=0)
                second, _ = stage_replacements(root, run_id="second-chicken",
                                               vocab_id="vocab-000009",
                                               rate_limit_delay=0)
            self.assertEqual(calls, [("chicken", "chicken meat")] * 2)
            self.assertEqual([entry["vocab_id"] for entry in result["targets"]], ["vocab-000009"])
            self.assertNotEqual(first, second)
            self.assertFalse((root / "baseline/media-staging/images/only-chicken/rice.jpg").exists())
            self.assertFalse((root / "data/image/en").exists())

    def test_unknown_target_is_rejected_before_staging(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("stage_image_replacements.build_dataset", return_value=approved_records()):
                with self.assertRaisesRegex(ValueError, "Unsupported"):
                    stage_replacements(root, vocab_id="vocab-999999")
            self.assertFalse((root / "baseline").exists())

    def test_cli_forwards_selected_vocab_id(self):
        with patch("stage_image_replacements.stage_replacements", return_value=(Path("manifest.json"),
                  {"targets": [{"vocab_id": "vocab-000009", "english": "chicken",
                               "status": "staged", "failure": None}]})) as stage:
            self.assertEqual(main(["--vocab-id", "vocab-000009"]), 0)
        self.assertEqual(stage.call_args.kwargs["vocab_id"], "vocab-000009")

    def test_curated_chicken_uses_existing_download_and_scoring_without_search(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = "https://upload.wikimedia.org/example/chicken.jpg"
            page = "https://commons.wikimedia.org/wiki/File:Chicken.jpg"

            def fake_download(_url, destination, **_kwargs):
                Image.new("RGB", (80, 50), "white").save(destination, format="JPEG")

            with patch("stage_image_replacements.build_dataset", return_value=approved_records()), \
                 patch.object(image, "search_images", side_effect=AssertionError("DDGS called")), \
                 patch.object(image, "download_candidate_image", side_effect=fake_download), \
                 patch.object(image.LazySiglipScorer, "score_batch",
                              return_value=[SimpleNamespace(score=0.7)]):
                path, result = stage_replacements(
                    root, run_id="curated-chicken", vocab_id="vocab-000009",
                    curated_image_url=source, curated_source_page_url=page,
                    timeout=2, retries=0, retry_delay=0, rate_limit_delay=0)
            entry = result["targets"][0]
            metadata = json.loads((path.parent / "_metadata/chicken.json").read_text(encoding="utf-8"))
            self.assertEqual(entry["status"], "staged")
            self.assertEqual(entry["search_client"], "curated_direct")
            self.assertEqual(entry["selected_result"]["source_page_url"], page)
            self.assertEqual(metadata["image_url"], source)
            self.assertEqual(metadata["search_client"], "curated_direct")
            self.assertEqual(metadata["image_selection"]["method"], "siglip2")
            self.assertEqual(entry["approval_status"], "pending_human_review")
            self.assertFalse((root / "data/image/en").exists())

    def test_curated_source_requires_chicken_and_both_urls(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                stage_replacements(root, vocab_id="vocab-000009",
                                   curated_image_url="https://example.test/chicken.jpg")
            with self.assertRaises(ValueError):
                stage_replacements(root, vocab_id="vocab-000004",
                                   curated_image_url="https://example.test/chicken.jpg",
                                   curated_source_page_url="https://example.test/file")
            self.assertFalse((root / "baseline").exists())

    def test_staging_isolates_outputs_and_records_valid_selected_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            production = root / "data/image/en"
            (production / "_metadata").mkdir(parents=True)
            (production / "rice.jpg").write_bytes(b"old rice")
            (production / "_metadata/rice.json").write_bytes(b"old metadata")
            dataset = root / "data/vocabulary/unified_dataset_v1.json"
            dataset.parent.mkdir(parents=True)
            dataset.write_bytes(b"old dataset")
            before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                      (production / "rice.jpg", production / "_metadata/rice.json", dataset)}
            old_dirs = (image.IMAGE_DIR, image.METADATA_DIR, image.CANDIDATE_CACHE_DIR)

            def fake_process(word, query_text, **kwargs):
                self.assertEqual(kwargs["query_provenance"], "human_approved")
                self.assertEqual(query_text, {"rice": "cooked rice", "chicken": "chicken meat"}[word])
                target = image.IMAGE_DIR / f"{word}.jpg"
                Image.new("RGB", (16, 12), "red").save(target, format="JPEG")
                image.save_metadata(word, query_text, {"provider": "duckduckgo",
                                    "image_url": f"https://example.test/{word}.jpg"},
                                    {"method": "siglip2", "model": "test-model", "score": 0.5},
                                    "human_approved")
                return image.ImageResult(True, word, query_text, "downloaded",
                                         selected_image=f"https://example.test/{word}.jpg",
                                         siglip_score=0.5, search_result_count=3,
                                         valid_candidate_count=3, candidate_count=2)

            with patch("stage_image_replacements.build_dataset", return_value=approved_records()), \
                 patch.object(image, "process_word", side_effect=fake_process):
                path, result = stage_replacements(root, run_id="run-1", timeout=2,
                                                  retries=0, retry_delay=0,
                                                  page_size=3, rate_limit_delay=0,
                                                  siglip_device="cpu", siglip_dtype="float32")
            self.assertEqual((image.IMAGE_DIR, image.METADATA_DIR,
                              image.CANDIDATE_CACHE_DIR), old_dirs)
            self.assertEqual(len(result["targets"]), 2)
            self.assertTrue(all(item["validation_status"] == "valid_jpeg_and_metadata"
                                for item in result["targets"]))
            self.assertTrue(all(item["approval_status"] == "pending_human_review"
                                for item in result["targets"]))
            self.assertEqual(result["targets"][0]["dimensions"], [16, 12])
            self.assertEqual(result["targets"][0]["siglip_selection"]["score"], 0.5)
            self.assertTrue(path.is_file())
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), result)
            self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in before})

    def test_ddg_timeout_is_recorded_without_candidate_or_production_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("stage_image_replacements.build_dataset", return_value=approved_records()), \
                 patch.object(image, "search_images", side_effect=CollectionError("DDG timeout")):
                path, result = stage_replacements(root, run_id="run-timeout", timeout=1,
                                                  retries=0, retry_delay=0,
                                                  page_size=2, rate_limit_delay=0)
            self.assertTrue(path.is_file())
            self.assertEqual([item["status"] for item in result["targets"]], ["failed", "failed"])
            self.assertTrue(all("DDG timeout" in item["failure"] for item in result["targets"]))
            self.assertTrue(all(item["staged_image_path"] is None for item in result["targets"]))
            self.assertFalse((root / "data/image/en").exists())

    def test_existing_or_unsafe_run_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("stage_image_replacements.build_dataset", return_value=approved_records()):
                with self.assertRaises(ValueError):
                    stage_replacements(root, run_id="../unsafe")
                with self.assertRaises(ValueError):
                    stage_replacements(root, run_id="nan", retry_delay=float("nan"))
                self.assertFalse((root / "baseline/media-staging").exists())
                base = root / "baseline/media-staging/images/existing"
                base.mkdir(parents=True)
                with self.assertRaises(FileExistsError):
                    stage_replacements(root, run_id="existing")

    def test_invalid_staged_metadata_remains_unapproved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def fake_process(word, query_text, **kwargs):
                Image.new("RGB", (8, 8), "blue").save(image.IMAGE_DIR / f"{word}.jpg")
                (image.METADATA_DIR / f"{word}.json").write_text("[]", encoding="utf-8")
                return image.ImageResult(True, word, query_text, "downloaded",
                                         selected_image="https://example.test/candidate.jpg")

            with patch("stage_image_replacements.build_dataset", return_value=approved_records()), \
                 patch.object(image, "process_word", side_effect=fake_process):
                path, data = stage_replacements(root, run_id="bad-metadata", timeout=1,
                                                retries=0, retry_delay=0, page_size=1,
                                                rate_limit_delay=0)
            self.assertTrue(path.is_file())
            self.assertTrue(all(item["status"] == "failed" for item in data["targets"]))
            self.assertTrue(all(item["validation_status"] == "invalid" for item in data["targets"]))
            self.assertTrue(all(item["approval_status"] == "pending_human_review"
                                for item in data["targets"]))
