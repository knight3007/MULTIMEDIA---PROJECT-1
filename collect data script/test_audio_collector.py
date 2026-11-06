"""Offline contract tests for Japanese Google Translate MP3 collection."""
import contextlib
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import audiocollector as audio


FIXTURE = Path(__file__).parent / "fixtures" / "short-tone.mp3"


class JapaneseMp3Tests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(patch.object(audio, "PROJECT_ROOT", self.root))
        self.enterContext(patch.object(audio, "AUDIO_DIR", self.root / "audio"))
        self.enterContext(patch.object(audio, "AUDIO_METADATA_DIR", self.root / "audio" / "_metadata"))
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        audio.ensure_audio_directories()
        self.word = "\u306d\u3053"

    def test_validator_parses_mp3_frames_and_rejects_fake_or_truncated_audio(self):
        good = self.root / "good.mp3"
        good.write_bytes(FIXTURE.read_bytes())
        result = audio.validate_audio(good)
        self.assertTrue(result.ok, result.reason)
        self.assertEqual(result.format, "mp3")
        self.assertGreater(result.duration_seconds, 0)
        for name, body in (("empty", b""), ("fake", b"ID3" + b"x" * 200),
                           ("truncated", FIXTURE.read_bytes()[:2000])):
            with self.subTest(name=name):
                path = self.root / f"{name}.mp3"
                path.write_bytes(body)
                self.assertFalse(audio.validate_audio(path).ok)
        old_wav = self.root / "old.wav"
        old_wav.write_bytes(b"RIFF" + b"x" * 100)
        self.assertFalse(audio.validate_audio(old_wav).ok)

    def test_gtts_receives_unicode_japanese_text_and_bounded_timeout(self):
        fake = Mock()
        with patch.dict(sys.modules, {"gtts": types.SimpleNamespace(gTTS=fake, gTTSError=RuntimeError)}):
            audio.synthesize_gtts_mp3(self.word, self.root / "speech.mp3", timeout=7)
        fake.assert_called_once_with(text=self.word, lang="ja", tld="com", slow=False, timeout=7)
        fake.return_value.save.assert_called_once_with(str(self.root / "speech.mp3"))

    def test_download_then_cache_hit_preserves_legacy_wav(self):
        legacy = self.root / "audio" / f"{self.word}.wav"
        legacy.write_bytes(b"old asset")

        def synthesize(_reading, destination, **_kwargs):
            destination.write_bytes(FIXTURE.read_bytes())

        with patch.object(audio, "synthesize_gtts_mp3", side_effect=synthesize) as synth:
            first = audio.process_audio_entry(1, self.word, self.word, timeout=5, retries=0, retry_delay=0)
            second = audio.process_audio_entry(1, self.word, self.word, timeout=5, retries=0, retry_delay=0)
        self.assertEqual(first.status, "success")
        self.assertEqual(first.output.name, f"{self.word}.mp3")
        self.assertEqual(second.status, "cache_hit")
        self.assertEqual(legacy.read_bytes(), b"old asset")
        metadata = json.loads(audio.audio_metadata_path(1, self.word, self.word).read_text(encoding="utf-8"))
        self.assertEqual(metadata["source"], "google_translate_gtts")
        self.assertEqual(metadata["format"], "mp3")
        self.assertEqual(metadata["audio"], f"audio/{self.word}.mp3")
        self.assertEqual(metadata["word"], self.word)
        self.assertEqual(metadata["reading"], self.word)
        self.assertEqual(metadata["locale"], "ja")
        self.assertEqual(metadata["voice"], {"tld": "com", "slow": False})
        synth.assert_called_once()

    def test_stale_sapi_metadata_preserves_existing_mp3(self):
        output = audio.audio_output_path(1, self.word, self.word)
        output.write_bytes(FIXTURE.read_bytes())
        metadata = audio.audio_metadata_path(1, self.word, self.word)
        metadata.write_text(json.dumps({"source": "Windows SAPI", "format": "wav"}), encoding="utf-8")

        original = output.read_bytes()
        before_metadata = metadata.read_bytes()
        with patch.object(audio, "synthesize_gtts_mp3") as synth:
            result = audio.process_audio_entry(1, self.word, self.word, timeout=5, retries=0, retry_delay=0)
        self.assertFalse(result.ok)
        self.assertIn("conflict", result.error)
        self.assertEqual(output.read_bytes(), original)
        self.assertEqual(metadata.read_bytes(), before_metadata)
        synth.assert_not_called()

    def test_wrong_duration_metadata_blocks_redownload(self):
        def synthesize(_reading, destination, **_kwargs):
            destination.write_bytes(FIXTURE.read_bytes())

        with patch.object(audio, "synthesize_gtts_mp3", side_effect=synthesize) as synth:
            first = audio.process_audio_entry(1, self.word, self.word, timeout=5, retries=0, retry_delay=0)
            metadata_path = audio.audio_metadata_path(1, self.word, self.word)
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["duration_seconds"] = 999
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
            second = audio.process_audio_entry(1, self.word, self.word, timeout=5, retries=0, retry_delay=0)
        self.assertEqual(first.status, "success")
        self.assertFalse(second.ok)
        self.assertIn("conflict", second.error)
        synth.assert_called_once()

    def test_corrupt_mp3_and_orphan_metadata_are_preserved(self):
        output = audio.audio_output_path(1, self.word, self.word)
        metadata = audio.audio_metadata_path(1, self.word, self.word)
        output.write_bytes(b"corrupt mp3")
        with patch.object(audio, "synthesize_gtts_mp3") as synth:
            first = audio.process_audio_entry(1, self.word, self.word, timeout=5, retries=0, retry_delay=0)
            output.unlink()
            metadata.write_text('{"status":"old"}', encoding="utf-8")
            second = audio.process_audio_entry(1, self.word, self.word, timeout=5, retries=0, retry_delay=0)
        self.assertFalse(first.ok)
        self.assertFalse(second.ok)
        self.assertEqual(metadata.read_text(encoding="utf-8"), '{"status":"old"}')
        synth.assert_not_called()

    def test_metadata_write_failure_does_not_retry_or_overwrite_new_mp3(self):
        def synthesize(_reading, destination, **_kwargs):
            destination.write_bytes(FIXTURE.read_bytes())

        with patch.object(audio, "synthesize_gtts_mp3", side_effect=synthesize) as synth, \
             patch.object(audio, "write_audio_metadata", side_effect=OSError("disk unavailable")):
            first = audio.process_audio_entry(1, self.word, self.word, timeout=5,
                                              retries=2, retry_delay=0)
        output = audio.audio_output_path(1, self.word, self.word)
        self.assertFalse(first.ok)
        self.assertEqual(output.read_bytes(), FIXTURE.read_bytes())
        synth.assert_called_once()
        with patch.object(audio, "synthesize_gtts_mp3") as again:
            second = audio.process_audio_entry(1, self.word, self.word, timeout=5,
                                               retries=0, retry_delay=0)
        self.assertFalse(second.ok)
        again.assert_not_called()

    def test_metadata_write_uses_temporary_file_and_preserves_old_file_on_replace_error(self):
        output = audio.audio_output_path(1, self.word, self.word)
        output.write_bytes(FIXTURE.read_bytes())
        check = audio.validate_audio(output)
        metadata = audio.audio_metadata_path(1, self.word, self.word)
        metadata.write_bytes(b"old metadata")
        result = audio.AudioResult(True, "1", self.word, self.word, "success",
                                   output=output, size=check.size, audio_format="mp3",
                                   duration_seconds=check.duration_seconds)
        with patch.object(Path, "replace", side_effect=OSError("replace failed")):
            with self.assertRaisesRegex(OSError, "replace failed"):
                audio.write_audio_metadata(result)
        self.assertEqual(metadata.read_bytes(), b"old metadata")
        self.assertEqual(list(metadata.parent.glob("*.tmp.json")), [])
    def test_bad_download_does_not_replace_existing_mp3_or_metadata(self):
        output = audio.audio_output_path(1, self.word, self.word)
        original = FIXTURE.read_bytes()
        output.write_bytes(original)
        metadata = audio.audio_metadata_path(1, self.word, self.word)
        metadata.write_text('{"source":"Windows SAPI"}', encoding="utf-8")

        def synthesize(_reading, destination, **_kwargs):
            destination.write_bytes(b"ID3not-really-an-mp3")

        with patch.object(audio, "synthesize_gtts_mp3", side_effect=synthesize):
            result = audio.process_audio_entry(1, self.word, self.word, timeout=5, retries=0, retry_delay=0)
        self.assertFalse(result.ok)
        self.assertEqual(output.read_bytes(), original)
        self.assertEqual(metadata.read_text(encoding="utf-8"), '{"source":"Windows SAPI"}')
        self.assertEqual(list(output.parent.glob("*.tmp.mp3")), [])

    def test_rate_limit_is_reported_without_retry(self):
        class Refused(Exception):
            rsp = types.SimpleNamespace(status_code=429)

        fake = Mock()
        fake.return_value.save.side_effect = Refused("rate limited")
        with patch.dict(sys.modules, {"gtts": types.SimpleNamespace(gTTS=fake, gTTSError=Refused)}):
            with self.assertRaisesRegex(audio.AudioPermanentError, "HTTP 429"):
                audio.synthesize_gtts_mp3(self.word, self.root / "speech.mp3", timeout=5)
        with patch.object(audio, "synthesize_gtts_mp3", side_effect=audio.AudioPermanentError("HTTP 429")) as synth:
            result = audio.process_audio_entry(1, self.word, self.word, timeout=5, retries=2, retry_delay=0)
        self.assertFalse(result.ok)
        synth.assert_called_once()
    def test_transient_failure_retries_then_succeeds(self):
        attempts = 0

        def synthesize(_reading, destination, **_kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise TimeoutError("network timeout")
            destination.write_bytes(FIXTURE.read_bytes())

        with patch.object(audio, "synthesize_gtts_mp3", side_effect=synthesize), \
             patch.object(audio.time, "sleep") as sleep:
            result = audio.process_audio_entry(1, self.word, self.word, timeout=5, retries=1, retry_delay=0.2)
        self.assertTrue(result.ok)
        self.assertEqual(attempts, 2)
        sleep.assert_called_once_with(0.2)

    def test_invalid_filename_fails_one_item_and_batch_continues(self):
        words = self.root / "words.txt"
        words.write_text("CON\n" + self.word + "\n", encoding="utf-8")

        def synthesize(_reading, destination, **_kwargs):
            destination.write_bytes(FIXTURE.read_bytes())

        with patch.object(audio, "synthesize_gtts_mp3", side_effect=synthesize):
            summary = audio.collect_audio(vocabulary_path=words, limit=2, timeout=5,
                                          retries=0, retry_delay=0, rate_limit_delay=0)
        self.assertEqual(summary.total, 2)
        self.assertEqual(summary.success, 1)
        self.assertEqual(len(summary.failed), 1)
        self.assertEqual(summary.results[1].status, "success")

    def test_direct_batch_handles_windows_non_utf8_stdout(self):
        words = self.root / "words.txt"
        words.write_text(self.word + "\n", encoding="utf-8")

        def synthesize(_reading, destination, **_kwargs):
            destination.write_bytes(FIXTURE.read_bytes())

        raw = io.BytesIO()
        stream = io.TextIOWrapper(raw, encoding="cp1252", write_through=True)
        with patch("sys.stdout", stream), patch.object(audio, "synthesize_gtts_mp3", side_effect=synthesize):
            summary = audio.collect_audio(vocabulary_path=words, limit=1, timeout=5,
                                          retries=0, retry_delay=0, rate_limit_delay=0)
        self.assertEqual(summary.success, 1)
        self.assertIn(self.word, raw.getvalue().decode("utf-8"))
    def test_duplicate_words_share_one_mp3(self):
        words = self.root / "words.txt"
        words.write_text(self.word + "\n" + self.word + "\n", encoding="utf-8")

        def synthesize(_reading, destination, **_kwargs):
            destination.write_bytes(FIXTURE.read_bytes())

        with patch.object(audio, "synthesize_gtts_mp3", side_effect=synthesize) as synth:
            summary = audio.collect_audio(vocabulary_path=words, limit=2, timeout=5,
                                          retries=0, retry_delay=0, rate_limit_delay=0)
        self.assertEqual([result.status for result in summary.results], ["success", "cache_hit"])
        synth.assert_called_once()


if __name__ == "__main__":
    unittest.main()
