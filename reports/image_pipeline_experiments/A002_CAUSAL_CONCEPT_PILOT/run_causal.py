"""Isolated causal-concept retrieval for vocab-000081 'because' (A002_CAUSAL_CONCEPT_PILOT).

Reuses the production search/download/normalize/SigLIP functions without modifying them.
Resumable: completed variants in retrieval_results.json are skipped; duplicate image URLs are
not downloaded twice. Run from the repository root:
    .venv\\Scripts\\python.exe -B reports/image_pipeline_experiments/A002_CAUSAL_CONCEPT_PILOT/run_causal.py
"""

import csv
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "collect data script"))
from imagecollector import (DEFAULT_PAGE_SIZE, IMAGE_PROVIDER, DDG_REGION, DDG_SAFESEARCH,
                            download_candidate_image, normalize_image_to_jpeg, search_images)
from image_scorer import DEFAULT_SIGLIP_MODEL


RUN_ID = "A002_CAUSAL_CONCEPT_PILOT"
VOCAB_ID = "vocab-000081"
SOURCE = ROOT / "reports/phase0_quality_review/a001_20261122/evaluation_matrix.json"
ICON_RESULTS = ROOT / "reports/image_pipeline_experiments/A002_ICON_PILOT_20/retrieval_results.json"
TIMEOUT, SEARCH_RETRIES, DOWNLOAD_RETRIES = 12, 1, 0  # same as A002_ICON_PILOT_20 for comparability
FIXED_TEXT = "an illustration in which one event causes another event to happen"
VARIANTS = [
    ("V1", "cause and effect pictogram", "Owner-specified: generic cause-effect pictogram."),
    ("V2", "reason and result visual illustration", "Owner-specified: reason/result framing."),
    ("V3", "cause effect visual sequence illustration", "Owner-specified: sequential causality."),
    ("V4", "child opening umbrella in the rain illustration",
     "Agent-written before searching (no Qwen): one frame can show both the cause (rain falling) "
     "and the result (child opening an umbrella), a familiar child-level situation, and the query "
     "avoids the word 'because' to reduce grammar slides and printed captions. Known risk: may "
     "read as 'rain' or 'umbrella' rather than the causal relation."),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def baseline_record():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    item = next(x for x in source["items"] if x["vocab_id"] == VOCAB_ID)
    assert item["english"] == "because"
    return item


def prepare():
    item = baseline_record()
    with (HERE / "query_variants.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["variant", "vocab_id", "query", "query_source", "rationale"])
        writer.writerow(["ORIGINAL", VOCAB_ID, item["parsed_qwen_query"], "A-001 Qwen3-1.7B cache", "Baseline reference; not searched again."])
        writer.writerow(["ICON", VOCAB_ID, "because icon", "A002_ICON_PILOT_20", "Previous pilot; not searched again."])
        for variant, query, rationale in VARIANTS:
            writer.writerow([variant, VOCAB_ID, query, "owner task" if variant != "V4" else "agent-written, recorded before search", rationale])
    manifest_path = HERE / "experiment_manifest.json"
    if not manifest_path.exists():
        save_json(manifest_path, {
            "experiment_id": RUN_ID, "status": "prepared",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "vocab_id": VOCAB_ID, "english": item["english"], "japanese": item["japanese"],
            "vietnamese": item["vietnamese"],
            "meaning_note": "なぜなら is a sentence-initial connective introducing the reason for a preceding statement (often paired with から); not interchangeable with clause-final から/ので in every context. semantic_decisions_v1.json review_status=needs_decision.",
            "source_matrix_sha256": digest(SOURCE), "icon_pilot_results_sha256": digest(ICON_RESULTS),
            "variants": [{"variant": v, "query": q} for v, q, _ in VARIANTS],
            "provider": IMAGE_PROVIDER, "region": DDG_REGION, "safesearch": DDG_SAFESEARCH,
            "page_size": DEFAULT_PAGE_SIZE, "timeout_seconds": TIMEOUT, "search_retries": SEARCH_RETRIES,
            "download_retries": DOWNLOAD_RETRIES, "siglip_model": DEFAULT_SIGLIP_MODEL,
            "siglip_primary_text": "each variant's own search query (production rule)",
            "siglip_fixed_text": FIXED_TEXT,
            "qwen_called": False, "ai_images_generated": False, "production_files_modified": False})
    results_path = HERE / "retrieval_results.json"
    if not results_path.exists():
        save_json(results_path, {"experiment_id": RUN_ID, "vocab_id": VOCAB_ID, "variants": [],
                                 "reference_fixed_scores": None})
    return item


def run():
    item = prepare()
    results_path = HERE / "retrieval_results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    done = {x["variant"] for x in results["variants"]}
    seen = {c["image_url"]: c for x in results["variants"] for c in x["candidates"] if c["status"] == "DOWNLOADED"}
    scorer, scorer_error = None, None
    try:
        from image_scorer import SiglipImageScorer
        scorer = SiglipImageScorer()
        print("SIGLIP_READY", scorer.device, flush=True)
    except Exception as error:
        scorer_error = f"{type(error).__name__}: {error}"
        print("SIGLIP_NOT_RUN", scorer_error, flush=True)

    for variant, query, rationale in VARIANTS:
        if variant in done:
            continue
        entry = {"variant": variant, "query": query, "rationale": rationale, "search_status": "NOT_RUN",
                 "search_error": None, "raw_result_count": 0, "normalized_result_count": 0,
                 "search_seconds": None, "ranking_status": "NOT_RUN", "ranking_error": scorer_error,
                 "fixed_text_status": "NOT_RUN", "selected_candidate_id": None,
                 "selection_method": None, "candidates": []}
        print("VARIANT", variant, query, flush=True)
        try:
            batch = search_images(query, page_size=DEFAULT_PAGE_SIZE, timeout=TIMEOUT,
                                  retries=SEARCH_RETRIES, retry_delay=1)
            entry.update(search_status="SUCCESS", raw_result_count=batch.raw_count,
                         normalized_result_count=len(batch.candidates),
                         search_seconds=batch.duration_seconds, search_backend=batch.backend)
            folder = HERE / "images" / variant
            folder.mkdir(parents=True, exist_ok=True)
            for rank, result in enumerate(batch.candidates[:DEFAULT_PAGE_SIZE], 1):
                cid = f"{variant}-{rank:02d}"
                raw, jpg = folder / f"{rank:02d}.img", folder / f"{rank:02d}.jpg"
                candidate = {"candidate_id": cid, "retrieval_rank": rank,
                             "source_url": result.get("source_page_url"), "image_url": result["image_url"],
                             "title": result.get("title"), "provider": result.get("provider"),
                             "width": result.get("width"), "height": result.get("height"),
                             "status": "DOWNLOAD_FAILED", "error": None, "duplicate_of": None,
                             "siglip_query_score": None, "siglip_fixed_score": None,
                             "raw_path": None, "raw_sha256": None, "image_path": None, "image_sha256": None}
                previous = seen.get(result["image_url"])
                if previous:
                    candidate.update(status="DOWNLOADED", duplicate_of=previous["candidate_id"],
                                     **{k: previous[k] for k in ("raw_path", "raw_sha256", "image_path", "image_sha256")})
                else:
                    try:
                        download_candidate_image(result["image_url"], raw, timeout=TIMEOUT,
                                                 retries=DOWNLOAD_RETRIES, retry_delay=0)
                        normalize_image_to_jpeg(raw, jpg)
                        with Image.open(jpg) as image:
                            image.verify()
                        candidate.update(status="DOWNLOADED", raw_path=raw.relative_to(ROOT).as_posix(),
                                         raw_sha256=digest(raw), image_path=jpg.relative_to(ROOT).as_posix(),
                                         image_sha256=digest(jpg))
                        seen[result["image_url"]] = candidate
                    except Exception as error:
                        candidate["error"] = f"{type(error).__name__}: {error}"
                        raw.unlink(missing_ok=True)
                        jpg.unlink(missing_ok=True)
                entry["candidates"].append(candidate)
            valid = [c for c in entry["candidates"] if c["status"] == "DOWNLOADED"]
            if valid and scorer:
                paths = [ROOT / c["raw_path"] for c in valid]
                try:
                    for c, s in zip(valid, scorer.score_batch(query, paths), strict=True):
                        c["siglip_query_score"] = s.score
                    chosen = max(valid, key=lambda c: c["siglip_query_score"])
                    entry.update(ranking_status="SCORED", ranking_error=None,
                                 selection_method="SIGLIP_TOP_SCORE", selected_candidate_id=chosen["candidate_id"])
                except Exception as error:
                    entry["ranking_error"] = f"{type(error).__name__}: {error}"
                try:
                    for c, s in zip(valid, scorer.score_batch(FIXED_TEXT, paths), strict=True):
                        c["siglip_fixed_score"] = s.score
                    entry["fixed_text_status"] = "SCORED"
                except Exception as error:
                    entry["fixed_text_status"] = f"FAILED: {type(error).__name__}: {error}"
            if valid and not entry["selected_candidate_id"]:
                entry.update(selection_method="FIRST_DOWNLOADED_UNRANKED", selected_candidate_id=valid[0]["candidate_id"])
        except Exception as error:
            entry.update(search_status="FAILED", search_error=f"{type(error).__name__}: {error}")
        results["variants"].append(entry)
        save_json(results_path, results)
        print("RESULT", variant, entry["search_status"], len(entry["candidates"]),
              entry["selected_candidate_id"], entry["ranking_status"], flush=True)
        time.sleep(2)

    # Fixed-text scores for the read-only references (original baseline + previous icon candidates).
    if scorer and not results.get("reference_fixed_scores"):
        icon = next(x for x in json.loads(ICON_RESULTS.read_text(encoding="utf-8"))["items"] if x["vocab_id"] == VOCAB_ID)
        refs = [("ORIGINAL", item["image_path"])] + [
            (c["candidate_id"], c["raw_path"]) for c in icon["candidates"] if c["status"] == "DOWNLOADED"]
        scores = scorer.score_batch(FIXED_TEXT, [ROOT / p for _, p in refs])
        results["reference_fixed_scores"] = {"text": FIXED_TEXT, "icon_selected_candidate_id": icon["selected_candidate_id"],
                                             "scores": {rid: s.score for (rid, _), s in zip(refs, scores)}}
        save_json(results_path, results)

    manifest_path = HERE / "experiment_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(status="retrieval_complete" if len(results["variants"]) == len(VARIANTS) else "partial",
                    completed_at_utc=datetime.now(timezone.utc).isoformat(),
                    siglip_status="SCORED" if scorer else "NOT_RUN", siglip_error=scorer_error)
    save_json(manifest_path, manifest)


if __name__ == "__main__":
    run()
