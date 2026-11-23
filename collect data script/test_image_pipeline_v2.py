"""Offline tests for image pipeline v2 policy and runner (mocked Qwen, search, download, SigLIP)."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

import image_pipeline_v2 as pipeline
import visual_query_policy as policy
from query_generator import QueryGenerationError

ROOT = Path(__file__).resolve().parents[1]


class FakeGenerator:
    batch_size = 2

    def __init__(self, answers):
        self.answers = answers  # word -> list of raw outputs (first, retry)
        self.calls = []

    def _load(self):
        pass

    def raw(self, _generator, words, correction):
        self.calls.append((tuple(words), correction is not None))
        return [(self.answers[w].pop(0), True) for w in words]


class PolicyTests(unittest.TestCase):
    def test_routes_and_query_styles(self):
        cases = {
            "CONCRETE | pear fruit": ("PHOTO", "pear fruit"),
            "ACTION | person cooking food": ("ICON", "person cooking food icon"),
            "STATE | tired person yawning icon": ("ICON", "tired person yawning icon"),
            "TIME | night sky moon icon": ("SCENE", "night sky moon illustration"),
            "ABSTRACT | person bright idea illustration": ("SCENE", "person bright idea illustration"),
        }
        for raw, (route, query) in cases.items():
            word = raw.split("|")[1].split()[0]
            with self.subTest(raw=raw):
                typed = policy.parse_typed_output(word, raw)
                self.assertEqual((typed.route, typed.query), (route, query))

    def test_connector_is_curated_without_query(self):
        typed = policy.parse_typed_output("although", "CONNECTOR | none")
        self.assertEqual((typed.route, typed.query), ("CURATE", None))

    def test_rejects_malformed_and_unknown_output(self):
        for raw in ("pear fruit", "FRUIT | pear", "CONCRETE | apple icon", "CONCRETE | red fruit", "A | b | c",
                    "ACTION | action"):
            with self.subTest(raw=raw), self.assertRaises(QueryGenerationError):
                policy.parse_typed_output("apple" if "CONCRETE" in raw else "buy", raw)

    def test_concrete_with_non_physical_class_is_rejected_for_retry(self):
        for raw in ("CONCRETE | swim action", "CONCRETE | project abstract", "CONCRETE | work activity",
                    "CONCRETE | business organization"):
            with self.subTest(raw=raw), self.assertRaisesRegex(QueryGenerationError, "not a physical noun"):
                policy.parse_typed_output(raw.split("|")[1].split()[0], raw)
        self.assertEqual(policy.parse_typed_output("mountain", "CONCRETE | mountain natural feature").route, "PHOTO")

    def test_digits_punctuation_and_meta_words_are_stripped(self):
        self.assertEqual(policy.parse_typed_output("always", "TIME | calendar with 12 o'clock marked").query,
                         "calendar with clock marked illustration")
        self.assertEqual(policy.parse_typed_output("database", "ABSTRACT | screen showing data organization").query,
                         "screen data organization illustration")

    def test_collision_prone_tokens_are_stripped(self):
        self.assertEqual(policy.parse_typed_output("buy", "ACTION | person buy action").query, "person buy icon")
        self.assertEqual(policy.parse_typed_output("write", "ACTION | person writing text letters").query,
                         "person writing icon")

    def test_classify_retries_once_then_fails(self):
        gen = FakeGenerator({"cook": ["cook", "ACTION | person cooking"], "bad": ["x", "y"]})
        self.assertEqual(policy.classify_words(["cook"], gen, raw_fn=gen.raw)[0].query, "person cooking icon")
        self.assertEqual(gen.calls[-1], (("cook",), True))
        with self.assertRaises(QueryGenerationError):
            policy.classify_words(["bad"], gen, raw_fn=gen.raw)

    def test_typed_prompt_examples_avoid_benchmark_words(self):
        benchmark = set((ROOT / "data/vocabulary/en.txt").read_text(encoding="utf-8").split())
        examples = {line.split(":", 1)[1].strip() for line in policy.TYPED_PROMPT.splitlines() if line.startswith("Input:")}
        self.assertEqual(examples & benchmark, set())

    def test_technical_rejection(self):
        tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        black, tiny, good, checker = (tmp / f"{n}.jpg" for n in ("black", "tiny", "good", "checker"))
        Image.new("RGB", (300, 300), (0, 0, 0)).save(black)
        Image.new("RGB", (60, 300), (200, 30, 30)).save(tiny)
        img = Image.new("RGB", (300, 300), (255, 255, 255))
        img.paste((200, 30, 30), (80, 80, 220, 220))
        img.save(good)
        board = Image.new("RGB", (320, 320))
        for y in range(0, 320, 10):
            for x in range(0, 320, 10):
                board.paste((204, 204, 204) if (x // 10 + y // 10) % 2 else (255, 255, 255), (x, y, x + 10, y + 10))
        board.save(checker)
        self.assertIn("near-uniform", policy.technical_rejection(black))
        self.assertIn("too small", policy.technical_rejection(tiny))
        self.assertIn("checkerboard", policy.technical_rejection(checker))
        self.assertIsNone(policy.technical_rejection(good))

    def test_proposal_skips_rejected_and_reports_no_suitable(self):
        cands = [{"candidate_id": "a", "score": 9.0, "rejection": "near-uniform"},
                 {"candidate_id": "b", "score": 2.0, "rejection": None},
                 {"candidate_id": "c", "score": 5.0, "rejection": None}]
        proposal = policy.propose(cands)
        self.assertEqual((proposal["proposed_candidate_id"], proposal["alternatives"]), ("c", ["b"]))
        self.assertEqual(proposal["review_status"], "needs_review")
        self.assertEqual(policy.propose(cands[:1])["status"], "NO_SUITABLE_IMAGE")


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.item = {"item_id": "item-1", "english": "cook", "japanese": "りょうりする", "vietnamese": "nấu ăn"}

    def fake_download(self, url, destination, **_):
        colour = {"u1": (0, 0, 0), "u2": (30, 120, 200), "u3": (200, 60, 20)}[url]
        img = Image.new("RGB", (240, 240), (255, 255, 255))
        if url != "u1":
            img.paste(colour, (40, 40, 200, 200))
        else:
            img = Image.new("RGB", (240, 240), colour)
        img.save(destination, format="PNG")

    def test_end_to_end_with_mocks(self):
        typed = policy.TypedQuery("cook", "ACTION", "ICON", "person cooking food icon")
        batch = SimpleNamespace(raw_count=3, candidates=[{"image_url": u, "source_page_url": "p", "title": u} for u in ("u1", "u2", "u3")])
        searched = []
        scorer = SimpleNamespace(score_batch=lambda q, paths: [SimpleNamespace(score=float(i)) for i, _ in enumerate(paths)])
        import imagecollector
        result = pipeline.process_item(self.item, self.tmp, typed=typed, scorer=scorer, approved={},
                                       search=lambda q, **kw: searched.append((q, kw)) or batch,
                                       download=self.fake_download, normalize=imagecollector.normalize_image_to_jpeg)
        self.assertEqual(searched[0][0], "person cooking food icon")
        self.assertEqual(searched[0][1]["retries"], 2)
        self.assertEqual(result["status"], "PROPOSED")
        self.assertIn("near-uniform", result["candidates"][0]["rejection"])
        self.assertEqual(result["proposed_candidate_id"], "item-1-03")
        self.assertEqual(result["review_status"], "needs_review")

    def test_connector_and_search_failure_never_produce_images(self):
        curated = pipeline.process_item(self.item, self.tmp, typed=policy.TypedQuery("cook", "CONNECTOR", "CURATE", None), approved={})
        self.assertEqual((curated["status"], curated["candidates"]), ("NEEDS_CURATION", []))

        def boom(*_, **__):
            raise RuntimeError("timeout")
        failed = pipeline.process_item(self.item, self.tmp, typed=policy.TypedQuery("cook", "ACTION", "ICON", "x icon"),
                                       approved={}, search=boom)
        self.assertEqual(failed["status"], "SEARCH_FAILED")

    def test_approved_registry_reuse_carries_restriction(self):
        registry = json.loads((ROOT / "data/vocabulary/approved_images_v1.json").read_text(encoding="utf-8"))
        approved = {e["lookup_key"]: e for e in registry["entries"]}
        self.assertEqual(len(approved), 100)
        because = next(e for e in registry["entries"] if e["english"] == "because")
        item = {"item_id": "x", "english": "Because ", "japanese": because["japanese"], "vietnamese": because["vietnamese"]}
        result = pipeline.process_item(item, self.tmp, approved=approved)
        self.assertEqual(result["status"], "APPROVED_REUSE")
        self.assertEqual(result["usage_restriction"], "INTERNAL_ONLY_TEMPORARY")
        other = dict(item, vietnamese="vì")
        with self.assertRaises(AttributeError):  # no match -> needs generator; proves no text-only reuse
            pipeline.process_item(other, self.tmp, approved=approved, generator=None)


if __name__ == "__main__":
    unittest.main()
