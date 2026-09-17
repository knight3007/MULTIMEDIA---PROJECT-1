from __future__ import annotations

import argparse
import base64
import json
import statistics
import subprocess
import time
import wave
from dataclasses import dataclass, field
from pathlib import Path

from collector_common import (
    PROJECT_ROOT, CollectionError, add_common_arguments,
    resolve_project_path, run_cli, validate_common_arguments,
)

JAPANESE_VOCABULARY_PATH = PROJECT_ROOT / "data" / "vocabulary" / "jp.txt"
AUDIO_DIR = PROJECT_ROOT / "data" / "audio" / "jp"
AUDIO_METADATA_DIR = AUDIO_DIR / "_metadata"
WAV_SIGNATURE = b"RIFF"


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
    source: str = "Windows SAPI"
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


def validate_audio(path: Path) -> AudioValidation:
    if not path.exists() or not path.is_file():
        return AudioValidation(ok=False, reason="file does not exist")
    size = path.stat().st_size
    if size == 0:
        return AudioValidation(ok=False, size=size, reason="file is empty")
    if path.suffix.lower() != ".wav":
        return AudioValidation(ok=False, size=size, reason=f"unsupported audio extension: {path.suffix}")
    with path.open("rb") as file:
        header = file.read(12)
    if not header.startswith(WAV_SIGNATURE) or header[8:12] != b"WAVE":
        return AudioValidation(ok=False, size=size, reason="file is not a WAV container")
    try:
        with wave.open(str(path), "rb") as audio:
            frames = audio.getnframes()
            frame_rate = audio.getframerate()
            sample_width = audio.getsampwidth()
            channels = audio.getnchannels()
            if frames <= 0:
                return AudioValidation(ok=False, size=size, reason="WAV has no audio frames")
            if frame_rate <= 0 or sample_width <= 0 or channels <= 0:
                return AudioValidation(ok=False, size=size, reason="WAV has invalid stream parameters")
            duration = frames / float(frame_rate)
    except (wave.Error, EOFError, OSError) as error:
        return AudioValidation(ok=False, size=size, reason=f"WAV decode failed: {error}")
    if duration <= 0:
        return AudioValidation(ok=False, size=size, reason="WAV duration is zero")
    return AudioValidation(ok=True, format="wav", size=size, duration_seconds=duration)


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
    return AUDIO_DIR / f"{stable_audio_stem(index, word, reading)}.wav"


def audio_metadata_path(index: int, word: str, reading: str) -> Path:
    return AUDIO_METADATA_DIR / f"{stable_audio_stem(index, word, reading)}.json"


def synthesize_sapi_wav(reading: str, destination: Path, *, timeout: int) -> str:
    payload = json.dumps(
        {"text": reading, "output": str(destination)},
        ensure_ascii=False,
    )
    script = f"""
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$payload = @'
{payload}
'@ | ConvertFrom-Json
$voice = New-Object -ComObject SAPI.SpVoice
$selected = $null
foreach ($candidate in @($voice.GetVoices())) {{
    $description = $candidate.GetDescription()
    $language = $candidate.GetAttribute('Language')
    if ($description -match 'Japanese' -or $language -match '411') {{
        $selected = $candidate
        break
    }}
}}
if ($null -eq $selected) {{
    throw 'No Japanese SAPI voice installed'
}}
$voice.Voice = $selected
$stream = New-Object -ComObject SAPI.SpFileStream
$stream.Open($payload.output, 3, $false)
try {{
    $voice.AudioOutputStream = $stream
    [void]$voice.Speak($payload.text, 0)
}} finally {{
    $stream.Close()
}}
Write-Output ('VOICE=' + $selected.GetDescription())
"""
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-EncodedCommand",
            encoded,
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "SAPI TTS failed"
        raise CollectionError(detail)
    for line in completed.stdout.splitlines():
        if line.startswith("VOICE="):
            return line.removeprefix("VOICE=").strip()
    return "Windows SAPI Japanese voice"


def write_audio_metadata(result: AudioResult) -> None:
    if result.output is None:
        return
    metadata = {
        "key": result.key,
        "word": result.word,
        "reading": result.reading,
        "audio": str(result.output.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "source": result.source,
        "format": result.audio_format,
        "size": result.size,
        "duration_seconds": result.duration_seconds,
        "status": result.status,
    }
    audio_metadata_path(int(result.key), result.word, result.reading).write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


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
    output = audio_output_path(index, word, reading)
    metadata_path = audio_metadata_path(index, word, reading)
    validation = validate_audio(output)
    if validation.ok:
        result = AudioResult(
            ok=True,
            key=key,
            word=word,
            reading=reading,
            status="cache_hit",
            output=output,
            size=validation.size,
            audio_format=validation.format,
            duration_seconds=validation.duration_seconds,
        )
        if not metadata_path.exists():
            write_audio_metadata(result)
        print("[AUDIO] CACHE HIT")
        print(f"KEY: {key}")
        print(f"WORD: {word}")
        print(f"READING: {reading}")
        print(f"FILE: {output.relative_to(PROJECT_ROOT)}")
        return result

    if output.exists() and not validation.ok:
        output.unlink(missing_ok=True)

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        temporary_path = output.with_name(f"{output.stem}.tmp.wav")
        try:
            temporary_path.unlink(missing_ok=True)
            source = synthesize_sapi_wav(reading, temporary_path, timeout=timeout)
            validation = validate_audio(temporary_path)
            if not validation.ok:
                raise CollectionError(validation.reason or "audio validation failed")
            temporary_path.replace(output)
            result = AudioResult(
                ok=True,
                key=key,
                word=word,
                reading=reading,
                status="success",
                output=output,
                size=validation.size,
                audio_format=validation.format,
                duration_seconds=validation.duration_seconds,
                source=source,
            )
            write_audio_metadata(result)
            print("=" * 40)
            print("[AUDIO]")
            print(f"KEY: {key}")
            print(f"WORD: {word}")
            print(f"READING: {reading}")
            print(f"SOURCE: {source}")
            print(f"OUTPUT: {output.relative_to(PROJECT_ROOT)}")
            print("STATUS: SUCCESS")
            print("=" * 40)
            return result
        except (CollectionError, OSError, subprocess.SubprocessError) as error:
            last_error = error
            temporary_path.unlink(missing_ok=True)
            print("[AUDIO][ERROR]")
            print(f"key: {key}")
            print(f"word: {word}")
            print(f"reading: {reading}")
            print(f"error: {error}")
            print(f"attempt: {attempt + 1}")
            if attempt < retries:
                time.sleep(retry_delay * (attempt + 1))

    error_message = str(last_error) if last_error else "audio generation failed"
    print("[AUDIO] FAILED")
    print(f"KEY: {key}")
    print(f"WORD: {word}")
    print(f"READING: {reading}")
    print(f"ERROR: {error_message}")
    return AudioResult(
        ok=False,
        key=key,
        word=word,
        reading=reading,
        status="failed",
        output=output,
        error=error_message,
    )


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
    parser = argparse.ArgumentParser(description="Collect Japanese vocabulary audio using Windows SAPI.")
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
