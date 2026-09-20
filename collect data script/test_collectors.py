"""Offline regression checks: python -m unittest discover -s "collect data script"."""
import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import Mock, patch

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
            (root / "queries.txt").write_text("a cat\n", encoding="utf-8")
            (root / "cat.jpg").write_bytes(b"\xff\xd8\xffcached")
            (root / "cat.json").write_text("{}", encoding="utf-8")
            with patch.object(image, "IMAGE_DIR", root), patch.object(image, "METADATA_DIR", root), \
                 patch.object(image, "CANDIDATE_CACHE_DIR", root / "candidates"), \
                 patch.object(image, "search_image") as search, \
                 patch.object(image.LazySiglipScorer, "score_batch") as score, \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(image.main(["--vocabulary", str(root / "words.txt"),
                                             "--query-file", str(root / "queries.txt")]), 0)
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


class QwenOutputTests(unittest.TestCase):
    def test_repeated_output_is_retried_without_changing_batch_order(self):
        generator = query.QwenQueryGenerator()
        pairs = [("bread", "bánh mì"), ("egg", "trứng")]
        with patch.object(generator, "_load"), \
             patch.object(generator, "_generate_raw", create=True,
                          side_effect=[[("bread loaf", True), ("egg egg icon", True)],
                                       [("chicken egg", True)]]) as generate, \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(generator.generate_batch(pairs), ["bread loaf", "chicken egg"])
        self.assertEqual(generate.call_count, 2)
        self.assertEqual(generate.call_args.args[0], [("egg", "trứng")])
        self.assertIn("egg egg icon", generate.call_args.kwargs["correction"])

    def test_invalid_retry_still_fails_instead_of_deduplicating(self):
        generator = query.QwenQueryGenerator()
        with patch.object(generator, "_load"), \
             patch.object(generator, "_generate_raw", create=True,
                          return_value=[("egg egg icon", True)]) as generate, \
             contextlib.redirect_stdout(io.StringIO()), \
             self.assertRaisesRegex(query.QueryGenerationError, "egg.*after one retry"):
            generator.generate("egg", "trứng")
        self.assertEqual(generate.call_count, 2)

    def test_empty_and_truncated_outputs_have_one_repair_attempt(self):
        for raw in [("", True), ("chicken egg", False)]:
            with self.subTest(raw=raw):
                generator = query.QwenQueryGenerator()
                with patch.object(generator, "_load"), \
                     patch.object(generator, "_generate_raw", create=True,
                                  side_effect=[[raw], [("chicken egg", True)]]), \
                     contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(generator.generate("egg", "trứng"), "chicken egg")

    def test_inference_failure_is_not_retried_as_format_error(self):
        generator = query.QwenQueryGenerator()
        with patch.object(generator, "_load"), \
             patch.object(generator, "_generate_raw", create=True,
                          side_effect=RuntimeError("out of memory")) as generate, \
             self.assertRaisesRegex(query.QueryGenerationError, "inference failed.*out of memory"):
            generator.generate("egg", "trứng")
        generate.assert_called_once()


