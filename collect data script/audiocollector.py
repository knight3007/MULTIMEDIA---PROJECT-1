from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from collector_common import (
    PROJECT_ROOT, CollectionError, add_common_arguments, configure_console,
    resolve_project_path, run_cli, validate_common_arguments,
)

JAPANESE_VOCABULARY_PATH = PROJECT_ROOT / "data" / "vocabulary" / "jp.txt"
AUDIO_DIR = PROJECT_ROOT / "data" / "audio" / "jp"
AUDIO_METADATA_DIR = AUDIO_DIR / "_metadata"
AUDIO_SOURCE = "google_translate_gtts"
AUDIO_LOCALE = "ja"
AUDIO_VOICE = {"tld": "com", "slow": False}
AUDIO_SCHEMA_VERSION = 1


@dataclass
class AudioValidation:
    ok: bool
    format: str | None = None
    size: int = 0
    duration_seconds: float | None = None
    reason: str | None = None


@dataclass
class AudioResult:
    ok: bool
    key: str
    word: str
    reading: str
    status: str
    output: Path | None = None
    size: int = 0
    audio_format: str | None = None
    duration_seconds: float | None = None
    source: str = AUDIO_SOURCE
    error: str | None = None


@dataclass
class AudioSummary:
    total: int = 0
    success: int = 0
    cache_hit: int = 0
    failed: list[AudioResult] = field(default_factory=list)
    results: list[AudioResult] = field(default_factory=list)

    def add(self, result: AudioResult) -> None:
        self.total += 1
        self.results.append(result)
        if result.ok:
            self.success += 1
        if result.status == "cache_hit":
            self.cache_hit += 1
        if not result.ok:
            self.failed.append(result)


def load_audio_vocabulary(path: Path) -> list[str]:
    if not path.exists():
        raise CollectionError(f"Audio vocabulary file not found: {path}")

    words = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    return [word for word in words if word]


def ensure_audio_directories() -> None:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_METADATA_DIR.mkdir(parents=True, exist_ok=True)


def has_complete_mp3_frames(path: Path) -> bool:
    """Reject a partial final MPEG Layer III frame, which Mutagen may accept."""
    body = path.read_bytes()
    offset = 0
    if body.startswith(b"ID3"):
        if len(body) < 10 or any(byte & 0x80 for byte in body[6:10]):
            return False
        tag_size = (body[6] << 21) | (body[7] << 14) | (body[8] << 7) | body[9]
        offset = 10 + tag_size + (10 if body[5] & 0x10 else 0)
    frames = 0
    mpeg1_bitrates = (0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320)
    mpeg2_bitrates = (0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160)
    sample_rates = (44100, 48000, 32000)
    while offset + 4 <= len(body):
        if len(body) - offset == 128 and body[offset:offset + 3] == b"TAG":
            break
        header = int.from_bytes(body[offset:offset + 4], "big")
        version = (header >> 19) & 3
        layer = (header >> 17) & 3
        bitrate_index = (header >> 12) & 15
        sample_index = (header >> 10) & 3
        if (header & 0xFFE00000) != 0xFFE00000 or version == 1 or layer != 1:
            return False
        if bitrate_index in (0, 15) or sample_index == 3:
            return False
        bitrate = (mpeg1_bitrates if version == 3 else mpeg2_bitrates)[bitrate_index]
        sample_rate = sample_rates[sample_index] >> (0 if version == 3 else 1 if version == 2 else 2)
        frame_size = (144000 if version == 3 else 72000) * bitrate // sample_rate
        frame_size += (header >> 9) & 1
        if frame_size < 4 or offset + frame_size > len(body):
            return False
        offset += frame_size
        frames += 1
    return frames >= 2 and (offset == len(body)
                            or len(body) - offset == 128 and body[offset:offset + 3] == b"TAG")


def validate_audio(path: Path) -> AudioValidation:
    """Parse actual MPEG frames; an extension or ID3 tag alone is insufficient."""
    if not path.is_file():
        return AudioValidation(ok=False, reason="file does not exist")
    size = path.stat().st_size
    if path.suffix.lower() != ".mp3":
        return AudioValidation(ok=False, size=size, reason=f"unsupported audio extension: {path.suffix}")
    if size < 128:
        return AudioValidation(ok=False, size=size, reason="MP3 is empty or truncated")
    try:
        from mutagen import MutagenError
        from mutagen.mp3 import MP3

        info = MP3(path).info
        duration = float(info.length)
        if duration < 0.1 or info.bitrate <= 0 or info.sample_rate <= 0:
            return AudioValidation(ok=False, size=size, reason="MP3 has invalid stream parameters")
        if not has_complete_mp3_frames(path):
            return AudioValidation(ok=False, size=size, reason="MP3 has incomplete or invalid frames")
    except (ImportError, MutagenError, OSError, ValueError) as error:
        return AudioValidation(ok=False, size=size, reason=f"MP3 parse failed: {error}")
    return AudioValidation(ok=True, format="mp3", size=size, duration_seconds=duration)


