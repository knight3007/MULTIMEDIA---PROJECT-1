"""Build the offline vocabulary manifest from source text and production assets."""

import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

from audiocollector import (AUDIO_LOCALE, AUDIO_SOURCE, AUDIO_VOICE,
                            stable_audio_stem, validate_audio)
from imagecollector import sanitize_filename
from semantic_decisions import load_decisions
from validate_vocabulary import validate_sources
from vocabulary_registry import load_registry, validate_registry


OUTPUT_PATH = Path("data/vocabulary/unified_dataset_v1.json")
LANGUAGES = ("en", "jp", "vn")


def safe_asset(root: Path, relative: Path) -> Path:
    """Keep derived asset and metadata references within the project root."""
    resolved_root = root.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(resolved_root):
        raise ValueError(f"Unsafe asset path outside project root: {relative}")
    return path


def read_metadata(path: Path, label: str):
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid {label} metadata {path}: {error}") from error
    if not isinstance(metadata, dict):
        raise ValueError(f"Invalid {label} metadata object: {path}")
    return metadata


def image_record(root: Path, english: str, approved):
    stem = sanitize_filename(english)
    relative = Path("data/image/en") / f"{stem}.jpg"
    metadata_relative = Path("data/image/en/_metadata") / f"{stem}.json"
    image_path = safe_asset(root, relative)
    metadata_path = safe_asset(root, metadata_relative)
    target = approved.get("image_search_intent") if approved else None
    result = {"status": "missing", "path": None, "url": None,
              "source_english": english, "target_search_sense": target,
              "effective_search_query": target,
              "final_search_query": None, "query_provenance": None,
              "provider": None, "ranking": None, "metadata_ref": None,
              "semantic_suitability": "unverified"}
    if not image_path.exists() and not metadata_path.exists():
        return result
    if not image_path.is_file() or not metadata_path.is_file():
        raise ValueError(f"Image or image metadata missing for {english}")
    try:
        with Image.open(image_path) as image:
            if image.format != "JPEG" or image.width < 1 or image.height < 1:
                raise ValueError(f"Invalid JPEG for {english}: {image_path}")
            image.verify()
    except (OSError, UnidentifiedImageError) as error:
        raise ValueError(f"Invalid JPEG for {english}: {error}") from error
    metadata = read_metadata(metadata_path, "image")
    query = metadata.get("search_query")
    if (metadata.get("word") != english or metadata.get("provider") != "duckduckgo"
            or not isinstance(query, str) or not query.strip()):
        raise ValueError(f"Image metadata word/provider/query mismatch for {english}")
    provenance = metadata.get("query_provenance", "model_generated_unreviewed")
    if provenance not in ("model_generated_unreviewed", "human_approved"):
        raise ValueError(f"Invalid image query provenance for {english}")
    mismatch = bool(target and query != target)
    result.update({"status": "needs_review", "path": relative.as_posix(),
                   "effective_search_query": target or query,
                   "final_search_query": query, "query_provenance": provenance,
                   "provider": metadata["provider"],
                   "ranking": metadata.get("image_selection"),
                   "metadata_ref": metadata_relative.as_posix(),
                   "semantic_suitability": "mismatch" if mismatch else "unverified"})
    return result


def audio_record(root: Path, index: int, japanese: str):
    stem = stable_audio_stem(index, japanese, japanese)
    relative = Path("data/audio/jp") / f"{stem}.mp3"
    metadata_relative = Path("data/audio/jp/_metadata") / f"{stem}.json"
    audio_path = safe_asset(root, relative)
    metadata_path = safe_asset(root, metadata_relative)
    result = {"status": "missing", "reading": japanese, "path": None,
              "url": None, "provider": AUDIO_SOURCE, "locale": AUDIO_LOCALE,
              "voice": AUDIO_VOICE.copy(), "format": "mp3",
              "duration_seconds": None, "size_bytes": None,
              "cache_identity": None, "metadata_ref": None}
    if not audio_path.exists() and not metadata_path.exists():
        return result
    if not audio_path.is_file() or not metadata_path.is_file():
        raise ValueError(f"Audio or audio metadata missing for {japanese}")
    validation = validate_audio(audio_path)
    if not validation.ok:
        raise ValueError(f"Invalid production MP3 for {japanese}: {validation.reason}")
    metadata = read_metadata(metadata_path, "audio")
    if (metadata.get("word") != japanese or metadata.get("reading") != japanese
            or metadata.get("audio") != relative.as_posix()
            or metadata.get("source") != AUDIO_SOURCE
            or metadata.get("locale") != AUDIO_LOCALE
            or metadata.get("voice") != AUDIO_VOICE
            or metadata.get("format") != "mp3"
            or metadata.get("size") != validation.size
            or metadata.get("status") not in ("success", "cache_hit")
            or not isinstance(metadata.get("duration_seconds"), (int, float))
            or abs(metadata["duration_seconds"] - validation.duration_seconds) >= 0.02):
        raise ValueError(f"Audio metadata mismatch for {japanese}")
    identity = hashlib.sha256(json.dumps(
        [japanese, AUDIO_SOURCE, AUDIO_LOCALE, AUDIO_VOICE, "mp3"],
        ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()
    result.update({"status": "needs_review", "path": relative.as_posix(),
                   "duration_seconds": validation.duration_seconds,
                   "size_bytes": validation.size, "cache_identity": identity,
                   "metadata_ref": metadata_relative.as_posix()})
    return result


def build_dataset(root: Path):
    paths = {lang: root / "data/vocabulary" / f"{lang}.txt" for lang in LANGUAGES}
    rows, issues = validate_sources(paths)
    if issues:
        raise ValueError("Invalid vocabulary sources: " + "; ".join(issues))
    registry = load_registry(root)
    ids = validate_registry(rows, registry)
    decisions = load_decisions(root, registry)
    records = []
    for index, ((english, japanese, vietnamese), vocab_id) in enumerate(zip(rows, ids), 1):
        approved = decisions["approved"].get(vocab_id)
        context = decisions["context"].get(vocab_id)
        record = {
            "schema_version": 1, "vocab_id": vocab_id, "source_row_index": index,
            "english": english,
            "japanese": {"display": japanese, "reading": japanese,
                         "written_form": context.get("written_form") if context else None},
            "vietnamese": vietnamese,
            "target_sense": approved["target_sense"] if approved else None,
            "part_of_speech": None,
            "usage_note": context.get("usage_note") if context else None,
            "review_status": "approved" if approved else "needs_decision" if context else "unreviewed",
            "decision_provenance": "owner_approved" if approved else None,
            "annotation_status": context.get("annotation_status") if context else None,
            "image": image_record(root, english, approved),
            "audio": audio_record(root, index, japanese),
        }
        records.append(record)
    return {"schema_version": 1, "records": records}


def write_dataset(root: Path):
    dataset = build_dataset(root)
    output = safe_asset(root, OUTPUT_PATH)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8", newline="\n")
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return output, dataset


if __name__ == "__main__":
    try:
        path, data = write_dataset(Path(__file__).resolve().parents[1])
        print(f"Wrote {len(data['records'])} records to {path}")
    except ValueError as error:
        raise SystemExit(f"ERROR: {error}") from error
