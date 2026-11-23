"""A-003 paired holdout: normal (cached Qwen) query vs '<english> icon', identical retrieval settings.

Phase 1 (--freeze): write frozen_sample.csv + experiment_manifest.json; refuses to change a frozen sample.
Phase 2 (default): resumable paired retrieval; skips (vocab_id, arm) pairs already in retrieval_results.json.
No Qwen call, no production writes. Run from the repository root.
"""

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "collect data script"))
from collector_common import DEFAULT_RETRIES, DEFAULT_TIMEOUT_SECONDS  # noqa: E402
from imagecollector import (DDG_REGION, DDG_SAFESEARCH, DEFAULT_PAGE_SIZE, IMAGE_PROVIDER,  # noqa: E402
                            download_candidate_image, normalize_image_to_jpeg, search_images)
from image_scorer import DEFAULT_SIGLIP_MODEL  # noqa: E402

RUN_ID = "A003_CONDITIONAL_SEARCH"
SOURCE = ROOT / "reports/phase0_quality_review/a001_20261122/evaluation_matrix.json"
ICON_PILOT_IDS = {19, 41, 42, 43, 47, 48, 51, 53, 54, 55, 56, 58, 61, 62, 65, 75, 77, 78, 81, 82}
CAUSAL_IDS = {81}
# Frozen before retrieval. Order is the execution order. No substitution after freeze.
SAMPLE = [
    (1, "CONCRETE", "food; task example; A-001 PASS"),
    (11, "CONCRETE", "animal; A-001 PASS"),
    (16, "CONCRETE", "nature/place; A-001 PASS"),
    (21, "CONCRETE", "building; task example; A-001 NEEDS_REVIEW (unfinished frame)"),
    (28, "CONCRETE", "vehicle; task example; A-001 PASS"),
    (31, "CONCRETE", "object; A-001 learning NEEDS_REVIEW (cover text)"),
    (57, "DIFFICULT_ACTION", "action verb; A-001 PASS (tests harm on a working action)"),
    (59, "DIFFICULT_ACTION", "action verb; A-001 FAIL (brand storefront)"),
    (63, "DIFFICULT_ACTION", "action verb; A-001 learning FAIL (flowchart)"),
    (45, "DIFFICULT_ABSTRACT", "emotion adjective; A-001 PASS"),
    (46, "DIFFICULT_ABSTRACT", "state adjective; A-001 learning FAIL (infographic)"),
    (83, "DIFFICULT_ABSTRACT", "frequency adverb; A-001 learning FAIL (word bubbles)"),
]
EXCLUDED = {"icon_pilot_20": sorted(ICON_PILOT_IDS), "causal_pilot": sorted(CAUSAL_IDS),
            "vocab-000086 why": "baseline query is already 'why icon' (arms would be confounded)",
            "vocab-000038 friend": "no baseline image query"}
SETTINGS = {"provider": IMAGE_PROVIDER, "region": DDG_REGION, "safesearch": DDG_SAFESEARCH,
            "page_size": DEFAULT_PAGE_SIZE, "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
            "search_retries": DEFAULT_RETRIES, "download_retries": DEFAULT_RETRIES, "retry_delay_seconds": 2.0,
            "pause_between_requests_seconds": 2.0, "siglip_model": DEFAULT_SIGLIP_MODEL}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def sample_rows():
    items = {x["vocab_id"]: x for x in json.loads(SOURCE.read_text(encoding="utf-8"))["items"]}
    numbers = [n for n, _, _ in SAMPLE]
    assert len(numbers) == len(set(numbers)) == 12
    assert not set(numbers) & (ICON_PILOT_IDS | CAUSAL_IDS | {38, 86})
    rows = []
    for index, (number, category, reason) in enumerate(SAMPLE):
        x = items[f"vocab-{number:06d}"]
        assert x["effective_image_query"], x["vocab_id"]
        rows.append({"order": index + 1, "vocab_id": x["vocab_id"], "category": category, "english": x["english"],
                     "japanese": x["japanese"], "vietnamese": x["vietnamese"], "target_sense": x["target_sense"] or "",
                     "intended_meaning": x["english"] + (f" ({x['target_sense']})" if x["target_sense"] else ""),
                     "selection_reason": reason, "normal_query": x["effective_image_query"],
                     "normal_query_provenance": x["query_provenance"], "icon_query": x["english"] + " icon",
                     "arm_order": "NORMAL_FIRST" if index % 2 == 0 else "ICON_FIRST",
                     "a001_image_path": x["image_path"] or "", "a001_image_sha256": x["image_sha256"] or "",
                     "a001_image_relevance": x["image_relevance"],
                     "a001_image_learning": x["image_learning_suitability"]})
    return rows