def stable_audio_stem(index: int, word: str, reading: str) -> str:
    """Preserve the vocabulary text, including Japanese characters, as the name."""
    if (not word or word in {".", ".."} or word.endswith((".", " "))
            or any(char in '<>:"/\\|?*' or ord(char) < 32 for char in word)):
        raise CollectionError(f"Vocabulary cannot be used as an audio filename: {word!r}")
    reserved = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
    reserved.update(f"{prefix}{number}" for prefix in ("COM", "LPT") for number in "123456789¹²³")
    if word.split(".", 1)[0].upper() in reserved:
        raise CollectionError(f"Reserved audio filename: {word!r}")
    return word


def audio_output_path(index: int, word: str, reading: str) -> Path:
    return AUDIO_DIR / f"{stable_audio_stem(index, word, reading)}.mp3"


def audio_metadata_path(index: int, word: str, reading: str) -> Path:
    return AUDIO_METADATA_DIR / f"{stable_audio_stem(index, word, reading)}.json"


class AudioPermanentError(CollectionError):
    """A configuration or provider refusal that should not be retried."""


def synthesize_gtts_mp3(reading: str, destination: Path, *, timeout: int, locale: str = AUDIO_LOCALE) -> None:
    """Download Google Translate speech once; the caller controls retry and cache."""
    try:
        from gtts import gTTS, gTTSError
    except ImportError as error:
        raise AudioPermanentError("gTTS is missing; install requirements-audio.txt") from error
    try:
        if locale not in {"ja", "en"}:
            raise AudioPermanentError(f"Unsupported pronunciation locale: {locale}")
        gTTS(text=reading, lang=locale, tld=AUDIO_VOICE["tld"],
             slow=AUDIO_VOICE["slow"], timeout=timeout).save(str(destination))
    except gTTSError as error:
        status = getattr(getattr(error, "rsp", None), "status_code", None)
        if status in (403, 429):
            raise AudioPermanentError(f"Google Translate refused the request (HTTP {status})") from error
        raise CollectionError(f"gTTS request failed: {error}") from error


