"""B-003.1 offline adapter checks; no Qwen, DDG, SigLIP or gTTS calls."""

import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import import_pipeline_adapter as adapter
from excel_vocabulary_importer import payload_hash


ROOT = Path(__file__).resolve().parents[1]
IMPORT = ROOT / "reports/b002_import_demo/fixture_private_import.json"
PNG = next((ROOT / "tests/fixtures/b001/assets").glob("*.png"))


class ImportPipelineAdapterTests(unittest.TestCase):
    def setUp(self):
        self.record = adapter.load_import(IMPORT)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_three_real_imported_rows_and_paths(self):
        manifest = adapter.build_manifest(self.record, self.root)
        self.assertEqual(len(manifest["items"]), 3)
        self.assertEqual(manifest["import_id"], self.record["import_id"])
        self.assertEqual(manifest["pack_id"], self.record["pack_id"])
        self.assertEqual([item["source_row"] for item in manifest["items"]], [2, 3, 4])
        for source, item in zip(self.record["rows"], manifest["items"]):
            for key in ("item_id", "english", "japanese", "vietnamese", "target_sense"):
                self.assertEqual(item[key], source[key])
            self.assertEqual(item["status"], "pending")
            self.assertEqual(item["review_status"], "pending")
            self.assertEqual(item["distribution"]["status"], "unknown")
            self.assertIsNone(item["image"])
            self.assertIsNone(item["audio"])
            self.assertTrue(item["planned_paths"]["image"].startswith("images/" + item["item_id"]))
        self.assertEqual(manifest["items"][2]["target_sense"], "rain weather")
        self.assertEqual(manifest["workspace"], "baseline/imports/" + self.record["import_id"])

    def test_write_is_per_import_and_exclusive(self):
        path, manifest = adapter.write_manifest(IMPORT, self.root)
        self.assertTrue(path.is_file())
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), manifest)
        with self.assertRaises(FileExistsError):
            adapter.write_manifest(IMPORT, self.root)
        second = copy.deepcopy(self.record)
        second["import_id"] = "imp-22222222-2222-4222-8222-222222222222"
        second_path = self.root / "second.json"
        second_path.write_text(json.dumps(second, ensure_ascii=False), encoding="utf-8")
        other, _ = adapter.write_manifest(second_path, self.root)
        self.assertNotEqual(path.parent, other.parent)

    def test_query_candidate_validation_and_rank_never_approve(self):
        manifest = adapter.build_manifest(self.record, self.root)
        item = adapter.claim_item(manifest, self.record["rows"][0]["item_id"])
        adapter.record_query(manifest, item["item_id"], "Apple Fruit")
        self.assertEqual(item["stages"]["query"]["output"], "apple fruit")
        adapter.record_candidates(manifest, item["item_id"], [
            {"image": "https://example.org/apple.png", "url": "https://example.org/page"},
            {"image": "http://localhost/private.png"}])
        candidates = item["stages"]["image_retrieval"]["candidates"]
        self.assertEqual(len(candidates), 1)
        directory = adapter.import_directory(self.root, manifest["import_id"])
        candidate_path = directory / "candidates" / item["item_id"] / "01.png"
        candidate_path.parent.mkdir(parents=True)
        shutil.copyfile(PNG, candidate_path)
        sha = adapter.record_candidate_file(manifest, item["item_id"], candidates[0]["candidate_id"], candidate_path, self.root)
        self.assertEqual(sha, hashlib.sha256(PNG.read_bytes()).hexdigest())
        adapter.record_rank(manifest, item["item_id"], candidates[0]["candidate_id"], 0.75)
        self.assertEqual(candidates[0]["score"], 0.75)
        self.assertEqual(item["status"], "processing")
        self.assertIsNone(item["image"])
        self.assertIsNone(item["stages"]["image_review"]["decision"])
        self.assertEqual(item["review_status"], "pending")
        with self.assertRaises(ValueError):
            adapter.record_candidate_file(manifest, item["item_id"], candidates[0]["candidate_id"], PNG, self.root)

    def test_missing_image_and_other_failures(self):
        manifest = adapter.build_manifest(self.record, self.root)
        first = adapter.claim_item(manifest, self.record["rows"][0]["item_id"])
        adapter.record_failure(manifest, first["item_id"], "image", "NO_SUITABLE_IMAGE", "No suitable candidate after review.")
        self.assertEqual(first["status"], "failed")
        self.assertEqual(first["stages"]["image_review"]["decision"], "NO_SUITABLE_IMAGE")
        self.assertIsNone(first["image"])
        self.assertEqual(first["errors"][0]["stage"], "image")
        second = adapter.claim_item(manifest, self.record["rows"][1]["item_id"])
        adapter.record_failure(manifest, second["item_id"], "query", "MODEL_UNAVAILABLE", "Provider unavailable.", True)
        self.assertEqual(second["errors"][0]["retryable"], True)
        self.assertEqual(manifest["items"][2]["status"], "pending")

    def test_reject_tampered_mapping_and_path_traversal(self):
        bad = copy.deepcopy(self.record)
        bad["rows"][0]["english"] = "changed"
        path = self.root / "tampered.json"
        path.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            adapter.load_import(path)
        bad = copy.deepcopy(self.record)
        bad["import_id"] = "imp-../escape"
        with self.assertRaises(ValueError):
            adapter.build_manifest(bad, self.root)
        bad = copy.deepcopy(self.record)
        bad["rows"][0]["item_id"] = "item-../../escape"
        with self.assertRaises(ValueError):
            adapter.build_manifest(bad, self.root)
        self.assertFalse((self.root / "escape").exists())

    def test_no_benchmark_or_internal_override_reuse(self):
        protected = [ROOT / "data/vocabulary/unified_dataset_v1.json",
                     ROOT / "data/vocabulary/id_registry_v1.json",
                     ROOT / "data/vocabulary/internal_image_overrides_v1.json"]
        before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in protected]
        record = copy.deepcopy(self.record)
        record["rows"][0]["english"] = "because"
        record["normalized_payload_sha256"] = payload_hash(record["rows"])
        manifest = adapter.build_manifest(record, self.root)
        self.assertIsNone(manifest["items"][0]["image"])
        self.assertEqual(manifest["items"][0]["distribution"]["status"], "unknown")
        self.assertEqual([hashlib.sha256(path.read_bytes()).hexdigest() for path in protected], before)


if __name__ == "__main__":
    unittest.main()
