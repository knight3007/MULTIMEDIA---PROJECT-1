"""Stage up to ten production-missing vocabulary images per isolated run."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from PIL import Image

import imagecollector as image
from collector_common import PROJECT_ROOT
from dataset_builder import build_dataset, safe_asset
from query_generator import (DEFAULT_QWEN_MODEL, QwenQueryGenerator,
                             QueryGenerationError, normalize_query, prepare_queries)
from semantic_decisions import load_decisions, select_effective_query
from stage_image_replacements import STAGING_BASE, save_run_manifest
from vocabulary_registry import ID_PATTERN, load_registry


QUERY_CACHE = Path("baseline/media-staging/image-queries/generated_qwen_full_v1.json")
VERB_CORRECTION = (
    "The input is an action verb, not an object. Output a short image search phrase "
    "showing a person visibly performing the action. Examples: Input: run -> Query: "
    "person running. Input: read -> Query: person reading a book. Never output "
    "verb, action, object, icon or explanation. Use only lowercase English words."
)


def prepare_staging_queries(words: list[str], prefix_path: Path, sparse_path: Path,
                            batch_size: int = 2) -> tuple[list[str | None], dict[int, str]]:
    """Keep the validated Qwen prefix and checkpoint later per-word failures."""
    if prefix_path.exists():
        prefix_doc = json.loads(prefix_path.read_text(encoding="utf-8"))
        count = len(prefix_doc["records"])
    else:
        count = 0
    prefix = prepare_queries(words, limit=max(1, count), model_name=DEFAULT_QWEN_MODEL,
                             batch_size=batch_size, cache_path=prefix_path)
    prefix_doc = json.loads(prefix_path.read_text(encoding="utf-8"))
    count = len(prefix)
    identity = {"schema_version": 1, "model": DEFAULT_QWEN_MODEL,
                "vocabulary_signature": prefix_doc["signature"],
                "prefix_count": count,
                "prefix_sha256": hashlib.sha256(prefix_path.read_bytes()).hexdigest()}
    if sparse_path.exists():
        sparse = json.loads(sparse_path.read_text(encoding="utf-8"))
        if any(sparse.get(key) != value for key, value in identity.items()):
            raise ValueError("Sparse Qwen staging cache does not match canonical prefix")
        saved = sparse.get("records")
        if not isinstance(saved, list) or len(saved) > len(words) - count:
            raise ValueError("Invalid sparse Qwen record count")
        for offset, record in enumerate(saved):
            index = count + offset
            if (record.get("source_row_index") != index + 1
                    or record.get("word") != words[index]
                    or record.get("status") not in {"generated", "failed"}):
                raise ValueError("Sparse Qwen cache row mismatch")
            if record["status"] == "generated":
                if normalize_query(record.get("query")) != record["query"]:
                    raise ValueError("Invalid sparse Qwen query")
            elif not isinstance(record.get("failure"), str) or not record["failure"]:
                raise ValueError("Sparse Qwen failure lacks evidence")
    else:
        sparse = {**identity, "records": []}

    if count + len(sparse["records"]) < len(words):
        generator = QwenQueryGenerator(DEFAULT_QWEN_MODEL, batch_size=batch_size)
        try:
            while count + len(sparse["records"]) < len(words):
                start = count + len(sparse["records"])
                batch = words[start:start + batch_size]
                try:
                    generated = generator.generate_batch(batch)
                    outcomes = [(normalize_query(query), None) for query in generated]
                except QueryGenerationError as error:
                    if "load failed" in str(error):
                        raise
                    outcomes = []
                    for word in batch:
                        try:
                            outcomes.append((normalize_query(generator.generate(word)), None))
                        except QueryGenerationError as single_error:
                            if "load failed" in str(single_error):
                                raise
                            outcomes.append((None, str(single_error)))
                if len(outcomes) != len(batch):
                    raise ValueError("Qwen result count mismatch")
                for offset, (query, failure) in enumerate(outcomes):
                    sparse["records"].append({"source_row_index": start + offset + 1,
                                              "word": batch[offset],
                                              "status": "generated" if query else "failed",
                                              "query": query, "failure": failure})
                    save_run_manifest(sparse_path, sparse)
                print(f"[QWEN] staging cache {count + len(sparse['records'])}/{len(words)}")
        finally:
            generator.close()
    queries = prefix + [item["query"] for item in sparse["records"]]
    errors = {count + offset: item["failure"] for offset, item in enumerate(sparse["records"])
              if item["status"] == "failed"}
    return queries, errors


def repair_failed_staging_queries(words: list[str], prefix_path: Path,
                                  sparse_path: Path) -> list[int]:
    """Retry rejected verb queries with the same Qwen model and a visual correction."""
    _, errors = prepare_staging_queries(words, prefix_path, sparse_path)
    if not errors:
        return []
    sparse = json.loads(sparse_path.read_text(encoding="utf-8"))
    prefix_count = sparse["prefix_count"]
    repaired = []
    generator = QwenQueryGenerator(DEFAULT_QWEN_MODEL)
    try:
        for index in sorted(errors):
            if "verb" not in errors[index].lower():
                continue
            item = sparse["records"][index - prefix_count]
            try:
                generator._load()
                raw, ended = generator._generate_raw([words[index]],
                                                     correction=VERB_CORRECTION)[0]
                if not ended:
                    raise QueryGenerationError("corrected query reached token limit without EOS")
                query = normalize_query(raw)
            except QueryGenerationError as error:
                item["correction_failure"] = str(error)
            else:
                item.update(status="generated", query=query, failure=None,
                            prior_failure=errors[index],
                            generation_method="qwen_corrected_verb_prompt",
                            correction_prompt=VERB_CORRECTION,
                            corrected_raw_output=raw)
                repaired.append(index + 1)
            save_run_manifest(sparse_path, sparse)
    finally:
        generator.close()
    return repaired


def choose_targets(dataset: dict, vocab_ids: list[str], model_queries: list[str],
                   decisions: dict, query_errors: dict[int, str] | None = None) -> list[dict]:
    """Resolve canonical words and query precedence without changing decisions."""
    records = dataset["records"]
    if (not 1 <= len(vocab_ids) <= 10 or len(set(vocab_ids)) != len(vocab_ids)
            or len(model_queries) != len(records)):
        raise ValueError("Choose 1–10 distinct IDs with one model query per canonical record")
    by_id = {record["vocab_id"]: (index, record) for index, record in enumerate(records)}
    selected = []
    for vocab_id in vocab_ids:
        if not isinstance(vocab_id, str) or not ID_PATTERN.fullmatch(vocab_id) or vocab_id not in by_id:
            raise ValueError(f"Unknown or invalid vocabulary ID: {vocab_id!r}")
        index, record = by_id[vocab_id]
        if record["image"]["path"] is not None:
            raise ValueError(f"Production image already exists for {vocab_id}")
        word = image.sanitize_filename(record["english"])
        target = {"vocab_id": vocab_id, "source_row_index": record["source_row_index"],
                  "english": word, "japanese_reading": record["japanese"]["reading"],
                  "vietnamese": record["vietnamese"], "target_sense": record["target_sense"],
                  "semantic_review_status": record["review_status"], "query": None,
                  "query_provenance": None, "status": "ready", "failure": None}
        try:
            target["query"], target["query_provenance"] = select_effective_query(
                vocab_id, model_queries[index], decisions)
            if target["query"] is None:
                target.update(status="blocked_query_generation",
                              failure=(query_errors or {}).get(index, "Qwen query unavailable"))
        except ValueError as error:
            target.update(status="blocked_semantic_review", failure=str(error))
        selected.append(target)
    return selected


def _validated_asset(root: Path, run_dir: Path, target: dict, expected_hash: str | None = None) -> dict:
    word, query, provenance = target["english"], target["query"], target["query_provenance"]
    path = run_dir / f"{word}.jpg"
    metadata_path = run_dir / "_metadata" / f"{word}.json"
    with Image.open(path) as opened:
        if opened.format != "JPEG" or opened.width < 1 or opened.height < 1:
            raise ValueError("staged image is not a valid JPEG")
        dimensions = [opened.width, opened.height]
        opened.verify()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise ValueError("staged metadata is not an object")
    selection = metadata.get("image_selection")
    if (metadata.get("word") != word or metadata.get("search_query") != query
            or metadata.get("query_provenance") != provenance
            or metadata.get("provider") != image.IMAGE_PROVIDER
            or metadata.get("search_client") != "ddgs"
            or metadata.get("search_backend") != "bing"
            or not image.is_supported_remote_url(metadata.get("image_url"))
            or not isinstance(selection, dict) or selection.get("method") != "siglip2"
            or selection.get("model") != image.DEFAULT_SIGLIP_MODEL
            or not isinstance(selection.get("score"), (int, float))
            or not math.isfinite(selection["score"])):
        raise ValueError("staged metadata/query/source/SigLIP mismatch")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected_hash is not None and digest != expected_hash:
        raise ValueError("staged JPEG SHA-256 changed; preserve asset")
    return {"staged_image_path": path.relative_to(root).as_posix(),
            "staged_metadata_path": metadata_path.relative_to(root).as_posix(),
            "dimensions": dimensions, "size_bytes": path.stat().st_size,
            "sha256": digest,
            "selected_result": {key: metadata.get(key) for key in
                                ("image_url", "source_page_url", "title", "width", "height", "result_source")},
            "siglip_selection": selection, "validation_status": "valid_jpeg_and_metadata"}


def stage_images(root: Path, vocab_ids: list[str], *, run_id: str | None = None,
                 resume: bool = False, timeout: int = 12, retries: int = 1,
                 retry_delay: float = 1.0, page_size: int = 3,
                 rate_limit_delay: float = 1.0, qwen_batch_size: int = 2,
                 qwen_cache: Path | None = None, siglip_device: str = "auto",
                 siglip_dtype: str = "auto") -> tuple[Path, dict]:
    if (timeout < 1 or retries < 0 or page_size < 1 or page_size > 3
            or qwen_batch_size < 1 or not math.isfinite(retry_delay) or retry_delay < 0
            or not math.isfinite(rate_limit_delay) or rate_limit_delay < 0):
        raise ValueError("Invalid bounded image staging settings")
    if resume and run_id is None:
        raise ValueError("Resume requires a run ID")
    if run_id is not None and not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Unsafe staging run ID")
    root = root.resolve()
    dataset = build_dataset(root)
    records = dataset["records"]
    if not 1 <= len(vocab_ids) <= 10 or len(set(vocab_ids)) != len(vocab_ids):
        raise ValueError("Choose 1–10 distinct vocabulary IDs")
    by_id = {record["vocab_id"]: record for record in records}
    for vocab_id in vocab_ids:
        if not isinstance(vocab_id, str) or not ID_PATTERN.fullmatch(vocab_id) or vocab_id not in by_id:
            raise ValueError(f"Unknown or invalid vocabulary ID: {vocab_id!r}")
        if by_id[vocab_id]["image"]["path"] is not None:
            raise ValueError(f"Production image already exists for {vocab_id}")
    if len({by_id[vocab_id]["english"] for vocab_id in vocab_ids}) != len(vocab_ids):
        raise ValueError("Selected vocabulary words collide on image filename")
    decisions = load_decisions(root, load_registry(root))
    cache_path = safe_asset(root, qwen_cache or QUERY_CACHE)
    cache_base = safe_asset(root, QUERY_CACHE.parent)
    if cache_path.parent != cache_base or cache_base != root / QUERY_CACHE.parent:
        raise ValueError("Qwen staging cache must remain in isolated image-queries directory")
    queries, query_errors = prepare_staging_queries(
        [r["english"] for r in records], cache_path,
        cache_path.with_name("generated_qwen_sparse_v1.json"), qwen_batch_size)
    selected = choose_targets(dataset, vocab_ids, queries, decisions, query_errors)
    selected.sort(key=lambda entry: entry["source_row_index"])
    ordered_ids = [entry["vocab_id"] for entry in selected]
    if run_id is None:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    base = safe_asset(root, STAGING_BASE)
    run_dir = safe_asset(root, STAGING_BASE / run_id)
    if base != root / STAGING_BASE or run_dir != base / run_id:
        raise ValueError("Image staging path is redirected")
    manifest_path = run_dir / "run_manifest.json"
    if resume:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (data.get("schema_version") != 1 or data.get("run_id") != run_id
                or data.get("vocab_ids") != ordered_ids
                or data.get("purpose") != "generic_vocabulary_image_staging"):
            raise ValueError("Image staging manifest does not match requested IDs")
    else:
        run_dir.mkdir(parents=True, exist_ok=False)
        data = {"schema_version": 1, "run_id": run_id,
                "purpose": "generic_vocabulary_image_staging", "vocab_ids": ordered_ids,
                "configuration": {"timeout": timeout, "retries": retries,
                                  "retry_delay": retry_delay, "page_size": page_size,
                                  "rate_limit_delay": rate_limit_delay,
                                  "search_backend": "bing", "qwen_model": DEFAULT_QWEN_MODEL,
                                  "qwen_cache": cache_path.relative_to(root).as_posix(),
                                  "siglip_model": image.DEFAULT_SIGLIP_MODEL,
                                  "siglip_device": siglip_device, "siglip_dtype": siglip_dtype},
                "targets": []}
        save_run_manifest(manifest_path, data)

    prior = {entry["vocab_id"]: entry for entry in data["targets"]}
    if resume:
        for target in selected:
            old = prior.get(target["vocab_id"])
            if old and any(old.get(field) != target.get(field)
                           for field in ("english", "query", "query_provenance", "target_sense")
                           if field in old):
                raise ValueError("Canonical image target changed; preserve old run and use a new run ID")
            if not old:
                continue
            image_path = run_dir / f"{target['english']}.jpg"
            metadata_path = run_dir / "_metadata" / f"{target['english']}.json"
            if old.get("status") == "staged":
                try:
                    checked = _validated_asset(root, run_dir, target, old.get("sha256"))
                    if any(checked.get(field) != old.get(field) for field in
                           ("staged_image_path", "staged_metadata_path", "dimensions",
                            "size_bytes", "sha256", "selected_result", "siglip_selection")):
                        raise ValueError("manifest entry differs from staged asset")
                except (OSError, ValueError) as error:
                    raise ValueError(f"Existing staged image conflict for {target['vocab_id']}: {error}") from error
            elif image_path.exists() or metadata_path.exists():
                raise ValueError(f"Existing failed image conflict for {target['vocab_id']}; preserve old run")
    old_dirs = image.IMAGE_DIR, image.METADATA_DIR, image.CANDIDATE_CACHE_DIR
    image.IMAGE_DIR, image.METADATA_DIR, image.CANDIDATE_CACHE_DIR = (
        run_dir, run_dir / "_metadata", run_dir / "_candidates")
    blocked = None
    try:
        image.ensure_directories()
        scorer = image.LazySiglipScorer(SimpleNamespace(
            siglip_model=image.DEFAULT_SIGLIP_MODEL,
            siglip_device=siglip_device, siglip_dtype=siglip_dtype))
        entries = []
        for position, target in enumerate(selected):
            vocab_id, word = target["vocab_id"], target["english"]
            old = prior.get(vocab_id)
            entry = {**target, "provider": image.IMAGE_PROVIDER,
                     "search_client": "ddgs", "search_backend": "bing",
                     "approval_status": "pending_human_review", "license_status": "unknown",
                     "candidate_retrieval": None, "selected_result": None,
                     "siglip_selection": None, "staged_image_path": None,
                     "staged_metadata_path": None, "dimensions": None,
                     "size_bytes": None, "sha256": None,
                     "validation_status": "not_downloaded", "failure_stage": None,
                     "failure_type": None, "resume_cache_status": None}
            path, metadata_path = run_dir / f"{word}.jpg", run_dir / "_metadata" / f"{word}.json"
            if target["status"] in {"blocked_semantic_review", "blocked_query_generation"}:
                pass
            elif path.exists() or metadata_path.exists():
                try:
                    if (not old or old.get("status") != "staged"
                            or old.get("query") != target["query"]
                            or old.get("query_provenance") != target["query_provenance"]
                            or old.get("staged_image_path") != path.relative_to(root).as_posix()):
                        raise ValueError("existing staged JPEG/metadata conflict; preserve asset")
                    validated = _validated_asset(root, run_dir, target, old.get("sha256"))
                    if validated["selected_result"] != old.get("selected_result"):
                        raise ValueError("staged source metadata changed; preserve asset")
                    entry.update(old)
                    entry.update(validated)
                    entry["resume_cache_status"] = "cache_hit"
                except (OSError, ValueError) as error:
                    entry.update(status="failed", failure=str(error), failure_stage="resume_validation",
                                 failure_type=type(error).__name__)
            elif old and old.get("status") == "staged":
                entry.update(status="failed", failure="previously staged asset is missing; preserve evidence",
                             failure_stage="resume_validation", failure_type="MissingAsset")
            elif blocked:
                entry.update(status="blocked_provider", failure=blocked,
                             failure_stage="provider", failure_type="ProviderBlocked")
            else:
                collected = image.process_word(
                    word, target["query"], timeout=timeout, retries=retries,
                    retry_delay=retry_delay, page_size=page_size, scorer=scorer,
                    siglip_model=image.DEFAULT_SIGLIP_MODEL,
                    query_provenance=target["query_provenance"], search_backend="bing")
                entry["candidate_retrieval"] = {
                    "raw_results": collected.search_result_count,
                    "valid_results": collected.valid_candidate_count,
                    "downloaded_candidates": collected.candidate_count,
                    "search_seconds": collected.search_seconds,
                    "selected_image_url": collected.selected_image}
                if collected.ok and collected.status == "downloaded":
                    try:
                        validated = _validated_asset(root, run_dir, target)
                        if validated["selected_result"]["image_url"] != collected.selected_image:
                            raise ValueError("selected image URL differs from metadata")
                        entry.update(validated)
                        entry["status"] = "staged"
                    except (OSError, ValueError) as error:
                        entry.update(status="failed", failure=f"staged validation failed: {error}",
                                     failure_stage="validation", failure_type=type(error).__name__,
                                     validation_status="invalid")
                else:
                    reason = collected.reason or f"unexpected collection status: {collected.status}"
                    entry.update(status="failed", failure=reason,
                                 failure_stage=collected.failure_stage,
                                 failure_type=collected.failure_type)
                    if any(code in reason for code in ("HTTP 403", "HTTP 429")) or (
                            collected.failure_stage == "scoring" and "load" in reason.lower()):
                        blocked = reason
            entries.append(entry)
            data["targets"] = entries + [prior[item["vocab_id"]] for item in selected[position + 1:]
                                         if item["vocab_id"] in prior]
            save_run_manifest(manifest_path, data)
            if not blocked and position < len(selected) - 1 and rate_limit_delay:
                time.sleep(rate_limit_delay)
        data["targets"] = entries
    finally:
        image.IMAGE_DIR, image.METADATA_DIR, image.CANDIDATE_CACHE_DIR = old_dirs
    return manifest_path, data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vocab-id", action="append", required=True,
                        help="Stable ID to stage; repeat for up to ten IDs")
    parser.add_argument("--run-id", help="Unique run ID; required with --resume")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--timeout", type=int, default=12)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--retry-delay", type=float, default=1.0)
    parser.add_argument("--page-size", type=int, default=3)
    parser.add_argument("--rate-limit-delay", type=float, default=1.0)
    parser.add_argument("--qwen-batch-size", type=int, default=2)
    parser.add_argument("--qwen-cache", type=Path)
    parser.add_argument("--siglip-device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--siglip-dtype", choices=("auto", "float16", "bfloat16", "float32"),
                        default="auto")
    args = parser.parse_args(argv)
    path, data = stage_images(PROJECT_ROOT, args.vocab_id, **{k: v for k, v in vars(args).items()
                                                           if k != "vocab_id"})
    print(f"Staging manifest: {path}")
    for entry in data["targets"]:
        print(f"{entry['vocab_id']} {entry['english']}: {entry['status']}"
              + (f" ({entry['failure']})" if entry["failure"] else ""))
    return 0 if all(entry["status"] in {"staged", "blocked_semantic_review",
                                         "blocked_query_generation"}
                    for entry in data["targets"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
