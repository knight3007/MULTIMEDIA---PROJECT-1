"""Offline contracts for the isolated Phase C0 retrieval runner."""

import csv
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import image_retrieval_benchmark as benchmark


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports/image_pipeline_benchmark/20261106-image-query-v1"


def jpeg(colour):
    output = io.BytesIO()
    Image.new("RGB", (32, 32), colour).save(output, format="JPEG")
    return output.getvalue()


def row():
    return {
        "vocab_id": "vocab-000004", "source_row_index": 4, "english": "rice",
        "japanese": {"display": "ごはん"}, "vietnamese": "cơm",
        "semantic_review_status": "approved", "target_sense": "cooked rice",
        "image_search_intent": "cooked rice",
        "historical": {"raw_decoded_text": None, "raw_model_query": "rice grain",
                       "effective_search_query": "cooked rice", "query_provenance": "human_approved"},
        "variant_a": {"raw_decoded_text": "rice grain", "parsed_query": "rice grain",
                      "effective_search_query": "cooked rice", "query_provenance": "human_approved",
                      "validation_status": "valid"},
        "variant_b": {"raw_decoded_text": '{"search_query":"cooked rice"}',
                      "parsed_query": "cooked rice", "effective_search_query": "cooked rice",
                      "query_provenance": "human_approved", "validation_status": "valid",
                      "parsed": {"visual_type": "food", "search_query": "cooked rice",
                                 "visual_description": "A bowl of cooked rice",
                                 "negative_constraints": ["uncooked rice"], "reason": "Approved sense"}},
    }


