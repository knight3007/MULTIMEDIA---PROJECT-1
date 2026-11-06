"""Offline contract tests for generic stable-ID image staging."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import imagecollector as image
from stage_vocabulary_images import (choose_targets, prepare_staging_queries,
                                     repair_failed_staging_queries, stage_images)


def fixture_dataset():
    rows = []
    for number, word in enumerate(("cat", "dog", "friend", "tree"), 11):
        rows.append({"vocab_id": f"vocab-{number:06d}", "source_row_index": number,
                     "english": word, "japanese": {"reading": f"jp{number}"},
                     "vietnamese": f"vn{number}", "target_sense": None,
                     "review_status": "needs_decision" if number == 12 else "unreviewed",
                     "image": {"path": "data/image/en/tree.jpg" if number == 14 else None}})
    return {"records": rows}


class GenericImageStagingTests(unittest.TestCase):
    def test_invalid_id_and_run_are_rejected_before_query_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("stage_vocabulary_images.build_dataset", return_value=fixture_dataset()), \
                 patch("stage_vocabulary_images.load_decisions", return_value={"approved": {}}), \
                 patch("stage_vocabulary_images.load_registry", return_value={}), \
                 patch("stage_vocabulary_images.prepare_staging_queries") as generate:
                with self.assertRaises(ValueError):
                    stage_images(root, ["vocab-999999"])
                with self.assertRaises(ValueError):
                    stage_images(root, ["vocab-000011"], run_id="../unsafe")
            generate.assert_not_called()
            self.assertFalse((root / "baseline").exists())

    def test_targets_use_approved_query_and_block_missing_intent(self):
        data = fixture_dataset()
        data["records"][2]["review_status"] = "approved"
        decisions = {"approved": {"vocab-000011": {"image_search_intent": "pet cat"},
                                  "vocab-000013": {"image_search_intent": None}}}
        chosen = choose_targets(data, ["vocab-000011", "vocab-000012", "vocab-000013"],
                                ["cat animal", "dog animal", "friend person", "tree plant"],
                                decisions)
        self.assertEqual([(x["vocab_id"], x["query"], x["query_provenance"], x["status"])
                          for x in chosen],
                         [("vocab-000011", "pet cat", "human_approved", "ready"),
                          ("vocab-000012", "dog animal", "model_generated_unreviewed", "ready"),
                          ("vocab-000013", None, None, "blocked_semantic_review")])

    def test_rejects_invalid_duplicate_or_production_ids(self):
        data = fixture_dataset(); queries = ["cat animal", "dog animal", "friend person", "tree plant"]
        for ids in (["vocab-999999"], ["vocab-000011", "vocab-000011"],
                    ["vocab-000014"], ["../unsafe"]):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                choose_targets(data, ids, queries, {"approved": {}})

    def test_failed_qwen_word_does_not_block_later_word_or_repeat_on_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); prefix = root / "prefix.json"
            prefix.write_text(json.dumps({"model": "Qwen/Qwen3-1.7B", "signature": "fixture",
                                          "records": [{"word": "cat", "query": "cat animal"}]}),
                              encoding="utf-8")
            sparse = root / "sparse.json"

            class FakeGenerator:
                calls = []
                def __init__(self, *args, **kwargs): pass
                def generate_batch(self, words):
                    self.calls.append(tuple(words))
                    if "go" in words:
                        from query_generator import QueryGenerationError
                        raise QueryGenerationError("go verb rejected")
                    return [word + " action" for word in words]
                def generate(self, word):
                    return self.generate_batch([word])[0]
                def close(self): pass

            with patch("stage_vocabulary_images.prepare_queries", return_value=["cat animal"]), \
                 patch("stage_vocabulary_images.QwenQueryGenerator", FakeGenerator):
                queries, errors = prepare_staging_queries(["cat", "go", "read"], prefix, sparse)
                self.assertEqual(queries, ["cat animal", None, "read action"])
                self.assertIn("go verb rejected", errors[1])
                first_calls = list(FakeGenerator.calls)
                again, _ = prepare_staging_queries(["cat", "go", "read"], prefix, sparse)
            self.assertEqual(again, queries)
            self.assertEqual(first_calls, FakeGenerator.calls)

    def test_missing_model_query_is_a_recorded_block_not_an_approval(self):
        chosen = choose_targets(fixture_dataset(), ["vocab-000011", "vocab-000012"],
                                [None, "dog animal", "friend person", "tree plant"],
                                {"approved": {}}, {0: "Qwen rejected cat"})
        self.assertEqual(chosen[0]["status"], "blocked_query_generation")
        self.assertEqual(chosen[0]["failure"], "Qwen rejected cat")
        self.assertEqual(chosen[1]["status"], "ready")

    def test_qwen_correction_replaces_only_failed_staging_queries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); prefix = root / "prefix.json"; sparse = root / "sparse.json"
            prefix.write_text(json.dumps({"model": "Qwen/Qwen3-1.7B", "signature": "fixture",
                                          "records": [{"word": "cat", "query": "cat animal"}]}),
                              encoding="utf-8")

            class FakeGenerator:
                def __init__(self, *args, **kwargs): pass
                def generate_batch(self, words):
                    from query_generator import QueryGenerationError
                    if "go" in words: raise QueryGenerationError("go verb rejected")
                    return ["read action"]
                def generate(self, word): return self.generate_batch([word])[0]
                def _load(self): pass
                def _generate_raw(self, words, *, correction):
                    self_test.assertEqual(words, ["go"])
                    self_test.assertIn("person", correction)
                    return [("person going", True)]
                def close(self): pass

            self_test = self
            with patch("stage_vocabulary_images.prepare_queries", return_value=["cat animal"]), \
                 patch("stage_vocabulary_images.QwenQueryGenerator", FakeGenerator):
                prepare_staging_queries(["cat", "go", "read"], prefix, sparse)
                repaired = repair_failed_staging_queries(["cat", "go", "read"], prefix, sparse)
                queries, errors = prepare_staging_queries(["cat", "go", "read"], prefix, sparse)
            self.assertEqual(repaired, [2])
            self.assertEqual(queries, ["cat animal", "person going", "read action"])
            self.assertEqual(errors, {})
            saved = json.loads(sparse.read_text(encoding="utf-8"))
            self.assertEqual(saved["records"][0]["prior_failure"], "go verb rejected")
            self.assertEqual(saved["records"][0]["generation_method"], "qwen_corrected_verb_prompt")

    def test_resume_rejects_changed_query_without_touching_prior_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / "baseline/media-staging/images/old-blocked"
            run.mkdir(parents=True)
            manifest = {"schema_version": 1, "run_id": "old-blocked",
                        "purpose": "generic_vocabulary_image_staging",
                        "vocab_ids": ["vocab-000011"],
                        "targets": [{"vocab_id": "vocab-000011", "query": None,
                                     "query_provenance": None, "status": "blocked_query_generation",
                                     "failure": "old Qwen rejection"}]}
            path = run / "run_manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            before = path.read_bytes()
            with patch("stage_vocabulary_images.build_dataset", return_value=fixture_dataset()), \
                 patch("stage_vocabulary_images.load_decisions", return_value={"approved": {}}), \
                 patch("stage_vocabulary_images.load_registry", return_value={}), \
                 patch("stage_vocabulary_images.prepare_staging_queries",
                       return_value=(["cat animal", "dog animal", "friend person", "tree plant"], {})), \
                 patch.object(image, "process_word") as process:
                with self.assertRaisesRegex(ValueError, "changed"):
                    stage_images(root, ["vocab-000011"], run_id="old-blocked", resume=True)
            process.assert_not_called()
            self.assertEqual(path.read_bytes(), before)

    def test_stages_and_resumes_without_download_or_production_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            production = root / "data/image/en"; production.mkdir(parents=True)
            (production / "tree.jpg").write_bytes(b"preserve")
            before = hashlib.sha256((production / "tree.jpg").read_bytes()).hexdigest()
            calls = []

            def fake_process(word, query_text, **kwargs):
                calls.append((word, query_text, kwargs["query_provenance"], kwargs["search_backend"]))
                Image.new("RGB", (16, 12), "blue").save(image.IMAGE_DIR / f"{word}.jpg", format="JPEG")
                image.save_metadata(word, query_text,
                                    {"provider": image.IMAGE_PROVIDER,
                                     "image_url": f"https://example.test/{word}.jpg",
                                     "source_page_url": f"https://example.test/{word}",
                                     "search_client": "ddgs", "search_backend": "bing"},
                                    {"method": "siglip2", "model": image.DEFAULT_SIGLIP_MODEL,
                                     "score": 0.5}, kwargs["query_provenance"])
                return image.ImageResult(True, word, query_text, "downloaded",
                                         selected_image=f"https://example.test/{word}.jpg",
                                         search_result_count=3, valid_candidate_count=3,
                                         candidate_count=2, search_backend="bing")

            with patch("stage_vocabulary_images.build_dataset", return_value=fixture_dataset()), \
                 patch("stage_vocabulary_images.load_decisions", return_value={"approved": {}}), \
                 patch("stage_vocabulary_images.load_registry", return_value={}), \
                 patch("stage_vocabulary_images.prepare_staging_queries",
                       return_value=(["cat animal", "dog animal", "friend person", "tree plant"], {})), \
                 patch.object(image, "process_word", side_effect=fake_process):
                path, first = stage_images(root, ["vocab-000011", "vocab-000012"],
                                           run_id="generic-1", rate_limit_delay=0)
                first_hashes = [x["sha256"] for x in first["targets"]]
                _, second = stage_images(root, ["vocab-000011", "vocab-000012"],
                                         run_id="generic-1", resume=True, rate_limit_delay=0)
                manifest_before_conflict = path.read_bytes()
                Image.new("RGB", (16, 12), "red").save(
                    path.parent / "cat.jpg", format="JPEG")
                with self.assertRaisesRegex(ValueError, "changed|conflict"):
                    stage_images(root, ["vocab-000011", "vocab-000012"],
                                 run_id="generic-1", resume=True, rate_limit_delay=0)
                self.assertEqual(path.read_bytes(), manifest_before_conflict)
            self.assertEqual(calls, [("cat", "cat animal", "model_generated_unreviewed", "bing"),
                                     ("dog", "dog animal", "model_generated_unreviewed", "bing")])
            self.assertEqual([x["sha256"] for x in second["targets"]], first_hashes)
            self.assertTrue(all(x["resume_cache_status"] == "cache_hit" for x in second["targets"]))
            self.assertEqual(before, hashlib.sha256((production / "tree.jpg").read_bytes()).hexdigest())
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), second)
            self.assertFalse((root / "data/image/en/cat.jpg").exists())


if __name__ == "__main__":
    unittest.main()