def freeze():
    path = HERE / "frozen_sample.csv"
    rows = sample_rows()
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as file:
            frozen = [r["vocab_id"] for r in csv.DictReader(file)]
        assert frozen == [r["vocab_id"] for r in rows], "frozen sample differs; refusing to substitute"
        return rows
    HERE.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    save_json(HERE / "experiment_manifest.json", {
        "experiment_id": RUN_ID, "status": "frozen", "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": head, "sample_size": len(rows),
        "composition": {"CONCRETE": 6, "DIFFICULT_ACTION": 3, "DIFFICULT_ABSTRACT": 3},
        "sample_ids": [r["vocab_id"] for r in rows], "excluded": EXCLUDED, "arms": {
            "NORMAL": "A-001 effective_image_query (cached Qwen output; Qwen not called)",
            "ICON": "<english> icon"},
        "settings_both_arms": SETTINGS,
        "siglip_primary_text": "each arm's own query (production rule); top score selected",
        "siglip_shared_text": "the bare English word, applied to both arms' candidates (cross-arm yardstick only)",
        "source_hashes": {p: digest(ROOT / p) for p in [
            "collect data script/imagecollector.py", "collect data script/image_scorer.py",
            "collect data script/collector_common.py",
            "reports/phase0_quality_review/a001_20261122/evaluation_matrix.json",
            "data/vocabulary/unified_dataset_v1.json"]},
        "frozen_sample_sha256": digest(path), "qwen_called": False, "production_files_modified": False})
    return rows


