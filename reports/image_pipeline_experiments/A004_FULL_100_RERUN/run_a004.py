"""Bounded, resumable A-004 execution. Run query phase before image phase."""
import argparse
import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "collect data script"))
import imagecollector as image
from image_scorer import SiglipImageScorer
from query_generator import QwenQueryGenerator, normalize_query
from semantic_decisions import load_decisions, select_effective_query
from vocabulary_registry import load_registry

MANIFEST = HERE / "experiment_manifest.json"
QUERIES = HERE / "query_results.json"
RETRIEVAL = HERE / "retrieval_results.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, obj):
    temp = path.with_suffix(path.suffix + ".tmp")
    try:
        temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def freeze_guard(manifest):
    if manifest["dataset_sha256"] != sha(ROOT / manifest["dataset_path"]):
        raise ValueError("Frozen dataset changed")
    if manifest["frozen_vocabulary_sha256"] != sha(ROOT / manifest["frozen_vocabulary_path"]):
        raise ValueError("Frozen vocabulary changed")
    for name, expected in manifest["source_code_sha256"].items():
        if sha(ROOT / "collect data script" / name) != expected:
            raise ValueError(f"Frozen component changed: {name}")
    current = sha(Path(__file__))
    if "runner_sha256" in manifest and manifest["runner_sha256"] != current:
        raise ValueError("Runner changed after execution started")
    if "runner_sha256" not in manifest:
        manifest["runner_sha256"] = current
        atomic_json(MANIFEST, manifest)


def frozen_rows():
    with (HERE / "frozen_vocabulary.csv").open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def run_queries(manifest, rows, max_batches):
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    snapshot = manifest["query"]["local_snapshots"]
    if len(snapshot) != 1 or not snapshot[0]["config_exists"]:
        raise ValueError("Frozen local Qwen snapshot unavailable")
    results = load_json(QUERIES)
    pending = [row for row in rows if row["vocab_id"] not in results]
    if not pending:
        print("Qwen phase already attempted for all 100 IDs")
        return
    generator = QwenQueryGenerator(snapshot[0]["path"], batch_size=1)
    decisions = load_decisions(ROOT, load_registry(ROOT))
    try:
        generator._load()  # local snapshot only; no generation until an ID is marked attempted
        manifest["query"]["actual_device"] = str(generator._input_device())
        manifest["query"]["actual_dtype"] = str(generator.model.dtype)
        manifest["status"] = "QUERY_IN_PROGRESS"
        atomic_json(MANIFEST, manifest)
        for start in range(0, len(pending), 10):
            if max_batches is not None and start // 10 >= max_batches:
                break
            batch = pending[start:start + 10]
            for row in batch:
                vid = row["vocab_id"]
                entry = {"vocab_id": vid, "english": row["english"], "status": "ATTEMPTED",
                         "model": manifest["query"]["model"], "model_revision": snapshot[0]["revision"],
                         "raw_decoded_text": None, "ended_with_eos": None,
                         "normalized_query": None, "effective_query": None,
                         "query_provenance": None, "error": None, "attempted_at": now()}
                results[vid] = entry
                atomic_json(QUERIES, results)  # crash cannot silently repeat an inference
                try:
                    raw, ended = generator._generate_raw([row["english"]])[0]
                    entry["raw_decoded_text"], entry["ended_with_eos"] = raw, ended
                    if not ended:
                        raise ValueError("Qwen output reached token limit without EOS")
                    normalized = normalize_query(raw)
                    entry["normalized_query"] = normalized
                    try:
                        effective, provenance = select_effective_query(vid, normalized, decisions)
                    except ValueError as error:
                        entry["status"] = "BLOCKED_SEMANTIC_DECISION"
                        entry["error"] = str(error)
                    else:
                        entry.update(status="SUCCESS", effective_query=effective, query_provenance=provenance)
                except Exception as error:
                    entry["status"] = "FAILED"
                    entry["error"] = f"{type(error).__name__}: {error}"
                entry["finished_at"] = now()
                atomic_json(QUERIES, results)
                manifest["completed_query_ids"] = list(results)
                atomic_json(MANIFEST, manifest)
                print("QWEN", vid, entry["status"], flush=True)
            manifest["batches"].append({"phase": "query", "ids": [r["vocab_id"] for r in batch], "saved_at": now()})
            atomic_json(MANIFEST, manifest)
    finally:
        generator.close()


