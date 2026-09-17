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
from collector_common import CollectionError, load_vocabulary, validate_common_arguments


class CollectorTests(unittest.TestCase):
    def test_audio_import_is_independent(self):
        result = subprocess.run(
            [sys.executable, "-c", "import audiocollector, sys; "
             "assert not any(m in sys.modules for m in "
             "('imagecollector', 'image_scorer', 'torch', 'transformers', 'PIL'))"],
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


if __name__ == "__main__":
    unittest.main()
