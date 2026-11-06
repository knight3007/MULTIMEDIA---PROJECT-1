"""Offline contract tests for the persisted vocabulary dataset."""

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import imagecollector
from dataset_builder import audio_record, build_dataset, safe_asset, write_dataset
from vocabulary_registry import (initialize_registry, load_registry,
                                 reconcile_entry, validate_registry)
from semantic_decisions import load_decisions, select_effective_query


ROOT = Path(__file__).resolve().parents[1]
FLAGGED = {4, 7, 9, 15, 19, 30, 35, 37, 38, 45, 47, 49, 53, 60, 70,
           78, 81, 87, 88, 90, 91, 98, 100}


class RegistryTests(unittest.TestCase):
    def test_initial_registry_is_persistent_unique_and_matches_corrected_friend(self):
        rows = [tuple(lines) for lines in zip(*[
            (ROOT / "data" / "vocabulary" / f"{lang}.txt").read_text(encoding="utf-8").splitlines()
            for lang in ("en", "jp", "vn")])]
        registry = load_registry(ROOT)
        ordered = validate_registry(rows, registry)
        self.assertEqual(len(ordered), 100)
        self.assertEqual(len(set(ordered)), 100)
        self.assertEqual(ordered[37], "vocab-000038")
        self.assertEqual(rows[37], ("friend", "ともだち", "bạn"))
        entry = registry["entries"][37]
        self.assertEqual(entry["history"][0]["old_triple"][2], "bạn bè")

    def test_explicit_initialization_and_reconciliation_preserve_id(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            rows = [("friend", "ともだち", "bạn bè")]
            registry = initialize_registry(rows, path)
            with self.assertRaises(FileExistsError):
                initialize_registry(rows, path)
            reconcile_entry(registry, "vocab-000001", rows[0],
                            ("friend", "ともだち", "bạn"), "owner approved singular")
            self.assertEqual(validate_registry([("friend", "ともだち", "bạn")], registry),
                             ["vocab-000001"])

    def test_reorder_retains_identity_and_unsafe_mapping_fails(self):
        rows = [("a", "あ", "a"), ("b", "び", "b")]
        with tempfile.TemporaryDirectory() as directory:
            registry = initialize_registry(rows, Path(directory) / "registry.json")
            self.assertEqual(validate_registry(rows[::-1], registry),
                             ["vocab-000002", "vocab-000001"])
            with self.assertRaisesRegex(ValueError, "unmatched"):
                validate_registry([("a", "あ", "changed"), rows[1]], registry)
            registry["entries"][1]["vocab_id"] = "vocab-000001"
            with self.assertRaisesRegex(ValueError, "duplicate"):
                validate_registry(rows, registry)


class DecisionTests(unittest.TestCase):
    def test_only_three_owner_approvals_and_twenty_context_annotations(self):
        registry = load_registry(ROOT)
        decisions = load_decisions(ROOT, registry)
        self.assertEqual(set(decisions["approved"]),
                         {"vocab-000004", "vocab-000009", "vocab-000038"})
        self.assertEqual(len(decisions["context"]), 20)
        self.assertTrue(all(item["review_status"] == "needs_decision"
                            for item in decisions["context"].values()))
        for row, query in ((4, "cooked rice"), (9, "chicken meat")):
            self.assertEqual(select_effective_query(
                f"vocab-{row:06d}", "old model query", decisions),
                (query, "human_approved"))
        self.assertEqual(select_effective_query("vocab-000001", "apple fruit", decisions),
                         ("apple fruit", "model_generated_unreviewed"))

    def test_canonical_image_cli_uses_approved_queries_after_qwen(self):
        queries = ["apple fruit", "banana fruit", "strawberry fruit", "rice grain",
                   "bread food", "egg food", "milk beverage", "water beverage",
                   "chicken animal"]
        with patch("query_generator.prepare_queries", return_value=queries), \
             patch.object(imagecollector, "ensure_directories"), \
             patch.object(imagecollector, "process_word", side_effect=lambda word, query, **kw:
                          imagecollector.ImageResult(True, word, query, "cached")) as process, \
             patch.object(imagecollector, "LazySiglipScorer"), \
             patch("builtins.print"):
            self.assertEqual(imagecollector.main(["--limit", "9"]), 0)
        self.assertEqual(process.call_args_list[3].args[1], "cooked rice")
        self.assertEqual(process.call_args_list[3].kwargs["query_provenance"], "human_approved")
        self.assertEqual(process.call_args_list[8].args[1], "chicken meat")
        self.assertEqual(process.call_args_list[8].kwargs["query_provenance"], "human_approved")

    def test_pending_source_strings_equal_historical_audit(self):
        with (ROOT / "reports/phase_h_vocabulary_alignment.csv").open(
                encoding="utf-8-sig", newline="") as handle:
            audited = {int(row["row_index"]): row for row in csv.DictReader(handle)}
        dataset = build_dataset(ROOT)
        for row_index in FLAGGED - {4, 9, 38}:
            record = dataset["records"][row_index - 1]
            old = audited[row_index]
            self.assertEqual(record["english"], old["english"].strip())
            self.assertEqual(record["japanese"]["reading"], old["japanese"])
            self.assertEqual(record["vietnamese"], old["vietnamese"])

    def test_ledger_rejects_unapproved_extra_semantic_approval(self):
        registry = load_registry(ROOT)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "data/vocabulary/semantic_decisions_v1.json"
            path.parent.mkdir(parents=True)
            raw = json.loads((ROOT / "data/vocabulary/semantic_decisions_v1.json").read_text(
                encoding="utf-8"))
            extra = dict(raw["approved"][0], vocab_id="vocab-000001", source_row_index=1)
            raw["approved"].append(extra)
            path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "approved IDs"):
                load_decisions(root, registry)

    def test_ledger_rejects_changed_owner_query_intent(self):
        registry = load_registry(ROOT)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "data/vocabulary/semantic_decisions_v1.json"
            path.parent.mkdir(parents=True)
            raw = json.loads((ROOT / "data/vocabulary/semantic_decisions_v1.json").read_text(
                encoding="utf-8"))
            raw["approved"][0]["image_search_intent"] = "rice grain"
            path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "owner decision"):
                load_decisions(root, registry)

    def test_approved_sense_without_image_intent_holds_only_that_item(self):
        with patch("query_generator.prepare_queries", return_value=["q"] * 39), \
             patch.object(imagecollector, "ensure_directories"), \
             patch.object(imagecollector, "process_word", side_effect=lambda word, query, **kw:
                          imagecollector.ImageResult(True, word, query, "cached")) as process, \
             patch.object(imagecollector, "LazySiglipScorer"), \
             patch("builtins.print"):
            self.assertEqual(imagecollector.main(["--limit", "39"]), 1)
        self.assertEqual(process.call_count, 38)
        self.assertNotIn("friend", [call.args[0] for call in process.call_args_list])
        self.assertEqual(process.call_args_list[-1].args[0],
                         (ROOT / "data/vocabulary/en.txt").read_text(encoding="utf-8").splitlines()[38])

    def test_conflicting_existing_jpeg_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image_path = root / "rice.jpg"
            meta_path = root / "rice.json"
            image_path.write_bytes(b"\xff\xd8\xffold-image")
            meta_path.write_text(json.dumps({"word": "rice", "provider": "duckduckgo",
                                             "search_query": "rice grain"}), encoding="utf-8")
            before = image_path.read_bytes()
            with patch.object(imagecollector, "IMAGE_DIR", root), \
                 patch.object(imagecollector, "METADATA_DIR", root), \
                 patch.object(imagecollector, "search_images") as search:
                result = imagecollector.process_word("rice", "cooked rice", timeout=1,
                                                     retries=0, retry_delay=0, page_size=1)
            self.assertFalse(result.ok)
            self.assertIn("conflict", result.reason)
            self.assertEqual(image_path.read_bytes(), before)
            search.assert_not_called()

    def test_orphaned_image_metadata_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            meta_path = root / "rice.json"
            meta_path.write_text('{"word":"rice","search_query":"rice grain"}',
                                 encoding="utf-8")
            before = meta_path.read_bytes()
            with patch.object(imagecollector, "IMAGE_DIR", root), \
                 patch.object(imagecollector, "METADATA_DIR", root), \
                 patch.object(imagecollector, "search_images") as search, \
                 patch("builtins.print"):
                result = imagecollector.process_word("rice", "cooked rice", timeout=1,
                                                     retries=0, retry_delay=0, page_size=1)
            self.assertFalse(result.ok)
            self.assertIn("conflict", result.reason)
            self.assertEqual(meta_path.read_bytes(), before)
            search.assert_not_called()