def run_images(manifest, rows, max_batches):
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    query_results = load_json(QUERIES)
    if len(query_results) != 100:
        raise ValueError("Complete Qwen phase first; exactly 100 attempts required")
    results = load_json(RETRIEVAL)
    pending = [row for row in rows if row["vocab_id"] not in results]
    if not pending:
        print("Image phase already attempted for all 100 IDs")
        return
    scorer = SiglipImageScorer(device="auto", dtype="auto")
    manifest["ranking"]["actual_device"] = scorer.device
    manifest["ranking"]["actual_dtype"] = str(scorer.dtype)
    manifest["ranking"]["actual_model_path"] = scorer.model_path
    manifest["status"] = "IMAGE_IN_PROGRESS"
    atomic_json(MANIFEST, manifest)
    for start in range(0, len(pending), 10):
        if max_batches is not None and start // 10 >= max_batches:
            break
        batch = pending[start:start + 10]
        for row in batch:
            vid = row["vocab_id"]
            q = query_results[vid]
            entry = {"vocab_id": vid, "query": q.get("effective_query"),
                     "query_provenance": q.get("query_provenance"), "status": "NOT_RUN",
                     "search_attempted": False, "search_status": "NOT_RUN", "raw_result_count": 0,
                     "candidates": [], "score_attempted": False, "ranking_status": "NOT_RUN",
                     "proposed_candidate_id": None, "error": None}
            results[vid] = entry
            atomic_json(RETRIEVAL, results)
            if q["status"] != "SUCCESS":
                entry.update(status="SKIPPED_QUERY", error=q.get("error"))
                atomic_json(RETRIEVAL, results)
                manifest["completed_image_ids"] = list(results)
                atomic_json(MANIFEST, manifest)
                continue
            try:
                entry["search_attempted"] = True
                atomic_json(RETRIEVAL, results)
                batch_result = image.search_images(q["effective_query"], page_size=7, timeout=20,
                                                   retries=0, retry_delay=2, backend="auto")
                entry["search_status"] = "SUCCESS"
                entry["raw_result_count"] = batch_result.raw_count
                entry["search_backend"] = batch_result.backend
                entry["search_seconds"] = batch_result.duration_seconds
                for index, found in enumerate(batch_result.candidates[:7], 1):
                    entry["candidates"].append({"candidate_id": f"{vid}-{index:02d}",
                                                "retrieval_rank": index, "source": found,
                                                "download_status": "NOT_ATTEMPTED", "raw_path": None,
                                                "raw_sha256": None, "jpeg_path": None, "jpeg_sha256": None,
                                                "siglip_score": None, "error": None})
                atomic_json(RETRIEVAL, results)
                paths = []
                for candidate in entry["candidates"]:
                    item_dir = HERE / "images" / vid
                    item_dir.mkdir(parents=True, exist_ok=True)
                    stem = candidate["candidate_id"].split("-")[-1]
                    raw_path = item_dir / f"{stem}.img"
                    jpeg_path = item_dir / f"{stem}.jpg"
                    candidate["download_status"] = "ATTEMPTED"
                    atomic_json(RETRIEVAL, results)
                    try:
                        image.download_candidate_image(candidate["source"]["image_url"], raw_path,
                                                       timeout=20, retries=0, retry_delay=2)
                        image.normalize_image_to_jpeg(raw_path, jpeg_path)
                        candidate.update(download_status="SUCCESS", raw_path=raw_path.relative_to(ROOT).as_posix(),
                                         raw_sha256=sha(raw_path), jpeg_path=jpeg_path.relative_to(ROOT).as_posix(),
                                         jpeg_sha256=sha(jpeg_path))
                        paths.append(raw_path)
                    except Exception as error:
                        candidate.update(download_status="FAILED", error=f"{type(error).__name__}: {error}")
                    atomic_json(RETRIEVAL, results)
                if not paths:
                    entry.update(status="NO_VALID_CANDIDATES", error="No candidate downloaded and validated")
                else:
                    entry["score_attempted"] = True
                    atomic_json(RETRIEVAL, results)
                    scores = scorer.score_batch(q["effective_query"], paths)
                    by_path = {str(s.image_path): s.score for s in scores}
                    for candidate in entry["candidates"]:
                        if candidate["download_status"] == "SUCCESS":
                            candidate["siglip_score"] = float(by_path[str(ROOT / candidate["raw_path"])])
                    ranked = sorted((c for c in entry["candidates"] if c["siglip_score"] is not None),
                                    key=lambda c: c["siglip_score"], reverse=True)
                    for rank, candidate in enumerate(ranked, 1):
                        candidate["siglip_rank"] = rank
                    entry.update(status="RANKED", ranking_status="SUCCESS",
                                 proposed_candidate_id=ranked[0]["candidate_id"])
            except Exception as error:
                entry.update(status="FAILED", error=f"{type(error).__name__}: {error}")
            entry["finished_at"] = now()
            atomic_json(RETRIEVAL, results)
            manifest["completed_image_ids"] = list(results)
            atomic_json(MANIFEST, manifest)
            print("IMAGE", vid, entry["status"], "downloads", sum(c["download_status"] == "SUCCESS" for c in entry["candidates"]), flush=True)
        manifest["batches"].append({"phase": "image", "ids": [r["vocab_id"] for r in batch], "saved_at": now()})
        atomic_json(MANIFEST, manifest)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["queries", "images"])
    parser.add_argument("--max-batches", type=int)
    args = parser.parse_args()
    if args.max_batches is not None and args.max_batches < 1:
        parser.error("--max-batches must be positive")
    manifest = load_json(MANIFEST)
    freeze_guard(manifest)
    rows = frozen_rows()
    if len(rows) != 100:
        raise ValueError("Frozen sample must contain 100 IDs")
    if args.phase == "queries":
        run_queries(manifest, rows, args.max_batches)
    else:
        run_images(manifest, rows, args.max_batches)


if __name__ == "__main__":
    main()
