"""Stage small stable-ID Japanese MP3 batches without touching production audio."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import audiocollector as audio
from collector_common import PROJECT_ROOT, CollectionError, configure_console, run_cli
from validate_vocabulary import validate_sources
from vocabulary_registry import load_registry, validate_registry


STAGING_BASE = Path("baseline/media-staging/audio")
SMOKE_BASE = Path("baseline/gtts-smoke-2026-10-28")


def save_manifest(path: Path, data: dict) -> None:
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8", newline="\n")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def source_records(root: Path) -> dict[str, tuple[int, str, str, str]]:
    paths = {lang: root / "data/vocabulary" / f"{lang}.txt" for lang in ("en", "jp", "vn")}
    rows, issues = validate_sources(paths)
    if issues:
        raise ValueError("Invalid vocabulary: " + "; ".join(issues))
    ids = validate_registry(rows, load_registry(root))
    return {vocab_id: (index, *row) for index, (vocab_id, row) in enumerate(zip(ids, rows), 1)}


def verified_smoke(root: Path, index: int, reading: str) -> tuple[Path, str] | None:
    stem = audio.stable_audio_stem(index, reading, reading)
    source = root / SMOKE_BASE / f"{stem}.mp3"
    metadata = root / SMOKE_BASE / "_metadata" / f"{stem}.json"
    if not source.exists() and not metadata.exists():
        return None
    validation = audio.validate_audio(source)
    if not audio.is_valid_audio_cache(source, metadata, reading, reading, validation):
        return None
    try:
        saved = json.loads(metadata.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None
    if saved.get("key") != str(index):
        return None
    return source, hashlib.sha256(source.read_bytes()).hexdigest()


def stage_audio(root: Path, vocab_ids: list[str], *, run_id: str | None = None,
                resume: bool = False, timeout: int = 20, retries: int = 1,
                retry_delay: float = 2.0, rate_limit_delay: float = 1.0,
                reuse_smoke: bool = True) -> tuple[Path, dict]:
    if (not 1 <= len(vocab_ids) <= 10 or len(set(vocab_ids)) != len(vocab_ids)
            or timeout < 1 or retries < 0
            or not math.isfinite(retry_delay) or retry_delay < 0
            or not math.isfinite(rate_limit_delay) or rate_limit_delay < 0):
        raise ValueError("Select 1–10 unique IDs and finite, nonnegative retry/rate settings")
    if resume and run_id is None:
        raise ValueError("Resume requires a run ID")
    records = source_records(root)
    if any(vocab_id not in records for vocab_id in vocab_ids):
        raise ValueError("Unknown vocabulary ID in audio batch")
    selected = sorted(vocab_ids, key=lambda vocab_id: records[vocab_id][0])
    root = root.resolve()
    if run_id is None:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Unsafe audio staging run ID")
    base = (root / STAGING_BASE).resolve()
    run_dir = (base / run_id).resolve()
    if base != root / STAGING_BASE or run_dir != base / run_id:
        raise ValueError("Audio staging path is redirected")
    manifest_path = run_dir / "run_manifest.json"
    if resume:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (data.get("schema_version") != 1 or data.get("run_id") != run_id
                or data.get("vocab_ids") != selected):
            raise ValueError("Audio staging manifest does not match requested IDs")
    else:
        run_dir.mkdir(parents=True, exist_ok=False)
        data = {"schema_version": 1, "run_id": run_id, "vocab_ids": selected,
                "configuration": {"timeout": timeout, "retries": retries,
                                  "retry_delay": retry_delay,
                                  "rate_limit_delay": rate_limit_delay,
                                  "reuse_smoke": reuse_smoke},
                "entries": []}
        save_manifest(manifest_path, data)

    previous = {entry["vocab_id"]: entry for entry in data["entries"]}
    old_paths = audio.PROJECT_ROOT, audio.AUDIO_DIR, audio.AUDIO_METADATA_DIR
    audio.PROJECT_ROOT, audio.AUDIO_DIR, audio.AUDIO_METADATA_DIR = (
        root, run_dir, run_dir / "_metadata")
    provider_blocked = None
    try:
        audio.ensure_audio_directories()
        entries = []
        for position, vocab_id in enumerate(selected):
            index, english, reading, vietnamese = records[vocab_id]
            stem = audio.stable_audio_stem(index, reading, reading)
            output = run_dir / f"{stem}.mp3"
            metadata = run_dir / "_metadata" / f"{stem}.json"
            relative = output.relative_to(root).as_posix()
            entry = {"vocab_id": vocab_id, "source_row_index": index,
                     "english": english, "japanese_reading": reading,
                     "vietnamese": vietnamese, "mp3_filename": output.name,
                     "mp3_path": relative,
                     "metadata_path": metadata.relative_to(root).as_posix(),
                     "provider": audio.AUDIO_SOURCE, "locale": audio.AUDIO_LOCALE,
                     "voice": audio.AUDIO_VOICE.copy(), "duration_seconds": None,
                     "size_bytes": None, "sha256": None, "status": "failed",
                     "cache_status": "missing", "validation_status": "not_validated",
                     "reused_from": None, "failure": None}
            old = previous.get(vocab_id)
            network_attempted = False
            try:
                if output.exists() or metadata.exists():
                    check = audio.validate_audio(output)
                    if (not old or old.get("status") != "staged"
                            or old.get("mp3_path") != relative
                            or not audio.is_valid_audio_cache(output, metadata, reading, reading, check)
                            or json.loads(metadata.read_text(encoding="utf-8")).get("key") != str(index)
                            or hashlib.sha256(output.read_bytes()).hexdigest() != old.get("sha256")):
                        raise ValueError("existing staged MP3/metadata/hash conflict; preserve asset")
                    entry.update(old)
                    entry["resume_cache_status"] = "cache_hit"
                elif old and old.get("status") == "staged":
                    raise ValueError("previously staged asset is missing; inspect before retry")
                else:
                    smoke = verified_smoke(root, index, reading) if reuse_smoke else None
                    if smoke:
                        source, source_hash = smoke
                        with source.open("rb") as original, output.open("xb") as staged:
                            shutil.copyfileobj(original, staged)
                        result = audio.AudioResult(True, str(index), reading, reading,
                                                   "cache_hit", output=output,
                                                   size=audio.validate_audio(output).size,
                                                   audio_format="mp3",
                                                   duration_seconds=audio.validate_audio(output).duration_seconds)
                        audio.write_audio_metadata(result)
                        entry["cache_status"] = "reused_smoke"
                        entry["reused_from"] = source.relative_to(root).as_posix()
                        if hashlib.sha256(output.read_bytes()).hexdigest() != source_hash:
                            raise ValueError("smoke copy SHA-256 mismatch")
                    elif provider_blocked:
                        raise AudioProviderBlocked(provider_blocked)
                    else:
                        network_attempted = True
                        result = audio.process_audio_entry(
                            index, reading, reading, timeout=timeout, retries=retries,
                            retry_delay=retry_delay)
                        if not result.ok:
                            if "HTTP 403" in (result.error or "") or "HTTP 429" in (result.error or ""):
                                provider_blocked = result.error
                            raise CollectionError(result.error or "audio collection failed")
                        entry["cache_status"] = "downloaded" if result.status == "success" else "cache_hit"
                    check = audio.validate_audio(output)
                    if (not audio.is_valid_audio_cache(output, metadata, reading, reading, check)
                            or json.loads(metadata.read_text(encoding="utf-8")).get("key") != str(index)):
                        raise ValueError("staged MP3/metadata validation failed")
                    entry.update({"status": "staged", "validation_status": "valid_mp3_and_metadata",
                                  "duration_seconds": check.duration_seconds,
                                  "size_bytes": check.size,
                                  "sha256": hashlib.sha256(output.read_bytes()).hexdigest()})
            except (CollectionError, OSError, ValueError) as error:
                entry["failure"] = str(error)
            entries.append(entry)
            data["entries"] = entries + [previous[item] for item in selected[position + 1:]
                                         if item in previous]
            save_manifest(manifest_path, data)
            if network_attempted and not provider_blocked and position < len(selected) - 1 and rate_limit_delay:
                time.sleep(rate_limit_delay)
        data["entries"] = entries
    finally:
        audio.PROJECT_ROOT, audio.AUDIO_DIR, audio.AUDIO_METADATA_DIR = old_paths
    return manifest_path, data


class AudioProviderBlocked(CollectionError):
    """A provider refusal prevents further new requests in this batch."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vocab-id", action="append", required=True,
                        help="Stable ID to stage; repeat for up to 10 IDs")
    parser.add_argument("--run-id", help="Unique run ID; required with --resume")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--retry-delay", type=float, default=2.0)
    parser.add_argument("--rate-limit-delay", type=float, default=1.0)
    parser.add_argument("--no-smoke-reuse", action="store_true")
    args = parser.parse_args(argv)
    path, data = stage_audio(PROJECT_ROOT, args.vocab_id, run_id=args.run_id,
                             resume=args.resume, timeout=args.timeout,
                             retries=args.retries, retry_delay=args.retry_delay,
                             rate_limit_delay=args.rate_limit_delay,
                             reuse_smoke=not args.no_smoke_reuse)
    print(f"Staging manifest: {path}")
    for entry in data["entries"]:
        print(f"{entry['vocab_id']} {entry['japanese_reading']}: {entry['status']}"
              + (f" ({entry['failure']})" if entry["failure"] else ""))
    return 0 if all(entry["status"] == "staged" for entry in data["entries"]) else 1


if __name__ == "__main__":
    configure_console()
    run_cli(main)