def audio_metadata_record(result: AudioResult) -> dict:
    return {
        "schema_version": AUDIO_SCHEMA_VERSION,
        "key": result.key,
        "word": result.word,
        "reading": result.reading,
        "locale": AUDIO_LOCALE,
        "voice": AUDIO_VOICE.copy(),
        "audio": str(result.output.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "source": result.source,
        "format": result.audio_format,
        "size": result.size,
        "duration_seconds": result.duration_seconds,
        "status": result.status,
    }


def is_valid_audio_cache(output: Path, metadata_path: Path, word: str,
                         reading: str, validation: AudioValidation) -> bool:
    if not validation.ok or not metadata_path.is_file():
        return False
    try:
        saved = json.loads(metadata_path.read_text(encoding="utf-8"))
        expected_path = str(output.relative_to(PROJECT_ROOT)).replace("\\", "/")
        return (isinstance(saved, dict)
                and saved.get("schema_version") == AUDIO_SCHEMA_VERSION
                and saved.get("word") == word and saved.get("reading") == reading
                and saved.get("locale") == AUDIO_LOCALE and saved.get("voice") == AUDIO_VOICE
                and saved.get("source") == AUDIO_SOURCE and saved.get("format") == "mp3"
                and saved.get("audio") == expected_path
                and saved.get("size") == validation.size
                and isinstance(saved.get("duration_seconds"), (int, float))
                and abs(saved["duration_seconds"] - validation.duration_seconds) < 0.02
                and saved.get("status") in ("success", "cache_hit"))
    except (OSError, ValueError, UnicodeError):
        return False


def write_audio_metadata(result: AudioResult) -> None:
    if result.output is None:
        return
    target = audio_metadata_path(int(result.key), result.word, result.reading)
    temporary = target.with_name(f".{target.stem}.{uuid4().hex}.tmp.json")
    try:
        temporary.write_text(json.dumps(audio_metadata_record(result), ensure_ascii=False, indent=2),
                             encoding="utf-8")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def process_audio_entry(
    index: int,
    word: str,
    reading: str,
    *,
    timeout: int,
    retries: int,
    retry_delay: float,
) -> AudioResult:
    key = str(index)
    try:
        output = audio_output_path(index, word, reading)
        metadata_path = audio_metadata_path(index, word, reading)
    except CollectionError as error:
        return AudioResult(ok=False, key=key, word=word, reading=reading,
                           status="failed", error=str(error))

    validation = validate_audio(output)
    if is_valid_audio_cache(output, metadata_path, word, reading, validation):
        print(f"[AUDIO] CACHE HIT: {word} -> {output.relative_to(PROJECT_ROOT)}")
        return AudioResult(ok=True, key=key, word=word, reading=reading,
                           status="cache_hit", output=output, size=validation.size,
                           audio_format="mp3", duration_seconds=validation.duration_seconds)

    if output.exists() or metadata_path.exists():
        return AudioResult(ok=False, key=key, word=word, reading=reading,
                           status="failed", output=output,
                           error="existing MP3/metadata conflict; preserve asset for review")

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        temporary = output.with_name(f".{output.stem}.{uuid4().hex}.tmp.mp3")
        try:
            synthesize_gtts_mp3(reading, temporary, timeout=timeout)
            validation = validate_audio(temporary)
            if not validation.ok:
                raise CollectionError(validation.reason or "MP3 validation failed")
            temporary.replace(output)
            result = AudioResult(ok=True, key=key, word=word, reading=reading,
                                 status="success", output=output, size=validation.size,
                                 audio_format="mp3", duration_seconds=validation.duration_seconds)
            write_audio_metadata(result)
            print(f"[AUDIO] SUCCESS: {word} -> {output.relative_to(PROJECT_ROOT)}")
            return result
        except (AudioPermanentError, CollectionError, OSError) as error:
            last_error = error
            print(f"[AUDIO][ERROR] {word}: {error} (attempt {attempt + 1}/{retries + 1})")
            if isinstance(error, AudioPermanentError) or output.exists():
                break
            if attempt < retries:
                time.sleep(retry_delay * (attempt + 1))
        finally:
            temporary.unlink(missing_ok=True)

    return AudioResult(ok=False, key=key, word=word, reading=reading,
                       status="failed", output=output,
                       error=str(last_error) if last_error else "audio download failed")


def print_audio_summary(summary: AudioSummary) -> None:
    print()
    print("10 KEY AUDIO TEST" if summary.total == 10 else "AUDIO TEST")
    print("------------------")
    print(f"Total: {summary.total}")
    print(f"Success: {summary.success}")
    print(f"Cache hit: {summary.cache_hit}")
    print(f"Failed: {len(summary.failed)}")

    valid_sizes = [result.size for result in summary.results if result.ok and result.size > 0]
    if valid_sizes:
        print()
        print(f"Average audio size: {statistics.mean(valid_sizes):.0f}")
        print(f"Min audio size: {min(valid_sizes)}")
        print(f"Max audio size: {max(valid_sizes)}")

    if summary.failed:
        print()
        print("Failures:")
        for result in summary.failed:
            print(f"- key: {result.key}")
            print(f"  word: {result.word}")
            print(f"  reading: {result.reading}")
            print(f"  error: {result.error or 'unknown error'}")


def collect_audio(
    *,
    vocabulary_path: Path,
    limit: int,
    timeout: int,
    retries: int,
    retry_delay: float,
    rate_limit_delay: float,
) -> AudioSummary:
    configure_console()
    ensure_audio_directories()
    words = load_audio_vocabulary(vocabulary_path)
    words_to_process = words[:limit]
    summary = AudioSummary()

    for offset, word in enumerate(words_to_process, start=1):
        reading = word
        result = process_audio_entry(
            offset,
            word,
            reading,
            timeout=timeout,
            retries=retries,
            retry_delay=retry_delay,
        )
        summary.add(result)
        if result.status != "cache_hit" and offset < len(words_to_process):
            time.sleep(rate_limit_delay)

    print_audio_summary(summary)
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download Japanese vocabulary MP3 using Google Translate gTTS.")
    add_common_arguments(parser)
    parser.add_argument("--vocabulary", "--audio-vocabulary", dest="vocabulary", type=Path,
                        default=JAPANESE_VOCABULARY_PATH, help="Japanese vocabulary/reading file.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    validate_common_arguments(args)
    summary = collect_audio(
        vocabulary_path=resolve_project_path(args.vocabulary),
        limit=args.limit, timeout=args.timeout, retries=args.retries,
        retry_delay=args.retry_delay, rate_limit_delay=args.rate_limit_delay,
    )
    return 0 if not summary.failed else 1


if __name__ == "__main__":
    run_cli(main)
