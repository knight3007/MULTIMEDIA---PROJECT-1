"""Offline tests for stable-ID Japanese audio staging."""

import contextlib
import hashlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import audiocollector as audio
from collector_common import PROJECT_ROOT
from stage_japanese_audio import stage_audio


FIXTURE = Path(__file__).parent / "fixtures/short-tone.mp3"
SMOKE = Path("baseline/gtts-smoke-2026-10-28")


class StageJapaneseAudioTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        source = self.root / "data/vocabulary"
        source.mkdir(parents=True)
        for name in ("en.txt", "jp.txt", "vn.txt", "id_registry_v1.json"):
            shutil.copyfile(PROJECT_ROOT / "data/vocabulary" / name, source / name)
        self.dataset = source / "unified_dataset_v1.json"
        self.dataset.write_bytes(b"old production dataset")

    def _smoke(self, reading, index):
        path = self.root / SMOKE / f"{reading}.mp3"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(FIXTURE.read_bytes())
        check = audio.validate_audio(path)
        metadata = {"schema_version": 1, "key": str(index), "word": reading,
                    "reading": reading, "locale": "ja", "voice": audio.AUDIO_VOICE,
                    "audio": (SMOKE / f"{reading}.mp3").as_posix(),
                    "source": audio.AUDIO_SOURCE, "format": "mp3",
                    "size": check.size, "duration_seconds": check.duration_seconds,
                    "status": "success"}
        meta = path.parent / "_metadata" / f"{reading}.json"
        meta.parent.mkdir(parents=True, exist_ok=True)
        meta.write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")
        return path, meta

    def test_only_selected_ids_stage_unicode_files_and_record_partial_failure(self):
        def synth(reading, destination, **_kwargs):
            if reading == "バナナ":
                raise audio.AudioPermanentError("HTTP 429")
            destination.write_bytes(FIXTURE.read_bytes())

        with patch.object(audio, "synthesize_gtts_mp3", side_effect=synth):
            path, result = stage_audio(self.root, ["vocab-000001", "vocab-000002"],
                                       run_id="pilot-a", timeout=5, retries=1,
                                       retry_delay=0, rate_limit_delay=0,
                                       reuse_smoke=False)
        apple, banana = result["entries"]
        self.assertEqual(apple["vocab_id"], "vocab-000001")
        self.assertEqual(apple["source_row_index"], 1)
        self.assertEqual(apple["english"], "apple")
        self.assertEqual(apple["japanese_reading"], "りんご")
        self.assertEqual(apple["status"], "staged")
        self.assertEqual(apple["cache_status"], "downloaded")
        self.assertTrue((path.parent / "りんご.mp3").is_file())
        self.assertEqual(apple["sha256"], hashlib.sha256(FIXTURE.read_bytes()).hexdigest())
        self.assertEqual(banana["status"], "failed")
        self.assertIn("HTTP 429", banana["failure"])
        self.assertFalse((path.parent / "バナナ.mp3").exists())
        metadata = json.loads((path.parent / "_metadata/りんご.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["audio"], "baseline/media-staging/audio/pilot-a/りんご.mp3")
        self.assertEqual(metadata["locale"], "ja")
        self.assertEqual(self.dataset.read_bytes(), b"old production dataset")
        self.assertFalse((self.root / "data/audio/jp").exists())

    def test_verified_smoke_reuse_and_resume_cache_preserve_original_bytes(self):
        source, meta = self._smoke("りんご", 1)
        before = (source.read_bytes(), meta.read_bytes())
        with patch.object(audio, "synthesize_gtts_mp3") as synth:
            path, first = stage_audio(self.root, ["vocab-000001"], run_id="pilot-b",
                                      timeout=5, retries=0, retry_delay=0,
                                      rate_limit_delay=0)
            with self.assertRaises(FileExistsError):
                stage_audio(self.root, ["vocab-000001"], run_id="pilot-b",
                            timeout=5, retries=0, retry_delay=0,
                            rate_limit_delay=0)
            second_path, second = stage_audio(self.root, ["vocab-000001"],
                                              run_id="pilot-b", resume=True,
                                              timeout=5, retries=0, retry_delay=0,
                                              rate_limit_delay=0)
        self.assertEqual(path, second_path)
        self.assertEqual(first["entries"][0]["cache_status"], "reused_smoke")
        self.assertEqual(first["entries"][0]["reused_from"], (SMOKE / "りんご.mp3").as_posix())
        self.assertEqual(second["entries"][0]["cache_status"], "reused_smoke")
        self.assertEqual(second["entries"][0]["resume_cache_status"], "cache_hit")
        self.assertEqual((source.read_bytes(), meta.read_bytes()), before)
        self.assertEqual((path.parent / "りんご.mp3").read_bytes(), before[0])
        synth.assert_not_called()

    def test_resume_rejects_corrupt_audio_or_stale_metadata_without_overwrite(self):
        def synth(_reading, destination, **_kwargs):
            destination.write_bytes(FIXTURE.read_bytes())

        with patch.object(audio, "synthesize_gtts_mp3", side_effect=synth):
            path, _ = stage_audio(self.root, ["vocab-000001"], run_id="pilot-c",
                                  timeout=5, retries=0, retry_delay=0, rate_limit_delay=0,
                                  reuse_smoke=False)
        output = path.parent / "りんご.mp3"
        metadata = path.parent / "_metadata/りんご.json"
        output.write_bytes(b"corrupt")
        old_meta = metadata.read_bytes()
        with patch.object(audio, "synthesize_gtts_mp3") as synth_mock:
            _, result = stage_audio(self.root, ["vocab-000001"], run_id="pilot-c",
                                    resume=True, timeout=5, retries=0,
                                    retry_delay=0, rate_limit_delay=0)
        self.assertEqual(result["entries"][0]["status"], "failed")
        self.assertEqual(output.read_bytes(), b"corrupt")
        self.assertEqual(metadata.read_bytes(), old_meta)
        synth_mock.assert_not_called()
        with patch.object(audio, "synthesize_gtts_mp3", side_effect=synth):
            other, _ = stage_audio(self.root, ["vocab-000001"], run_id="pilot-c2",
                                   timeout=5, retries=0, retry_delay=0, rate_limit_delay=0,
                                   reuse_smoke=False)
        other_meta = other.parent / "_metadata/りんご.json"
        other_meta.unlink()
        old_audio = (other.parent / "りんご.mp3").read_bytes()
        with patch.object(audio, "synthesize_gtts_mp3") as synth_mock:
            _, result = stage_audio(self.root, ["vocab-000001"], run_id="pilot-c2",
                                    resume=True, timeout=5, retries=0,
                                    retry_delay=0, rate_limit_delay=0)
        self.assertEqual(result["entries"][0]["status"], "failed")
        self.assertEqual((other.parent / "りんご.mp3").read_bytes(), old_audio)
        synth_mock.assert_not_called()

    def test_provider_429_stops_later_new_requests(self):
        def synth(reading, destination, **_kwargs):
            if reading == "バナナ":
                raise audio.AudioPermanentError("HTTP 429")
            destination.write_bytes(FIXTURE.read_bytes())

        with patch.object(audio, "synthesize_gtts_mp3", side_effect=synth) as calls:
            _, result = stage_audio(self.root, ["vocab-000001", "vocab-000002",
                                                "vocab-000003"], run_id="pilot-limit",
                                    timeout=5, retries=0, retry_delay=0,
                                    rate_limit_delay=0, reuse_smoke=False)
        self.assertEqual([entry["status"] for entry in result["entries"]],
                         ["staged", "failed", "failed"])
        self.assertEqual(calls.call_count, 2)
        self.assertIn("HTTP 429", result["entries"][2]["failure"])

    def test_rate_delay_applies_after_failed_network_attempt(self):
        def synth(reading, destination, **_kwargs):
            if reading == "りんご":
                raise CollectionError("transient failure")
            destination.write_bytes(FIXTURE.read_bytes())

        from collector_common import CollectionError
        with patch.object(audio, "synthesize_gtts_mp3", side_effect=synth), \
             patch("stage_japanese_audio.time.sleep") as sleep:
            _, result = stage_audio(self.root, ["vocab-000001", "vocab-000002"],
                                    run_id="pilot-delay", timeout=5, retries=0,
                                    retry_delay=0, rate_limit_delay=0.4,
                                    reuse_smoke=False)
        self.assertEqual([entry["status"] for entry in result["entries"]],
                         ["failed", "staged"])
        sleep.assert_called_once_with(0.4)

    def test_stale_smoke_metadata_falls_back_to_new_download(self):
        source, meta = self._smoke("りんご", 1)
        saved = json.loads(meta.read_text(encoding="utf-8"))
        saved["reading"] = "wrong"
        meta.write_text(json.dumps(saved), encoding="utf-8")
        before = (source.read_bytes(), meta.read_bytes())

        def synth(_reading, destination, **_kwargs):
            destination.write_bytes(FIXTURE.read_bytes())

        with patch.object(audio, "synthesize_gtts_mp3", side_effect=synth) as call:
            _, result = stage_audio(self.root, ["vocab-000001"], run_id="pilot-d",
                                    timeout=5, retries=0, retry_delay=0,
                                    rate_limit_delay=0)
        self.assertEqual(result["entries"][0]["cache_status"], "downloaded")
        self.assertEqual((source.read_bytes(), meta.read_bytes()), before)
        call.assert_called_once()

    def test_invalid_selection_and_run_id_fail_before_writes(self):
        for ids, run_id in ((["vocab-999999"], "unknown"),
                            (["vocab-000001", "vocab-000001"], "duplicate"),
                            (["vocab-000001"], "../unsafe"),
                            ([], "empty")):
            with self.subTest(ids=ids, run_id=run_id):
                with self.assertRaises(ValueError):
                    stage_audio(self.root, ids, run_id=run_id)
        self.assertFalse((self.root / "baseline/media-staging/audio").exists())


if __name__ == "__main__":
    unittest.main()
