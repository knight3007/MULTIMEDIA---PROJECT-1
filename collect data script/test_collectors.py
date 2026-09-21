"""Offline regression checks: python -m unittest discover -s "collect data script"."""
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image

import audiocollector as audio
import collector
import imagecollector as image
from collector_common import CollectionError, load_vocabulary, run_cli, validate_common_arguments
import query_generator as query


class CollectorTests(unittest.TestCase):
    def test_audio_import_is_independent(self):
        result = subprocess.run(
            [sys.executable, "-c", "import audiocollector, sys; "
             "assert not any(m in sys.modules for m in "
             "('imagecollector', 'query_generator', 'image_scorer', 'torch', 'transformers', 'PIL'))"],
            cwd=Path(__file__).parent, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_legacy_dispatch(self):
        with patch.object(image, "main", return_value=0) as run:
            self.assertEqual(collector.main(["--limit", "1"]), 0)
            run.assert_called_once_with(["--limit", "1"])
        with patch.object(audio, "main", return_value=1) as run:
            self.assertEqual(collector.main(["--audio-only", "--limit", "2"]), 1)
            run.assert_called_once_with(["--limit", "2"])

    def test_invalid_arguments_and_duplicates(self):
        for flag, value in [("--limit", "0"), ("--timeout", "0"),
                            ("--retries", "-1"), ("--retry-delay", "nan"),
                            ("--rate-limit-delay", "-1")]:
            with self.subTest(flag=flag), self.assertRaises(CollectionError):
                validate_common_arguments(audio.parse_args([flag, value]))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "words.txt"
            path.write_text("cat\ndog\ncat\n", encoding="utf-8")
            with self.assertRaisesRegex(CollectionError, "Duplicate vocabulary found: cat"):
                load_vocabulary(path)

    def test_cached_images_do_not_load_model_or_search(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "words.txt").write_text("cat\n", encoding="utf-8")
            (root / "cat.jpg").write_bytes(b"\xff\xd8\xffcached")
            (root / "cat.json").write_text(
                json.dumps({"provider": "duckduckgo", "search_query": "a cat"}), encoding="utf-8",
            )
            with patch.object(image, "IMAGE_DIR", root), patch.object(image, "METADATA_DIR", root), \
                 patch.object(image, "CANDIDATE_CACHE_DIR", root / "candidates"), \
                 patch.object(query, "prepare_queries", return_value=["a cat"]), \
                 patch.object(image, "search_images") as search, \
                 patch.object(image.LazySiglipScorer, "score_batch") as score, \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(image.main(["--vocabulary", str(root / "words.txt")]), 0)
                search.assert_not_called()
                score.assert_not_called()

    def test_siglip_error_is_reported_as_collection_failure(self):
        from image_scorer import ImageScoringError
        scorer = Mock()
        scorer.score_batch.side_effect = ImageScoringError("bad image")
        with patch.object(image, "download_candidate_images", return_value=[({"url": "test"}, Path("test.jpg"))]), \
             contextlib.redirect_stdout(io.StringIO()), \
             self.assertRaisesRegex(CollectionError, "bad image"):
            image.choose_image_result_with_siglip("cat", "cat", [], scorer,
                                                  timeout=1, retries=0, retry_delay=0)

    def test_audio_generation_then_cache_hit(self):
        def synthesize(reading, destination, **kwargs):
            with wave.open(str(destination), "wb") as stream:
                stream.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
                stream.writeframes(b"\x00\x00" * 1600)
            return "Test voice"

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(audio, "PROJECT_ROOT", root), patch.object(audio, "AUDIO_DIR", root / "audio"), \
                 patch.object(audio, "AUDIO_METADATA_DIR", root / "metadata"), \
                 patch.object(audio, "synthesize_sapi_wav", side_effect=synthesize) as synth, \
                 contextlib.redirect_stdout(io.StringIO()):
                audio.ensure_audio_directories()
                kwargs = dict(timeout=1, retries=0, retry_delay=0)
                first = audio.process_audio_entry(1, "ねこ", "ねこ", **kwargs)
                second = audio.process_audio_entry(1, "ねこ", "ねこ", **kwargs)
                self.assertEqual(first.status, "success")
                self.assertEqual(first.output.name, "ねこ.wav")
                self.assertEqual(audio.audio_metadata_path(1, "ねこ", "ねこ").name, "ねこ.json")
                self.assertEqual(second.status, "cache_hit")
                self.assertAlmostEqual(first.duration_seconds, 0.1)
                self.assertTrue(audio.audio_metadata_path(1, "ねこ", "ねこ").exists())
                synth.assert_called_once()


class DuckDuckGoProviderTests(unittest.TestCase):
    @staticmethod
    def candidate(name: str) -> dict:
        return {
            "provider": "duckduckgo",
            "title": name,
            "image_url": f"https://cdn.example/{name}.png",
            "thumbnail_url": None,
            "source_page_url": f"https://example.com/{name}",
            "width": 640,
            "height": 480,
            "source": "DuckDuckGo",
        }

    def test_ddg_results_are_normalized_and_bad_candidates_are_filtered(self):
        raw = [
            {
                "title": "Apple fruit",
                "image": "https://cdn.example/apple.png",
                "thumbnail": "https://cdn.example/apple-thumb.jpg",
                "url": "https://example.com/apple",
                "width": 800,
                "height": 600,
                "source": "DuckDuckGo",
            },
            {"title": "missing image", "url": "https://example.com/missing"},
            {"image": "ftp://example.com/apple.jpg", "url": "https://example.com/ftp"},
            {"image": "http://localhost/private.jpg", "url": "https://example.com/private"},
            {"image": "https://cdn.example/apple.png", "url": "https://example.com/duplicate-image"},
            {"image": "https://cdn.example/other.jpg", "url": "https://example.com/apple"},
            "not a mapping",
        ]

        self.assertEqual(image.normalize_ddg_results(raw), [{
            "provider": "duckduckgo",
            "title": "Apple fruit",
            "image_url": "https://cdn.example/apple.png",
            "thumbnail_url": "https://cdn.example/apple-thumb.jpg",
            "source_page_url": "https://example.com/apple",
            "width": 800,
            "height": 600,
            "source": "DuckDuckGo",
        }])

    def test_ddg_search_uses_explicit_safe_settings_and_retries(self):
        from ddgs.exceptions import DDGSException

        raw = [{"title": "Cat", "image": "https://cdn.example/cat.webp",
                "url": "https://example.com/cat"}]
        client = Mock()
        client.images.side_effect = [DDGSException("temporarily limited"), raw]
        with patch("ddgs.DDGS", return_value=client) as ddgs, \
             patch.object(image.time, "sleep") as sleep:
            batch = image.search_images("cat", page_size=7, timeout=5, retries=1, retry_delay=0.25)

        self.assertEqual(batch.raw_count, 1)
        self.assertEqual(len(batch.candidates), 1)
        self.assertGreaterEqual(batch.duration_seconds, 0)
        ddgs.assert_called_with(timeout=5)
        client.images.assert_called_with(
            query="cat", region="wt-wt", safesearch="moderate",
            max_results=7, backend="duckduckgo",
        )
        sleep.assert_called_once_with(0.25)

    def test_empty_ddg_results_are_a_clean_provider_failure(self):
        client = Mock()
        client.images.return_value = []
        with patch("ddgs.DDGS", return_value=client), \
             self.assertRaisesRegex(CollectionError, "DuckDuckGo.*no image results"):
            image.search_images("missing", page_size=7, timeout=5, retries=0, retry_delay=0)

    def test_one_failed_download_does_not_discard_other_candidates(self):
        candidates = [self.candidate("bad"), self.candidate("good")]
        directory = self.enterContext(tempfile.TemporaryDirectory())
        stale_dir = Path(directory) / "cat"
        stale_dir.mkdir()
        (stale_dir / "01.jpg").write_bytes(b"\xff\xd8\xffstale-openverse-candidate")
        with patch.object(image, "CANDIDATE_CACHE_DIR", Path(directory)), \
             patch.object(image, "download_image_as_jpeg",
                          side_effect=[CollectionError("HTTP 403"), None]) as download, \
             contextlib.redirect_stdout(io.StringIO()):
            downloaded = image.download_candidate_images(
                "cat", candidates, timeout=5, retries=0, retry_delay=0,
            )
        self.assertEqual([candidate for candidate, _path in downloaded], [candidates[1]])
        self.assertEqual(download.call_count, 2)

    def test_download_decodes_png_content_and_saves_final_jpeg(self):
        source = io.BytesIO()
        Image.new("RGBA", (8, 6), (255, 0, 0, 128)).save(source, format="PNG")
        directory = self.enterContext(tempfile.TemporaryDirectory())
        destination = Path(directory) / "image.jpg"
        with patch.object(image, "request_with_retry",
                          return_value=(source.getvalue(), {"content-type": "image/png"}, 200)):
            image.download_image_as_jpeg(
                "https://cdn.example/image.png", destination,
                timeout=5, retries=0, retry_delay=0,
            )
        with Image.open(destination) as saved:
            self.assertEqual(saved.format, "JPEG")
            self.assertEqual(saved.mode, "RGB")
            self.assertEqual(saved.size, (8, 6))

    def test_provider_mismatch_invalidates_old_image_cache(self):
        directory = self.enterContext(tempfile.TemporaryDirectory())
        root = Path(directory)
        image_path = root / "cat.jpg"
        metadata_path = root / "cat.json"
        image_path.write_bytes(b"\xff\xd8\xffcached")
        metadata_path.write_text(json.dumps({
            "provider": "openverse", "search_query": "cat",
        }), encoding="utf-8")
        self.assertFalse(image.is_valid_image_cache(image_path, metadata_path, "cat"))
        metadata_path.write_text(json.dumps({
            "provider": "duckduckgo", "search_query": "cat",
        }), encoding="utf-8")
        self.assertTrue(image.is_valid_image_cache(image_path, metadata_path, "cat"))

    def test_metadata_contains_real_ddg_fields_without_fake_license(self):
        metadata = image.metadata_from_result(
            "cat", "cat animal", self.candidate("cat"),
            {"method": "siglip2", "model": "test-model", "score": 0.75},
        )
        self.assertEqual(metadata["provider"], "duckduckgo")
        self.assertEqual(metadata["image_url"], "https://cdn.example/cat.png")
        self.assertEqual(metadata["source_page_url"], "https://example.com/cat")
        self.assertEqual(metadata["image_selection"]["score"], 0.75)
        self.assertTrue({"creator", "creator_url", "license", "license_url",
                         "foreign_landing_url"}.isdisjoint(metadata))

    def test_siglip_still_selects_the_highest_scoring_download(self):
        from image_scorer import ScoreResult

        first, second = self.candidate("first"), self.candidate("second")
        first_path, second_path = Path("first.jpg"), Path("second.jpg")
        scorer = Mock()
        scorer.score_batch.return_value = [
            ScoreResult(first_path, 0.1), ScoreResult(second_path, 0.9),
        ]
        with patch.object(image, "download_candidate_images",
                          return_value=[(first, first_path), (second, second_path)]), \
             contextlib.redirect_stdout(io.StringIO()):
            chosen, score, count, download_seconds, scoring_seconds = \
                image.choose_image_result_with_siglip(
                    "cat", "cat animal", [first, second], scorer,
                    timeout=5, retries=0, retry_delay=0,
                )
        self.assertIs(chosen, second)
        self.assertEqual(score, 0.9)
        self.assertEqual(count, 2)
        self.assertGreaterEqual(download_seconds, 0)
        self.assertGreaterEqual(scoring_seconds, 0)


class QwenOutputTests(unittest.TestCase):
    def test_normalize_query_accepts_clean_queries_and_controlled_icons(self):
        for raw, expected in [
            ("  APPLE   FRUIT  ", "apple fruit"),
            ("software application icon", "software application icon"),
            ("password lock icon", "password lock icon"),
            ("notification bell icon", "notification bell icon"),
        ]:
            with self.subTest(raw=raw):
                self.assertEqual(query.normalize_query(raw), expected)

    def test_normalize_query_rejects_malformed_or_meta_output(self):
        invalid = [
            '"apple fruit"',
            "green-apple",
            "apple fruit\nExplanation",
            "one two three four five six seven eight nine ten eleven twelve thirteen",
            "visual concept",
            "egg eggs",
            "milk container milk bottle milk jug",
            "apple fruit apples",
            "important thing",
        ]
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(query.QueryGenerationError):
                query.normalize_query(raw)

    def test_raw_generation_uses_optimized_non_thinking_contract(self):
        import torch

        generator = query.QwenQueryGenerator()
        generator.torch = torch
        generator.tokenizer = Mock()
        generator.tokenizer.pad_token_id = 0
        generator.tokenizer.eos_token_id = 9
        generator.tokenizer.apply_chat_template.return_value = "prompt"
        generator.tokenizer.return_value = {
            "input_ids": torch.tensor([[1, 2]]),
            "attention_mask": torch.tensor([[1, 1]]),
        }
        generator.tokenizer.decode.return_value = "apple fruit"
        generator.model = Mock()
        generator.model.generation_config.eos_token_id = 9
        generator.model.generate.return_value = torch.tensor([[1, 2, 3, 9]])

        with patch.object(generator, "_input_device", return_value=torch.device("cpu")):
            self.assertEqual(generator._generate_raw(["apple"]),
                             [("apple fruit", True)])

        template_kwargs = generator.tokenizer.apply_chat_template.call_args.kwargs
        self.assertFalse(template_kwargs["enable_thinking"])
        messages = generator.tokenizer.apply_chat_template.call_args.args[0]
        self.assertIn("Query:", messages[-1]["content"])
        self.assertEqual(
            messages[-1]["content"],
            "Input: apple\nQuery:",
        )
        self.assertNotIn("Vietnamese", "\n".join(message["content"] for message in messages))
        prompt = messages[0]["content"]
        self.assertIn("one common everyday sense", prompt)
        self.assertIn("brand", prompt)
        self.assertIn("1-12 lowercase English words", prompt)
        self.assertIn("keyword stuffing", prompt)
        self.assertIn("same thing", prompt)
        self.assertIn("related object, part, effect, action, place, tool, environment, accessory, or infrastructure", prompt)
        self.assertIn("short noun phrase", prompt)
        self.assertIn("input word exactly once", prompt)
        self.assertIn("disambiguation", prompt)
        self.assertIn("association", prompt)
        self.assertIn("Use each word at most once", prompt)
        self.assertIn("Input: pear\nQuery: pear fruit", prompt)
        self.assertIn("Input: autumn\nQuery: autumn season", prompt)
        generation_kwargs = generator.model.generate.call_args.kwargs
        self.assertEqual(generation_kwargs["max_new_tokens"], 32)
        self.assertFalse(generation_kwargs["do_sample"])
        for name in ("temperature", "top_p", "top_k"):
            self.assertNotIn(name, generation_kwargs)

        generator.tokenizer.apply_chat_template.reset_mock()
        with patch.object(generator, "_input_device", return_value=torch.device("cpu")):
            generator._generate_raw(["apple"], correction="Fix the format.")
        repair_messages = generator.tokenizer.apply_chat_template.call_args.args[0]
        self.assertIn("Fix the format.", repair_messages[-1]["content"])
        self.assertTrue(repair_messages[-1]["content"].endswith("Query:"))

    def test_repeated_output_is_retried_without_changing_batch_order(self):
        generator = query.QwenQueryGenerator()
        words = ["bread", "egg"]
        with patch.object(generator, "_load"), \
             patch.object(generator, "_generate_raw", create=True,
                          side_effect=[[("bread loaf", True), ("egg egg icon", True)],
                                       [("chicken egg", True)]]) as generate, \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(generator.generate_batch(words), ["bread loaf", "chicken egg"])
        self.assertEqual(generate.call_count, 2)
        self.assertEqual(generate.call_args.args[0], ["egg"])
        correction = generate.call_args.kwargs["correction"]
        self.assertNotIn("egg egg icon", correction)
        self.assertIn("failed validation", correction)
        self.assertIn("Start over", correction)
        self.assertIn("singular and plural", correction)
        self.assertIn("Preserve the input as the target", correction)
        self.assertIn("one broad semantic class", correction)
        self.assertIn("Do not enumerate", correction)
        self.assertIn("no icon for a physical", correction)
        self.assertNotIn("Vietnamese", correction)

    def test_invalid_retry_still_fails_instead_of_deduplicating(self):
        generator = query.QwenQueryGenerator()
        with patch.object(generator, "_load"), \
             patch.object(generator, "_generate_raw", create=True,
                          return_value=[("egg egg icon", True)]) as generate, \
             contextlib.redirect_stdout(io.StringIO()), \
             self.assertRaisesRegex(query.QueryGenerationError, "egg.*after one retry"):
            generator.generate("egg")
        self.assertEqual(generate.call_count, 2)

    def test_empty_and_truncated_outputs_have_one_repair_attempt(self):
        for raw in [("", True), ("chicken egg", False)]:
            with self.subTest(raw=raw):
                generator = query.QwenQueryGenerator()
                with patch.object(generator, "_load"), \
                     patch.object(generator, "_generate_raw", create=True,
                                  side_effect=[[raw], [("chicken egg", True)]]), \
                     contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(generator.generate("egg"), "chicken egg")

    def test_inference_failure_is_not_retried_as_format_error(self):
        generator = query.QwenQueryGenerator()
        with patch.object(generator, "_load"), \
             patch.object(generator, "_generate_raw", create=True,
                          side_effect=RuntimeError("out of memory")) as generate, \
             self.assertRaisesRegex(query.QueryGenerationError, "inference failed.*out of memory"):
            generator.generate("egg")
        generate.assert_called_once()

    def test_cache_contains_only_english_words_and_queries(self):
        directory = self.enterContext(tempfile.TemporaryDirectory())
        cache_path = Path(directory) / "queries.json"
        with patch.object(query.QwenQueryGenerator, "generate_batch",
                          return_value=["bank building", "mouse animal"]), \
             patch.object(query.QwenQueryGenerator, "close"), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(
                query.prepare_queries(["bank", "mouse"], limit=2, cache_path=cache_path),
                ["bank building", "mouse animal"],
            )
        cache_text = cache_path.read_text(encoding="utf-8")
        self.assertNotIn("meaning", cache_text)
        self.assertNotIn("Vietnamese", cache_text)


class QwenIntegrationTests(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(tempfile.TemporaryDirectory())
        self.root = Path(directory)
        self.en = self.root / "en.txt"
        self.cache = self.root / "queries.json"
        self.en.write_text(" bank \nmouse\ntrain\n", encoding="utf-8")
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.enterContext(patch.object(image, "ensure_directories"))
        self.prepare = self.enterContext(patch.object(query, "prepare_queries",
                                                     return_value=["bank building", "mouse animal"]))
        self.process = self.enterContext(patch.object(
            image, "process_word", side_effect=lambda word, text, **kwargs:
            image.ImageResult(ok=True, word=word, query_text=text, status="cached"),
        ))
        self.scorer = self.enterContext(patch.object(image, "LazySiglipScorer"))
        self.args = ["--vocabulary", str(self.en),
                     "--qwen-cache", str(self.cache), "--limit", "2"]

    def test_words_and_generated_queries_are_aligned(self):
        events = []
        def prepare(*args, **kwargs):
            events.append("queries ready and model released")
            return ["bank building", "mouse animal"]
        self.prepare.side_effect = prepare
        self.scorer.side_effect = lambda args: events.append("create scorer")
        self.assertEqual(image.main(self.args), 0)
        self.prepare.assert_called_once_with(
            ["bank", "mouse", "train"],
            limit=2, model_name=query.DEFAULT_QWEN_MODEL,
            batch_size=query.DEFAULT_BATCH_SIZE, cache_path=self.cache,
        )
        self.assertEqual(events, ["queries ready and model released", "create scorer"])
        self.assertEqual([call.args for call in self.process.call_args_list],
                         [("bank", "bank building"), ("mouse", "mouse animal")])

    def test_qwen_options_are_forwarded_and_paths_are_project_relative(self):
        with patch.object(image, "PROJECT_ROOT", self.root), \
             patch("collector_common.PROJECT_ROOT", self.root):
            self.assertEqual(image.main([
                "--vocabulary", "en.txt",
                "--qwen-cache", "queries.json", "--qwen-model", "local-qwen", "--qwen-batch-size", "1",
                "--limit", "2", "--no-siglip",
            ]), 0)
        self.assertEqual(self.prepare.call_args.kwargs,
                         dict(limit=2, model_name="local-qwen", batch_size=1, cache_path=self.cache))
        self.scorer.assert_not_called()

    def test_cli_has_no_legacy_query_or_vietnamese_options(self):
        args = image.parse_args([])
        self.assertFalse(hasattr(args, "vn_vocabulary"))
        self.assertFalse(hasattr(args, "query_file"))
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            image.parse_args(["--query-file", "key.txt"])

    def test_invalid_qwen_batch_size_fails_before_generation(self):
        with self.assertRaisesRegex(CollectionError, "--qwen-batch-size must be at least 1"):
            image.main(self.args + ["--qwen-batch-size", "0"])
        self.prepare.assert_not_called()

    def test_qwen_output_count_cannot_silently_truncate_words(self):
        self.prepare.return_value = ["bank building"]
        with self.assertRaisesRegex(CollectionError, "Qwen query count mismatch"):
            image.main(self.args)
        self.process.assert_not_called()
        self.scorer.assert_not_called()

    def test_qwen_error_uses_cli_error_handler_without_fallback(self):
        self.prepare.side_effect = query.QueryGenerationError("Qwen returned an empty query")
        output = io.StringIO()
        with patch("collector_common.configure_console"), contextlib.redirect_stdout(output), \
             self.assertRaises(SystemExit) as raised:
            run_cli(lambda: image.main(self.args))
        self.assertEqual(raised.exception.code, 1)
        self.assertIn("ERROR: Qwen returned an empty query", output.getvalue())
        self.process.assert_not_called()
        self.scorer.assert_not_called()

    def test_cli_parsing_does_not_import_qwen_or_ml(self):
        result = subprocess.run(
            [sys.executable, "-c", "import imagecollector, sys; imagecollector.parse_args([]); "
             "assert not any(m in sys.modules for m in "
             "('query_generator', 'torch', 'transformers'))"],
            cwd=Path(__file__).parent, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
