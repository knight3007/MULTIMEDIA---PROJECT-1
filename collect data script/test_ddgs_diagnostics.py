"""Offline guards for DDGS backend selection and staging diagnostics."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from ddgs.exceptions import DDGSException

import imagecollector as image
from collector_common import CollectionError
from stage_image_replacements import stage_replacements
from test_stage_image_replacements import approved_records


class DDGSDiagnosticsTests(unittest.TestCase):
    def test_explicit_bing_backend_is_recorded_without_changing_legacy_provider(self):
        client = Mock()
        client.images.return_value = [{"image": "https://example.test/cat.jpg"}]
        with patch("ddgs.DDGS", return_value=client):
            batch = image.search_images("cat", page_size=1, timeout=5, retries=0,
                                        retry_delay=0, backend="bing")
        self.assertEqual(batch.backend, "bing")
        self.assertEqual(batch.candidates[0]["provider"], "duckduckgo")
        self.assertEqual(batch.candidates[0]["search_backend"], "bing")
        self.assertEqual(client.images.call_args.kwargs["backend"], "bing")
        metadata = image.metadata_from_result("cat", "cat", batch.candidates[0])
        self.assertEqual(metadata["provider"], "duckduckgo")
        self.assertEqual(metadata["search_client"], "ddgs")
        self.assertEqual(metadata["search_backend"], "bing")

    def test_failed_search_records_backend_attempt_type_and_elapsed_time(self):
        client = Mock()
        client.images.side_effect = DDGSException(
            "request https://name:secret@example.test/path failed")
        with patch("ddgs.DDGS", return_value=client):
            with self.assertRaises(CollectionError) as caught:
                image.search_images("cat", page_size=1, timeout=5, retries=0,
                                    retry_delay=0, backend="duckduckgo")
        error = caught.exception
        self.assertEqual(error.backend, "duckduckgo")
        self.assertEqual(error.attempts, 1)
        self.assertEqual(error.cause_type, "DDGSException")
        self.assertGreater(error.duration_seconds, 0)
        self.assertNotIn("secret", str(error))

    def test_process_word_reports_search_failure_stage_and_timing(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(image, "IMAGE_DIR", Path(directory)), \
                 patch.object(image, "METADATA_DIR", Path(directory)), \
                 patch.object(image, "search_images", side_effect=CollectionError("timeout")), \
                 contextlib.redirect_stdout(io.StringIO()):
                result = image.process_word("cat", "cat", timeout=5, retries=0,
                                            retry_delay=0, page_size=1,
                                            search_backend="bing")
        self.assertFalse(result.ok)
        self.assertEqual(result.failure_stage, "search")
        self.assertEqual(result.search_backend, "bing")
        self.assertGreater(result.search_seconds, 0)

    def test_scoring_failure_is_not_reported_as_search_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = {"provider": "duckduckgo",
                         "image_url": "https://example.test/cat.jpg"}
            scorer = Mock()
            from image_scorer import ImageScoringError
            scorer.score_batch.side_effect = ImageScoringError("model unavailable")
            with patch.object(image, "IMAGE_DIR", Path(directory)), \
                 patch.object(image, "METADATA_DIR", Path(directory)), \
                 patch.object(image, "search_images", return_value=image.ImageSearchBatch(
                     [candidate], 1, 0.2)), \
                 patch.object(image, "download_candidate_images", return_value=[
                     (candidate, Path(directory) / "cat.img")]), \
                 contextlib.redirect_stdout(io.StringIO()):
                result = image.process_word("cat", "cat", timeout=5, retries=0,
                                            retry_delay=0, page_size=1, scorer=scorer)
        self.assertEqual(result.failure_stage, "scoring")
        self.assertEqual(result.search_seconds, 0.2)

    def test_bing_download_failure_is_labeled_as_download_not_duckduckgo(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(image, "IMAGE_DIR", Path(directory)), \
                 patch.object(image, "METADATA_DIR", Path(directory)), \
                 patch.object(image, "search_images", return_value=image.ImageSearchBatch(
                     [], 1, 0.2, "bing")), \
                 contextlib.redirect_stdout(io.StringIO()):
                result = image.process_word("cat", "cat", timeout=5, retries=0,
                                            retry_delay=0, page_size=1,
                                            search_backend="bing")
        self.assertEqual(result.failure_stage, "download")
        self.assertEqual(result.search_seconds, 0.2)
        self.assertNotIn("DuckDuckGo", result.reason)

    def test_staging_passes_backend_and_marks_search_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def failed_process(word, query, **kwargs):
                self.assertEqual(kwargs["search_backend"], "bing")
                return image.ImageResult(False, word, query, "failed", reason="timeout",
                                         search_seconds=0.4, search_backend="bing",
                                         failure_stage="search", failure_type="DDGSException")
            with patch("stage_image_replacements.build_dataset",
                       return_value=approved_records()), \
                 patch.object(image, "process_word", side_effect=failed_process):
                _, data = stage_replacements(root, run_id="backend-diagnostic",
                                             retries=0, retry_delay=0,
                                             rate_limit_delay=0, search_backend="bing")
        for target in data["targets"]:
            self.assertEqual(target["search_client"], "ddgs")
            self.assertEqual(target["search_backend"], "bing")
            self.assertEqual(target["failure_stage"], "search")
            self.assertEqual(target["failure_type"], "DDGSException")
            self.assertEqual(target["candidate_retrieval"]["search_seconds"], 0.4)


if __name__ == "__main__":
    unittest.main()