class QwenIntegrationTests(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(tempfile.TemporaryDirectory())
        self.root = Path(directory)
        self.en = self.root / "en.txt"
        self.vn = self.root / "vn.txt"
        self.keys = self.root / "key.txt"
        self.cache = self.root / "queries.json"
        self.en.write_text(" bank \nmouse\ntrain\n", encoding="utf-8")
        self.vn.write_text(" ngân hàng \ncon chuột\ntàu hỏa\n", encoding="utf-8")
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.enterContext(patch.object(image, "ensure_directories"))
        self.prepare = self.enterContext(patch.object(query, "prepare_queries",
                                                     return_value=["bank building", "mouse animal"]))
        self.process = self.enterContext(patch.object(
            image, "process_word", side_effect=lambda word, text, **kwargs:
            image.ImageResult(ok=True, word=word, query_text=text, status="cached"),
        ))
        self.scorer = self.enterContext(patch.object(image, "LazySiglipScorer"))
        self.args = ["--vocabulary", str(self.en), "--vn-vocabulary", str(self.vn),
                     "--qwen-cache", str(self.cache), "--limit", "2"]

    def test_legacy_default_key_file_does_not_prepare_queries(self):
        self.keys.write_text("bank office\nsmall mouse\nrailway train\n", encoding="utf-8")
        with patch.object(image, "QUERY_PATH", self.keys):
            self.assertEqual(image.main(self.args), 0)
        self.prepare.assert_not_called()
        self.assertEqual([call.args for call in self.process.call_args_list],
                         [("bank", "bank office"), ("mouse", "small mouse")])

    def test_qwen_pairs_and_queries_are_aligned_without_key_file(self):
        events = []
        def prepare(*args, **kwargs):
            events.append("queries ready and model released")
            return ["bank building", "mouse animal"]
        self.prepare.side_effect = prepare
        self.scorer.side_effect = lambda args: events.append("create scorer")
        with patch.object(image, "load_query_file", side_effect=AssertionError("legacy file read")):
            self.assertEqual(image.main(self.args + ["--qwen-queries"]), 0)
        self.prepare.assert_called_once_with(
            [("bank", "ngân hàng"), ("mouse", "con chuột"), ("train", "tàu hỏa")],
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
                "--qwen-queries", "--vocabulary", "en.txt", "--vn-vocabulary", "vn.txt",
                "--qwen-cache", "queries.json", "--qwen-model", "local-qwen", "--qwen-batch-size", "1",
                "--limit", "2", "--no-siglip",
            ]), 0)
        self.assertEqual(self.prepare.call_args.kwargs,
                         dict(limit=2, model_name="local-qwen", batch_size=1, cache_path=self.cache))
        self.scorer.assert_not_called()

    def test_bad_alignment_fails_before_query_or_image_work(self):
        for content, message in [("ngân hàng\n", "EN/VN line count mismatch"),
                                 ("ngân hàng\n\ntàu hỏa\n", "Blank Vietnamese vocabulary at line 2")]:
            with self.subTest(content=content):
                self.vn.write_text(content, encoding="utf-8")
                with self.assertRaisesRegex(CollectionError, message):
                    image.main(self.args + ["--qwen-queries"])
        self.prepare.assert_not_called()
        self.process.assert_not_called()
        self.scorer.assert_not_called()

    def test_invalid_qwen_batch_size_fails_before_generation(self):
        with self.assertRaisesRegex(CollectionError, "--qwen-batch-size must be at least 1"):
            image.main(self.args + ["--qwen-queries", "--qwen-batch-size", "0"])
        self.prepare.assert_not_called()

    def test_qwen_output_count_cannot_silently_truncate_words(self):
        self.prepare.return_value = ["bank building"]
        with self.assertRaisesRegex(CollectionError, "Qwen query count mismatch"):
            image.main(self.args + ["--qwen-queries"])
        self.process.assert_not_called()
        self.scorer.assert_not_called()

    def test_qwen_error_uses_cli_error_handler_without_fallback(self):
        self.prepare.side_effect = query.QueryGenerationError("Qwen returned an empty query")
        output = io.StringIO()
        with patch("collector_common.configure_console"), contextlib.redirect_stdout(output), \
             self.assertRaises(SystemExit) as raised:
            run_cli(lambda: image.main(self.args + ["--qwen-queries"]))
        self.assertEqual(raised.exception.code, 1)
        self.assertIn("ERROR: Qwen returned an empty query", output.getvalue())
        self.process.assert_not_called()
        self.scorer.assert_not_called()

    def test_legacy_cli_parsing_does_not_import_qwen_or_ml(self):
        result = subprocess.run(
            [sys.executable, "-c", "import imagecollector, sys; imagecollector.parse_args([]); "
             "assert not any(m in sys.modules for m in "
             "('query_generator', 'torch', 'transformers'))"],
            cwd=Path(__file__).parent, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