class PhaseC0Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run_dir = Path(self.temp.name)
        self.resolver = lambda host, port: [(None, None, None, None, ("93.184.215.14", port))]
        for name in ("getaddrinfo", "create_connection"):
            guard = patch.object(benchmark.socket, name, side_effect=AssertionError("network forbidden in tests"))
            guard.start()
            self.addCleanup(guard.stop)

    def test_phase_ab_identity_and_provenance(self):
        records, manifest = benchmark.load_phase_ab(ROOT, SOURCE)
        self.assertEqual(len(records), 25)
        self.assertEqual([r["source_row_index"] for r in records], benchmark.BENCHMARK_IDS)
        self.assertEqual(records[0]["historical"]["raw_model_query"], "rice grain")
        self.assertEqual(records[0]["historical"]["effective_search_query"], "cooked rice")
        self.assertEqual(sum(r["semantic_review_status"] == "needs_decision" for r in records), 6)
        self.assertEqual(manifest["status"], "complete")

    def test_missing_or_malformed_query_record(self):
        broken = row()
        del broken["variant_b"]["parsed_query"]
        with self.assertRaises(ValueError):
            benchmark.query_contract(broken, "fresh_b")
        broken = row()
        broken["variant_b"]["validation_status"] = "invalid"
        broken["variant_b"]["parsed_query"] = None
        broken["variant_b"]["effective_search_query"] = None
        self.assertEqual(benchmark.query_contract(broken, "fresh_b")["skip_reason"], "invalid_query_generation")

    def test_review_gate_rejects_missing_labels(self):
        with self.assertRaisesRegex(ValueError, "human review"):
            benchmark.load_review_labels(SOURCE / "owner_review.csv", SOURCE)
        blank_copy = self.run_dir / "reviewed.csv"
        shutil.copyfile(SOURCE / "owner_review.csv", blank_copy)
        with self.assertRaisesRegex(ValueError, "human review incomplete"):
            benchmark.load_review_labels(blank_copy, SOURCE)
        self.assertEqual(benchmark.review_gate(row(), "fresh_b", None), "missing_review_labels")

    def test_completed_review_labels_do_not_approve_pending_meanings(self):
        reviewed = self.run_dir / "completed_review.csv"
        with (SOURCE / "owner_review.csv").open(encoding="utf-8", newline="") as source_file:
            source_rows = list(csv.DictReader(source_file))
        for item in source_rows:
            if item["candidate_available"] == "True":
                item.update(correct_intended_meaning="true", visibly_depictable="true",
                            ambiguous_or_wrong_sense="false",
                            inappropriate_text_or_brand_lure="false",
                            reviewer_rationale="fixture human review", reviewer_id="fixture-reviewer",
                            reviewed_at="2026-11-07T10:00:00+07:00")
        with reviewed.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=list(source_rows[0]))
            writer.writeheader()
            writer.writerows(source_rows)
        records, _ = benchmark.load_phase_ab(ROOT, SOURCE)
        labels = benchmark.load_review_labels(reviewed, SOURCE, records)
        self.assertEqual(len(labels), 75)
        self.assertEqual(sum(benchmark.review_gate(item, "fresh_b", labels[item["vocab_id"], "fresh_b"])
                             == "pending_semantic_decision" for item in records), 6)
        self.assertIsNone(benchmark.review_gate(records[0], "fresh_b",
                                                 labels[records[0]["vocab_id"], "fresh_b"]))

    def test_live_mode_requires_review_before_run_creation(self):
        run_id = "unit-test-review-gate-c0"
        output = ROOT / benchmark.OUTPUT_BASE / run_id
        self.assertFalse(output.exists())
        with self.assertRaisesRegex(ValueError, "completed, independently reviewed"):
            benchmark.run(ROOT, run_id, live=True, labels_path=None)
        self.assertFalse(output.exists())

    def test_pending_semantics_skip_even_with_positive_label(self):
        item = row()
        item["semantic_review_status"] = "needs_decision"
        item["target_sense"] = None
        item["image_search_intent"] = None
        self.assertEqual(benchmark.review_gate(item, "fresh_b", {"approved": True}),
                         "pending_semantic_decision")

    def test_missing_approved_intent_and_negative_label_skip(self):
        item = row()
        item["image_search_intent"] = None
        self.assertEqual(benchmark.review_gate(item, "fresh_b", {"approved": True}),
                         "approved_intent_missing")
        self.assertEqual(benchmark.review_gate(row(), "fresh_b", {"approved": False}),
                         "query_rejected_by_human_review")
        self.assertEqual(benchmark.review_gate(row(), "fresh_a",
                                               {"approved": True, "candidate_query": "rice grain"}),
                         "reviewed_query_differs_from_effective_query")

    def test_safe_url_blocks_malformed_and_private(self):
        for url in ("oops", "file:///etc/passwd", "http://127.0.0.1/a",
                    "http://10.0.0.5/x", "http://169.254.169.254/latest",
                    "http://localhost/x", "https://user:pass@example.com/x"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                benchmark.safe_public_url(url, self.resolver)
        self.assertEqual(benchmark.safe_public_url("https://EXAMPLE.com/a#x", self.resolver),
                         "https://example.com/a")
        private_dns = lambda host, port: [(None, None, None, None, ("192.168.1.1", port))]
        with self.assertRaises(ValueError):
            benchmark.safe_public_url("https://example.com/a", private_dns)

    def test_valid_results_retained_and_future_score_empty(self):
        item = row()
        adapter = lambda query, limit: ([{"image": "https://example.com/a.jpg",
                                          "url": "https://example.com/page", "title": "Rice"}], 0.2, 1)
        fetch = lambda url: (jpeg("white"), {"content-type": "image/jpeg"}, 200, 0.1, 1)
        result = benchmark.process_query(self.run_dir, item, "fresh_b", adapter, fetch,
                                         self.resolver, limit=10)
        self.assertEqual(result["results"][0]["status"], "downloaded")
        meta = json.loads((self.run_dir / result["results"][0]["metadata_path"]).read_text(encoding="utf-8"))
        self.assertEqual(meta["target_sense"], "cooked rice")
        self.assertEqual(meta["visual_type"], "food")
        self.assertTrue(meta["license_unknown"])
        self.assertEqual(meta["raw_model_query"], "cooked rice")
        self.assertTrue((self.run_dir / meta["candidate_path"]).is_file())
        self.assertTrue((self.run_dir / meta["preview_path"]).is_file())
        self.assertIsNone(meta["ranking"]["raw_score"])

    def test_raw_model_query_stays_distinct_from_approved_override(self):
        item = row()
        adapter = lambda query, limit: ([{"image": "https://example.com/a.jpg"}], 0.1, 1)
        fetch = lambda url: (jpeg("white"), {}, 200, 0.1, 1)
        result = benchmark.process_query(self.run_dir, item, "fresh_a", adapter, fetch,
                                         self.resolver)
        meta = json.loads((self.run_dir / result["results"][0]["metadata_path"]).read_text(encoding="utf-8"))
        self.assertEqual(meta["raw_model_query"], "rice grain")
        self.assertEqual(meta["effective_search_query"], "cooked rice")

    def test_duplicate_url_and_content_hash_are_preserved(self):
        item = row()
        urls = ["https://example.com/a.jpg", "https://EXAMPLE.com/a.jpg#frag",
                "https://example.com/b.jpg"]
        adapter = lambda query, limit: ([{"image": u} for u in urls], 0.1, 1)
        fetch = lambda url: (jpeg("white"), {}, 200, 0.1, 1)
        result = benchmark.process_query(self.run_dir, item, "fresh_b", adapter, fetch,
                                         self.resolver)
        self.assertEqual([r["status"] for r in result["results"]],
                         ["downloaded", "duplicate_url", "duplicate_content"])

    def test_failures_timeouts_invalid_images_and_private_url_retained(self):
        item = row()
        raw = [{"image": "http://10.0.0.2/a"}, {"image": "https://example.com/timeout"},
               {"image": "https://example.com/bad"}]
        adapter = lambda query, limit: (raw, 0.1, 1)
        def fetch(url):
            if "timeout" in url:
                raise TimeoutError("timed out")
            return b"not an image", {}, 200, 0.1, 1
        result = benchmark.process_query(self.run_dir, item, "fresh_b", adapter, fetch,
                                         self.resolver)
        self.assertEqual([r["status"] for r in result["results"]],
                         ["rejected_url", "download_failed", "invalid_image"])
        self.assertEqual(len(result["results"]), len(raw))

    def test_resume_does_not_search_or_overwrite_valid_candidate(self):
        item = row()
        adapter = lambda query, limit: ([{"image": "https://example.com/a.jpg"}], 0.1, 1)
        fetch = lambda url: (jpeg("white"), {}, 200, 0.1, 1)
        first = benchmark.process_query(self.run_dir, item, "fresh_b", adapter, fetch,
                                        self.resolver)
        def forbidden(*args):
            raise AssertionError("resume called network")
        second = benchmark.process_query(self.run_dir, item, "fresh_b", forbidden, forbidden,
                                         self.resolver)
        self.assertEqual(first, second)

    def test_partial_run_resumes_without_refetching_first_candidate(self):
        item = row()
        adapter = lambda query, limit: ([{"image": "https://example.com/a.jpg"},
                                         {"image": "https://example.com/b.jpg"}], 0.1, 1)
        calls = []
        def interrupted_fetch(url):
            calls.append(url)
            if url.endswith("b.jpg"):
                raise KeyboardInterrupt()
            return jpeg("white"), {}, 200, 0.1, 1
        with self.assertRaises(KeyboardInterrupt):
            benchmark.process_query(self.run_dir, item, "fresh_b", adapter,
                                    interrupted_fetch, self.resolver)
        def no_search(*args):
            raise AssertionError("search repeated")
        def resumed_fetch(url):
            self.assertTrue(url.endswith("b.jpg"))
            return jpeg("black"), {}, 200, 0.1, 1
        result = benchmark.process_query(self.run_dir, item, "fresh_b", no_search,
                                         resumed_fetch, self.resolver)
        self.assertEqual([r["status"] for r in result["results"]], ["downloaded", "downloaded"])
        self.assertEqual(len(calls), 2)

    def test_http_redirect_is_not_followed(self):
        class FakeResponse:
            status = 302
            def getheaders(self):
                return [("Location", "http://127.0.0.1/private")]
        class FakeConnection:
            def __init__(self, *args):
                pass
            def request(self, *args, **kwargs):
                pass
            def getresponse(self):
                return FakeResponse()
            def close(self):
                pass
        public = [(None, None, None, None, ("93.184.215.14", 443))]
        with patch.object(benchmark.socket, "getaddrinfo", return_value=public), \
             patch.object(benchmark, "_PinnedHTTPS", FakeConnection):
            fetcher = benchmark.SafeFetcher(1, 0, 0, benchmark.RateLimiter(0))
            with self.assertRaises(benchmark.HTTPStatusError):
                fetcher("https://example.com/a.jpg")

    def test_changed_candidate_file_fails_resume(self):
        item = row()
        adapter = lambda query, limit: ([{"image": "https://example.com/a.jpg"}], 0.1, 1)
        fetch = lambda url: (jpeg("white"), {}, 200, 0.1, 1)
        result = benchmark.process_query(self.run_dir, item, "fresh_b", adapter, fetch,
                                         self.resolver)
        meta = json.loads((self.run_dir / result["results"][0]["metadata_path"]).read_text(encoding="utf-8"))
        (self.run_dir / meta["candidate_path"]).write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            benchmark.process_query(self.run_dir, item, "fresh_b", adapter, fetch,
                                    self.resolver)

    def test_source_assets_hash_unchanged(self):
        records, manifest = benchmark.load_phase_ab(ROOT, SOURCE)
        benchmark.verify_frozen(ROOT, manifest["input_hashes"])
        benchmark.verify_frozen(ROOT, manifest["protected_hashes"])
        self.assertEqual(len(records), 25)


if __name__ == "__main__":
    unittest.main()
