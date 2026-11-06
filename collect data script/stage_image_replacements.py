"""Stage only the two owner-approved replacement images; never publish them."""

import argparse
import json
import math
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse
from uuid import uuid4

from PIL import Image

import imagecollector as image
from collector_common import PROJECT_ROOT
from dataset_builder import build_dataset, safe_asset


STAGING_BASE = Path("baseline/media-staging/images")
TARGETS = {"vocab-000004": ("rice", "cooked rice"),
           "vocab-000009": ("chicken", "chicken meat")}


def save_run_manifest(path: Path, data: dict) -> None:
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8", newline="\n")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def stage_replacements(root: Path, *, run_id: str | None = None,
                       vocab_id: str | None = None,
                       curated_image_url: str | None = None,
                       curated_source_page_url: str | None = None,
                       timeout: int = 8, retries: int = 1,
                       retry_delay: float = 1.0, page_size: int = 3,
                       rate_limit_delay: float = 1.0,
                       siglip_device: str = "auto", siglip_dtype: str = "auto",
                       search_backend: str = "auto"):
    if (timeout < 1 or retries < 0 or page_size < 1
            or not math.isfinite(retry_delay) or retry_delay < 0
            or not math.isfinite(rate_limit_delay) or rate_limit_delay < 0):
        raise ValueError("timeout/page-size must be positive; retries/delays nonnegative")
    if search_backend not in {"auto", "duckduckgo", "bing"}:
        raise ValueError("Unsupported image search backend")
    if vocab_id is not None and vocab_id not in TARGETS:
        raise ValueError(f"Unsupported image staging target: {vocab_id}")
    curated = curated_image_url is not None or curated_source_page_url is not None
    if curated and (vocab_id != "vocab-000009"
                    or not image.is_supported_remote_url(curated_image_url)
                    or not image.is_supported_remote_url(curated_source_page_url)):
        raise ValueError("Curated source requires chicken ID and both remote URLs")
    selected_targets = list(TARGETS.items()) if vocab_id is None else [(vocab_id, TARGETS[vocab_id])]
    root = root.resolve()
    records = {record["vocab_id"]: record for record in build_dataset(root)["records"]}
    for vocab_id, (word, query) in selected_targets:
        record = records.get(vocab_id)
        if (not record or record["english"] != word or record["review_status"] != "approved"
                or record["target_sense"] != query
                or record["image"]["effective_search_query"] != query):
            raise ValueError(f"Missing approved staging target: {vocab_id}")

    if run_id is None:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Unsafe staging run ID")
    base = safe_asset(root, STAGING_BASE)
    run_dir = safe_asset(root, STAGING_BASE / run_id)
    if base != root / STAGING_BASE:
        raise ValueError("Staging base is redirected by a link")
    if not run_dir.is_relative_to(base) or run_dir == base:
        raise ValueError("Staging directory escapes the staging base")
    run_dir.mkdir(parents=True, exist_ok=False)
    manifest_path = run_dir / "run_manifest.json"
    result = {"schema_version": 1, "run_id": run_id,
              "purpose": "owner_approved_image_replacement_review",
              "configuration": {"timeout": timeout, "retries": retries,
                                "retry_delay": retry_delay, "page_size": page_size,
                                "rate_limit_delay": rate_limit_delay,
                                "search_backend": search_backend,
                                "curated_image_url": curated_image_url,
                                "curated_source_page_url": curated_source_page_url,
                                "siglip_model": image.DEFAULT_SIGLIP_MODEL,
                                "siglip_device": siglip_device,
                                "siglip_dtype": siglip_dtype},
              "targets": []}
    save_run_manifest(manifest_path, result)

    old_dirs = image.IMAGE_DIR, image.METADATA_DIR, image.CANDIDATE_CACHE_DIR
    image.IMAGE_DIR = run_dir
    image.METADATA_DIR = run_dir / "_metadata"
    image.CANDIDATE_CACHE_DIR = run_dir / "_candidates"
    try:
        image.ensure_directories()
        scorer = image.LazySiglipScorer(SimpleNamespace(
            siglip_model=image.DEFAULT_SIGLIP_MODEL,
            siglip_device=siglip_device, siglip_dtype=siglip_dtype))
        for offset, (vocab_id, (word, query)) in enumerate(selected_targets):
            source = records[vocab_id]
            client = "curated_direct" if curated else "ddgs"
            backend = "curated_direct" if curated else search_backend
            provider = "curated_direct" if curated else image.IMAGE_PROVIDER
            entry = {"vocab_id": vocab_id, "source_row_index": source["source_row_index"]
                     if "source_row_index" in source else int(vocab_id[-6:]),
                     "english": word, "japanese_reading": source["japanese"]["reading"],
                     "vietnamese": source["vietnamese"],
                     "target_sense": source["target_sense"], "effective_query": query,
                     "query_provenance": "human_approved", "provider": provider,
                     "search_client": client, "search_backend": backend,
                     "status": "failed", "approval_status": "pending_human_review",
                     "candidate_retrieval": None, "selected_result": None,
                     "siglip_selection": None, "staged_image_path": None,
                     "staged_metadata_path": None, "dimensions": None,
                     "validation_status": "not_downloaded", "failure": None,
                     "failure_stage": None, "failure_type": None}
            options = {}
            if curated:
                options["search_batch_override"] = image.ImageSearchBatch(
                    [{"image_url": curated_image_url,
                      "source_page_url": curated_source_page_url,
                      "title": "Curated source file page",
                      "provider": provider,
                      "source": urlparse(curated_source_page_url).hostname,
                      "search_client": client, "search_backend": backend}],
                    raw_count=1, duration_seconds=0.0, backend=backend)
            collected = image.process_word(
                word, query, timeout=timeout, retries=retries, retry_delay=retry_delay,
                page_size=page_size, scorer=scorer,
                siglip_model=image.DEFAULT_SIGLIP_MODEL,
                query_provenance="human_approved", search_backend=search_backend,
                **options)
            entry["candidate_retrieval"] = {
                "raw_results": collected.search_result_count,
                "valid_results": collected.valid_candidate_count,
                "downloaded_candidates": collected.candidate_count,
                "selected_image_url": collected.selected_image,
                "search_seconds": collected.search_seconds}
            if collected.ok and collected.status == "downloaded":
                staged = run_dir / f"{word}.jpg"
                metadata_path = run_dir / "_metadata" / f"{word}.json"
                try:
                    with Image.open(staged) as opened:
                        if opened.format != "JPEG" or opened.width < 1 or opened.height < 1:
                            raise ValueError("staged file is not a valid JPEG")
                        dimensions = [opened.width, opened.height]
                        opened.verify()
                    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                    if not isinstance(metadata, dict):
                        raise ValueError("staged metadata is not an object")
                    selection = metadata.get("image_selection")
                    if (metadata.get("word") != word
                            or metadata.get("search_query") != query
                            or metadata.get("query_provenance") != "human_approved"
                            or metadata.get("provider") != provider
                            or (backend != "auto" and
                                (metadata.get("search_client") != client or
                                 metadata.get("search_backend") != backend))
                            or metadata.get("image_url") != collected.selected_image
                            or not isinstance(selection, dict)
                            or selection.get("method") != "siglip2"
                            or not isinstance(selection.get("score"), (int, float))):
                        raise ValueError("staged metadata/query/SigLIP mismatch")
                    entry.update({"status": "staged", "staged_image_path":
                                  staged.relative_to(root).as_posix(),
                                  "staged_metadata_path": metadata_path.relative_to(root).as_posix(),
                                  "dimensions": dimensions,
                                  "validation_status": "valid_jpeg_and_metadata",
                                  "selected_result": {key: metadata.get(key) for key in
                                                      ("image_url", "source_page_url", "title",
                                                       "width", "height", "result_source")},
                                  "siglip_selection": selection})
                except (OSError, ValueError, json.JSONDecodeError) as error:
                    entry.update({"validation_status": "invalid",
                                  "failure": f"staged validation failed: {error}",
                                  "failure_stage": "validation",
                                  "failure_type": type(error).__name__})
                    if staged.exists():
                        entry["staged_image_path"] = staged.relative_to(root).as_posix()
                    if metadata_path.exists():
                        entry["staged_metadata_path"] = metadata_path.relative_to(root).as_posix()
            else:
                entry["failure"] = collected.reason or f"unexpected collection status: {collected.status}"
                entry["failure_stage"] = collected.failure_stage
                entry["failure_type"] = collected.failure_type
            result["targets"].append(entry)
            save_run_manifest(manifest_path, result)
            if offset < len(selected_targets) - 1 and rate_limit_delay:
                time.sleep(rate_limit_delay)
    finally:
        image.IMAGE_DIR, image.METADATA_DIR, image.CANDIDATE_CACHE_DIR = old_dirs
    return manifest_path, result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--retry-delay", type=float, default=1.0)
    parser.add_argument("--page-size", type=int, default=3)
    parser.add_argument("--rate-limit-delay", type=float, default=1.0)
    parser.add_argument("--search-backend", choices=("auto", "duckduckgo", "bing"),
                        default="auto")
    parser.add_argument("--vocab-id", help="Stage only one approved replacement ID")
    parser.add_argument("--curated-image-url", help="Direct image URL with separately verified reuse rights")
    parser.add_argument("--curated-source-page-url", help="File page showing those rights")
    parser.add_argument("--siglip-device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--siglip-dtype", choices=("auto", "float16", "bfloat16", "float32"),
                        default="auto")
    args = parser.parse_args(argv)
    path, data = stage_replacements(PROJECT_ROOT, **vars(args))
    print(f"Staging manifest: {path}")
    for entry in data["targets"]:
        print(f"{entry['vocab_id']} {entry['english']}: {entry['status']}"
              + (f" ({entry['failure']})" if entry["failure"] else ""))
    return 0 if all(entry["status"] == "staged" for entry in data["targets"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
