"""Offline contracts for the isolated, query-only Qwen benchmark."""

import json
import tempfile
import unittest
from pathlib import Path

from image_query_benchmark import (
    BENCHMARK_IDS, SCHEMA_VERSION, freeze_inputs, load_inputs,
    parse_visual_output, read_checkpoint, run_experiment,
    validate_experiment_document, write_checkpoint,
)


ROOT = Path(__file__).resolve().parents[1]


class BenchmarkContractTests(unittest.TestCase):
    def test_canonical_rows_preserve_raw_model_and_effective_query(self):
        rows = load_inputs(ROOT)
        self.assertEqual([row["source_row_index"] for row in rows], BENCHMARK_IDS)
        self.assertEqual(len(rows), 25)
        rice = rows[0]
        self.assertEqual(rice["historical"]["raw_model_query"], "rice grain")
        self.assertEqual(rice["historical"]["effective_search_query"], "cooked rice")
        self.assertEqual(rice["historical"]["query_provenance"], "human_approved")
        self.assertIsNone(rice["historical"]["raw_decoded_text"])

    def test_context_does_not_approve_ambiguous_meaning(self):
        rows = load_inputs(ROOT)
        rain = next(row for row in rows if row["source_row_index"] == 19)
        self.assertEqual(rain["semantic_review_status"], "needs_decision")
        self.assertIsNone(rain["target_sense"])
        self.assertIn("雨", rain["usage_note"])

    def test_valid_json_requires_controlled_type_and_all_fields(self):
        raw = json.dumps({
            "visual_type": "action", "search_query": "person writing a letter",
            "visual_description": "A person writes words on paper.",
            "negative_constraints": ["drawing", "typed text"],
            "reason": "Writing is visible through the pen and written words.",
        })
        result = parse_visual_output(raw, ended=True)
        self.assertEqual(result["validation_status"], "valid")
        self.assertEqual(result["parsed"]["visual_type"], "action")
        for altered in (raw[:-1], raw.replace('"action"', '"unknown_type"')):
            self.assertEqual(parse_visual_output(altered, ended=True)["validation_status"], "invalid")

    def test_token_limit_preserves_raw_and_reports_error(self):
        raw = '{"visual_type":"action"'
        result = parse_visual_output(raw, ended=False)
        self.assertEqual(result["raw_decoded_text"], raw)
        self.assertEqual(result["validation_status"], "invalid")
        self.assertIn("token limit", result["error"])
        self.assertIsNone(result["parsed"])

    def test_missing_approved_intent_is_not_invented(self):
        from image_query_benchmark import resolve_effective_query
        with self.assertRaisesRegex(ValueError, "no image search intent"):
            resolve_effective_query("model query", {
                "review_status": "approved", "target_sense": "one friend",
                "image_search_intent": None,
            })

    def test_checkpoint_rejects_changed_input_hash_and_keeps_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "input.txt"
            source.write_text("first", encoding="utf-8")
            hashes = freeze_inputs(base, [source])
            run = base / "run"
            run.mkdir()
            document = {"schema_version": SCHEMA_VERSION, "input_hashes": hashes,
                        "records": [{"source_row_index": 4, "raw_decoded_text": "raw"}]}
            write_checkpoint(run / "query_experiment.json", document)
            self.assertEqual(read_checkpoint(run / "query_experiment.json", base)["records"], document["records"])
            source.write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash"):
                read_checkpoint(run / "query_experiment.json", base)

    def test_mocked_run_persists_all_rows_and_resumes_without_regeneration(self):
        calls = []

        class FakeBackend:
            metadata = {"model": "mock", "revision": "fixture", "device": "cpu"}

            def generate(self, variant, row):
                calls.append((variant, row["source_row_index"]))
                if variant == "a":
                    return {"raw_decoded_text": "person swimming", "raw_attempts": [],
                            "parsed_query": "person swimming", "validation_status": "valid",
                            "error": None, "ended_with_eos": True, "duration_seconds": 0.01}
                return {**parse_visual_output(json.dumps({
                    "visual_type": "action", "search_query": "person swimming in pool",
                    "visual_description": "A person swims in a pool.",
                    "negative_constraints": [], "reason": "The action is visible.",
                }), True), "ended_with_eos": True, "duration_seconds": 0.02}

            def close(self):
                pass

        class UnloadedBackend(FakeBackend):
            metadata = {"model": "mock", "revision": "fixture", "device": None}

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            run = run_experiment(ROOT, "offline-fixture", output_base=base,
                                 backend=FakeBackend(), protected_paths=[])
            self.assertEqual(len(run["records"]), 25)
            self.assertEqual(len(calls), 50)
            self.assertEqual(len(list((base / "offline-fixture" / "raw_generation" / "variant_a").glob("*.json"))), 25)
            review = (base / "offline-fixture" / "owner_review.csv").read_text(encoding="utf-8")
            self.assertEqual(len(review.splitlines()), 76)
            self.assertIn("reviewer_id,", review)
            run_experiment(ROOT, "offline-fixture", resume=True, output_base=base,
                           backend=UnloadedBackend(), protected_paths=[])
            self.assertEqual(len(calls), 50)
            retained = json.loads((base / "offline-fixture" / "experiment_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(retained["model_runtime"]["device"], "cpu")
            saved = json.loads((base / "offline-fixture" / "query_experiment.json").read_text(encoding="utf-8"))
            validate_experiment_document(saved)
            saved["records"].pop()
            with self.assertRaisesRegex(ValueError, "25 canonical"):
                validate_experiment_document(saved)
            prompt_path = base / "offline-fixture" / "prompts.json"
            prompts = json.loads(prompt_path.read_text(encoding="utf-8"))
            prompts["variant_b"]["system_prompt"] = "changed prompt"
            prompt_path.write_text(json.dumps(prompts), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "prompt"):
                run_experiment(ROOT, "offline-fixture", resume=True, output_base=base,
                               backend=FakeBackend(), protected_paths=[])

    def test_malformed_model_json_is_saved_without_fallback(self):
        class FakeBackend:
            metadata = {"model": "mock", "revision": "fixture", "device": "cpu"}

            def generate(self, variant, row):
                if variant == "a":
                    return {"raw_decoded_text": "rice grain", "raw_attempts": [],
                            "parsed_query": "rice grain", "validation_status": "valid",
                            "error": None, "ended_with_eos": True, "duration_seconds": 0.01}
                return {**parse_visual_output('{"visual_type":', True),
                        "ended_with_eos": True, "duration_seconds": 0.01}

            def close(self):
                pass

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            rows = run_experiment(ROOT, "malformed-fixture", output_base=base,
                                  backend=FakeBackend(), protected_paths=[])["records"]
            first = rows[0]
            self.assertEqual(first["variant_b"]["raw_decoded_text"], '{"visual_type":')
            self.assertIsNone(first["variant_b"]["effective_search_query"])
            self.assertEqual(first["variant_b"]["validation_status"], "invalid")
            manifest = json.loads((base / "malformed-fixture" / "experiment_manifest.json").read_text())
            self.assertEqual(len(manifest["failure_summaries"]["b"]), 25)


if __name__ == "__main__":
    unittest.main()