def retrieve(row, arm, query, scorer):
    entry = {"vocab_id": row["vocab_id"], "arm": arm, "query": query, "search_status": "NOT_RUN",
             "search_error": None, "raw_result_count": 0, "normalized_result_count": 0,
             "search_seconds": None, "download_seconds": None, "scoring_seconds": None,
             "ranking_status": "NOT_RUN", "ranking_error": None, "shared_text_status": "NOT_RUN",
             "selected_candidate_id": None, "selection_method": None, "candidates": [],
             "started_at_utc": datetime.now(timezone.utc).isoformat()}
    try:
        batch = search_images(query, page_size=SETTINGS["page_size"], timeout=SETTINGS["timeout_seconds"],
                              retries=SETTINGS["search_retries"], retry_delay=SETTINGS["retry_delay_seconds"])
    except Exception as error:
        entry.update(search_status="FAILED", search_error=f"{type(error).__name__}: {error}")
        return entry
    entry.update(search_status="SUCCESS", raw_result_count=batch.raw_count,
                 normalized_result_count=len(batch.candidates), search_seconds=batch.duration_seconds)
    folder = HERE / "images" / row["vocab_id"] / arm
    folder.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    for rank, result in enumerate(batch.candidates[:SETTINGS["page_size"]], 1):
        raw, jpg = folder / f"{rank:02d}.img", folder / f"{rank:02d}.jpg"
        c = {"candidate_id": f"{row['vocab_id']}-{arm}-{rank:02d}", "retrieval_rank": rank,
             "source_url": result.get("source_page_url"), "image_url": result["image_url"],
             "title": result.get("title"), "provider": result.get("provider"),
             "status": "DOWNLOAD_FAILED", "error": None, "query_score": None, "shared_score": None,
             "raw_path": None, "raw_sha256": None, "image_path": None, "image_sha256": None}
        try:
            download_candidate_image(result["image_url"], raw, timeout=SETTINGS["timeout_seconds"],
                                     retries=SETTINGS["download_retries"], retry_delay=SETTINGS["retry_delay_seconds"])
            normalize_image_to_jpeg(raw, jpg)
            with Image.open(jpg) as image:
                image.verify()
            c.update(status="DOWNLOADED", raw_path=raw.relative_to(ROOT).as_posix(), raw_sha256=digest(raw),
                     image_path=jpg.relative_to(ROOT).as_posix(), image_sha256=digest(jpg))
        except Exception as error:
            c["error"] = f"{type(error).__name__}: {error}"
            raw.unlink(missing_ok=True)
            jpg.unlink(missing_ok=True)
        entry["candidates"].append(c)
    entry["download_seconds"] = time.perf_counter() - started
    valid = [c for c in entry["candidates"] if c["status"] == "DOWNLOADED"]
    if valid and scorer:
        paths = [ROOT / c["raw_path"] for c in valid]
        started = time.perf_counter()
        try:
            for c, s in zip(valid, scorer.score_batch(query, paths), strict=True):
                c["query_score"] = s.score
            chosen = max(valid, key=lambda c: c["query_score"])
            entry.update(ranking_status="SCORED", selection_method="SIGLIP_TOP_SCORE",
                         selected_candidate_id=chosen["candidate_id"])
        except Exception as error:
            entry["ranking_error"] = f"{type(error).__name__}: {error}"
        entry["scoring_seconds"] = time.perf_counter() - started
        try:
            for c, s in zip(valid, scorer.score_batch(row["english"], paths), strict=True):
                c["shared_score"] = s.score
            entry["shared_text_status"] = "SCORED"
        except Exception as error:
            entry["shared_text_status"] = f"FAILED: {type(error).__name__}: {error}"
    if valid and not entry["selected_candidate_id"]:
        entry.update(selection_method="FIRST_DOWNLOADED_UNRANKED", selected_candidate_id=valid[0]["candidate_id"])
    return entry


def run():
    rows = freeze()
    path = HERE / "retrieval_results.json"
    results = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"experiment_id": RUN_ID, "pairs": []}
    done = {(p["vocab_id"], p["arm"]) for p in results["pairs"]}
    scorer, scorer_error = None, None
    try:
        from image_scorer import SiglipImageScorer
        scorer = SiglipImageScorer()
        print("SIGLIP_READY", scorer.device, flush=True)
    except Exception as error:
        scorer_error = f"{type(error).__name__}: {error}"
        print("SIGLIP_NOT_RUN", scorer_error, flush=True)
    for row in rows:
        arms = [("NORMAL", row["normal_query"]), ("ICON", row["icon_query"])]
        if row["arm_order"] == "ICON_FIRST":
            arms.reverse()
        for arm, query in arms:
            if (row["vocab_id"], arm) in done:
                continue
            entry = retrieve(row, arm, query, scorer)
            if not scorer:
                entry["ranking_error"] = scorer_error
            results["pairs"].append(entry)
            save_json(path, results)
            print("RESULT", row["vocab_id"], arm, entry["search_status"],
                  sum(c["status"] == "DOWNLOADED" for c in entry["candidates"]), len(entry["candidates"]),
                  entry["selected_candidate_id"], flush=True)
            time.sleep(SETTINGS["pause_between_requests_seconds"])
    manifest_path = HERE / "experiment_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(status="retrieval_complete" if len(results["pairs"]) == 2 * len(rows) else "partial",
                    completed_at_utc=datetime.now(timezone.utc).isoformat(),
                    siglip_status="SCORED" if scorer else "NOT_RUN", siglip_error=scorer_error)
    save_json(manifest_path, manifest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    freeze() if parser.parse_args().freeze else run()