class DatasetTests(unittest.TestCase):
    def test_asset_reference_cannot_escape_project_root(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Unsafe asset path"):
                safe_asset(Path(directory), Path("../outside.jpg"))

    def test_production_dataset_has_correct_review_and_asset_states(self):
        dataset = build_dataset(ROOT)
        records = dataset["records"]
        self.assertEqual(len(records), 100)
        self.assertEqual([r["review_status"] for r in records].count("approved"), 3)
        self.assertEqual([r["review_status"] for r in records].count("needs_decision"), 20)
        self.assertEqual([r["review_status"] for r in records].count("unreviewed"), 77)
        rice, chicken, friend = (records[i - 1] for i in (4, 9, 38))
        self.assertEqual(rice["target_sense"], "cooked rice")
        self.assertEqual(rice["decision_provenance"], "owner_approved")
        self.assertEqual(rice["image"]["effective_search_query"], "cooked rice")
        self.assertEqual(rice["image"]["target_search_sense"], "cooked rice")
        self.assertEqual(rice["image"]["final_search_query"], "rice grain")
        self.assertEqual(rice["image"]["status"], "needs_review")
        self.assertEqual(rice["image"]["semantic_suitability"], "mismatch")
        self.assertIsNone(rice["image"]["url"])
        self.assertEqual(chicken["image"]["semantic_suitability"], "mismatch")
        self.assertEqual(chicken["image"]["final_search_query"], "chicken animal")
        self.assertEqual(friend["vietnamese"], "bạn")
        self.assertEqual(friend["target_sense"], "one friend (singular)")
        self.assertEqual(records[14]["annotation_status"], "context_added_pending_review")
        self.assertEqual(records[14]["japanese"]["reading"], "はな")
        self.assertEqual(records[14]["japanese"]["written_form"], "花")
        self.assertEqual(records[14]["review_status"], "needs_decision")
        self.assertEqual(sum(r["image"]["path"] is not None for r in records), 10)
        self.assertEqual(sum(r["audio"]["path"] is not None for r in records), 0)
        self.assertTrue(all(r["audio"]["status"] == "missing" for r in records))
        self.assertTrue(all(r["audio"]["url"] is None for r in records))
        self.assertEqual({r["source_row_index"] for r in records if r["review_status"] != "unreviewed"}, FLAGGED)

    def test_repeat_build_is_byte_identical_and_does_not_change_registry(self):
        registry_path = ROOT / "data/vocabulary/id_registry_v1.json"
        before = registry_path.read_bytes()
        a = build_dataset(ROOT)
        b = build_dataset(ROOT)
        self.assertEqual(a, b)
        self.assertEqual(before, registry_path.read_bytes())

    def test_corrupt_metadata_is_rejected_before_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for lang in ("en", "jp", "vn"):
                target = root / "data/vocabulary" / f"{lang}.txt"
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / "data/vocabulary" / f"{lang}.txt", target)
            for name in ("id_registry_v1.json", "semantic_decisions_v1.json"):
                shutil.copyfile(ROOT / "data/vocabulary" / name,
                                root / "data/vocabulary" / name)
            img = root / "data/image/en"
            (img / "_metadata").mkdir(parents=True)
            shutil.copyfile(ROOT / "data/image/en/apple.jpg", img / "apple.jpg")
            (img / "_metadata/apple.json").write_text("{bad", encoding="utf-8")
            previous = root / "data/vocabulary/unified_dataset_v1.json"
            previous.write_text("previous manifest", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "metadata"):
                write_dataset(root)
            self.assertEqual(previous.read_text(encoding="utf-8"), "previous manifest")

    def test_valid_production_mp3_is_linked_but_waits_for_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio_dir = root / "data/audio/jp"
            meta_dir = audio_dir / "_metadata"
            meta_dir.mkdir(parents=True)
            output = audio_dir / "りんご.mp3"
            shutil.copyfile(ROOT / "collect data script/fixtures/short-tone.mp3", output)
            from audiocollector import validate_audio
            validation = validate_audio(output)
            self.assertTrue(validation.ok)
            metadata = {"word": "りんご", "reading": "りんご",
                        "audio": "data/audio/jp/りんご.mp3", "source": "google_translate_gtts",
                        "locale": "ja", "voice": {"tld": "com", "slow": False},
                        "format": "mp3", "size": validation.size,
                        "duration_seconds": validation.duration_seconds, "status": "success"}
            (meta_dir / "りんご.json").write_text(json.dumps(metadata, ensure_ascii=False),
                                                   encoding="utf-8")
            linked = audio_record(root, 1, "りんご")
            self.assertEqual(linked["status"], "needs_review")
            self.assertEqual(linked["path"], "data/audio/jp/りんご.mp3")
            self.assertIsNone(linked["url"])
            self.assertEqual(len(linked["cache_identity"]), 64)
