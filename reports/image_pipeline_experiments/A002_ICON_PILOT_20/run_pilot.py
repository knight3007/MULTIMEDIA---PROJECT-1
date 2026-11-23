"""Isolated 20-item icon search using the repository's image collector and scorer."""

import argparse
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


RUN_ID = "A002_ICON_PILOT_20"
SOURCE = ROOT / "reports/phase0_quality_review/a001_20261122/evaluation_matrix.json"
IDS = [19, 41, 42, 43, 47, 48, 51, 53, 54, 55, 56, 58, 61, 62, 65, 75, 77, 78, 81, 82]
REASONS = {
    19: "weather term; wrong illumination image", 41: "today; timepiece mismatch",
    42: "tomorrow; timepiece mismatch", 43: "yesterday; unrelated scene",
    47: "abstract adjective; poor image", 48: "abstract adjective; poor image",
    51: "go action; static portrait", 53: "write action; unclear scene",
    54: "study action; object-style query", 55: "work action; object-style query",
    56: "sleep action; object-style query", 58: "drink action; beverage noun",
    61: "understand action; unrelated image", 62: "remember action; object-style query",
    65: "swim action; static portrait", 75: "abstract experience; poor image",
    77: "important adjective; poor image", 78: "different relation; poor image",
    81: "because relation; poor image", 82: "always frequency; poor image",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def source_items():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert source["run_id"] == "a001_20261122"
    by_id = {x["vocab_id"]: x for x in source["items"]}
    assert len(IDS) == len(set(IDS)) == 20
    selected = [by_id[f"vocab-{number:06d}"] for number in IDS]
    assert all(x["image_learning_suitability"] == "FAIL" for x in selected)
    return selected


def prepare():
    selected = source_items()
    HERE.mkdir(parents=True, exist_ok=True)
    with (HERE / "selected_vocabulary.csv").open("w", encoding="utf-8-sig", newline="") as file:
        fields = ["vocab_id", "english", "japanese", "vietnamese", "selection_reason",
                  "baseline_query", "icon_query", "baseline_image", "baseline_image_sha256",
                  "ai_image_relevance", "ai_image_learning_suitability"]
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for x, number in zip(selected, IDS):
            writer.writerow(dict(vocab_id=x["vocab_id"], english=x["english"], japanese=x["japanese"],
                vietnamese=x["vietnamese"], selection_reason=REASONS[number],
                baseline_query=x["parsed_qwen_query"], icon_query=x["english"] + " icon",
                baseline_image=x["image_path"] or "", baseline_image_sha256=x["image_sha256"] or "",
                ai_image_relevance=x["image_relevance"],
                ai_image_learning_suitability=x["image_learning_suitability"]))
    manifest = {"experiment_id": RUN_ID, "status": "prepared", "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_run_id": "a001_20261122", "source_matrix_sha256": digest(SOURCE),
        "selected_ids": [x["vocab_id"] for x in selected],
        "query_rule": "<english vocabulary> icon", "provider": IMAGE_PROVIDER,
        "region": DDG_REGION, "safesearch": DDG_SAFESEARCH,
        "page_size": DEFAULT_PAGE_SIZE, "timeout_seconds": 12, "search_retries": 1,
        "download_retries": 0, "siglip_model": "google/siglip2-so400m-patch16-384",
        "production_files_modified": False}
    if not (HERE / "experiment_manifest.json").exists():
        save_json(HERE / "experiment_manifest.json", manifest)
    if not (HERE / "retrieval_results.json").exists():
        save_json(HERE / "retrieval_results.json", {"experiment_id": RUN_ID, "items": []})
    return selected


def run():
    selected = prepare()
    results_path = HERE / "retrieval_results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    done = {x["vocab_id"] for x in results["items"]}
    scorer = None
    scorer_error = None
    try:
        from image_scorer import SiglipImageScorer
        scorer = SiglipImageScorer()
        print("SIGLIP_READY", scorer.device, scorer.model_path, flush=True)
    except (Exception) as error:
        scorer_error = f"{type(error).__name__}: {error}"
        print("SIGLIP_NOT_RUN", scorer_error, flush=True)
    for x in selected:
        if x["vocab_id"] in done:
            continue
        query = x["english"] + " icon"
        item = {"vocab_id": x["vocab_id"], "english": x["english"], "query": query,
                "search_status": "NOT_RUN", "search_error": None, "raw_result_count": 0,
                "normalized_result_count": 0, "search_seconds": None, "download_seconds": None,
                "scoring_seconds": None, "ranking_status": "NOT_RUN", "ranking_error": scorer_error,
                "selection_method": None, "selected_candidate_id": None, "candidates": []}
        print("ITEM", x["vocab_id"], query, flush=True)
        try:
            batch = search_images(query, page_size=DEFAULT_PAGE_SIZE, timeout=12, retries=1, retry_delay=1)
            item.update(search_status="SUCCESS", raw_result_count=batch.raw_count,
                        normalized_result_count=len(batch.candidates), search_seconds=batch.duration_seconds,
                        search_backend=batch.backend)
            started = time.perf_counter()
            for rank, result in enumerate(batch.candidates[:DEFAULT_PAGE_SIZE], 1):
                candidate_id = f"{x['vocab_id']}-{rank:02d}"
                folder = HERE / "images" / x["vocab_id"]
                folder.mkdir(parents=True, exist_ok=True)
                raw = folder / f"{rank:02d}.img"
                jpg = folder / f"{rank:02d}.jpg"
                candidate = {"candidate_id": candidate_id, "retrieval_rank": rank,
                    "source_url": result.get("source_page_url"), "image_url": result["image_url"],
                    "title": result.get("title"), "provider": result.get("provider"),
                    "search_backend": result.get("search_backend", batch.backend),
                    "status": "DOWNLOAD_FAILED", "error": None, "siglip_score": None,
                    "raw_path": None, "raw_sha256": None, "image_path": None, "image_sha256": None}
                try:
                    download_candidate_image(result["image_url"], raw, timeout=12, retries=0, retry_delay=0)
                    normalize_image_to_jpeg(raw, jpg)
                    with Image.open(jpg) as image:
                        image.verify()
                    candidate.update(status="DOWNLOADED", raw_path=raw.relative_to(ROOT).as_posix(),
                        raw_sha256=digest(raw), image_path=jpg.relative_to(ROOT).as_posix(),
                        image_sha256=digest(jpg))
                except Exception as error:
                    candidate["error"] = f"{type(error).__name__}: {error}"
                    raw.unlink(missing_ok=True)
                    jpg.unlink(missing_ok=True)
                item["candidates"].append(candidate)
            item["download_seconds"] = time.perf_counter() - started
            valid = [c for c in item["candidates"] if c["status"] == "DOWNLOADED"]
            if valid and scorer:
                started = time.perf_counter()
                try:
                    scores = scorer.score_batch(query, [ROOT / c["raw_path"] for c in valid])
                    for candidate, score in zip(valid, scores, strict=True):
                        candidate["siglip_score"] = score.score
                    chosen = max(valid, key=lambda c: c["siglip_score"])
                    item.update(ranking_status="SCORED", ranking_error=None,
                                selection_method="SIGLIP_TOP_SCORE", selected_candidate_id=chosen["candidate_id"])
                except Exception as error:
                    item["ranking_error"] = f"{type(error).__name__}: {error}"
                item["scoring_seconds"] = time.perf_counter() - started
            if valid and not item["selected_candidate_id"]:
                item.update(selection_method="FIRST_DOWNLOADED_UNRANKED",
                            selected_candidate_id=valid[0]["candidate_id"])
        except Exception as error:
            item.update(search_status="FAILED", search_error=f"{type(error).__name__}: {error}")
        results["items"].append(item)
        save_json(results_path, results)
        print("RESULT", item["search_status"], len(item["candidates"]),
              item["selected_candidate_id"], item["ranking_status"], flush=True)
        time.sleep(2)
    manifest_path = HERE / "experiment_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = "retrieval_complete" if len(results["items"]) == 20 else "partial"
    manifest["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["siglip_status"] = "SCORED" if any(x["ranking_status"] == "SCORED" for x in results["items"]) else "NOT_RUN"
    manifest["retrieval_result_count"] = len(results["items"])
    save_json(manifest_path, manifest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    prepare() if args.prepare else run()
