"""Run only the frozen A-003.2 sometimes queries; retain partial results."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "collect data script"))
from imagecollector import download_candidate_image, normalize_image_to_jpeg, search_images  # noqa: E402


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


manifest = json.loads((HERE / "repair_manifest.json").read_text(encoding="utf-8"))
assert manifest["status"] == "QUERIES_FROZEN_BEFORE_RETRIEVAL"
assert manifest["new_retrieval"]["vocab-000031"]["queries"] == []
variants = manifest["new_retrieval"]["vocab-000083"]["queries"]
assert 1 <= len(variants) <= 3 and all(v["variant"] in ("S1", "S2", "S3") for v in variants)
settings = manifest["settings"]
assert settings["max_candidates_per_variant"] <= 7
for relative, expected in manifest["source_sha256"].items():
    source = ROOT / ("reports/image_pipeline_experiments/" + relative if relative.startswith("A003_") else relative)
    assert digest(source) == expected, relative
result_path = HERE / "targeted_retrieval_results.json"
if result_path.exists():
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["queries"] == variants
    assert all(v["search_status"] == "FAILED" and not v["candidates"] for v in result["variants"])
else:
    result = {"task_id": "A-003.2", "vocab_id": "vocab-000083", "queries": variants,
              "started_at_utc": datetime.now(timezone.utc).isoformat(), "variants": []}
    save(result_path, result)
for variant in variants:
    existing = next((v for v in result["variants"] if v["variant"] == variant["variant"]), None)
    if existing:
        existing.setdefault("previous_search_errors", []).append(existing["search_error"])
        existing["search_status"] = "NOT_RUN"
        existing["search_error"] = None
        entry = existing
    else:
        entry = {"variant": variant["variant"], "query": variant["query"],
                 "search_status": "NOT_RUN", "search_error": None, "raw_result_count": 0,
                 "normalized_result_count": 0, "candidates": []}
        result["variants"].append(entry)
    save(result_path, result)
    try:
        batch = search_images(variant["query"], page_size=settings["max_candidates_per_variant"],
                              timeout=settings["timeout_seconds"], retries=settings["search_retries"],
                              retry_delay=settings["retry_delay_seconds"])
        entry.update(search_status="SUCCESS", raw_result_count=batch.raw_count,
                     normalized_result_count=len(batch.candidates))
    except Exception as error:
        entry.update(search_status="FAILED", search_error=f"{type(error).__name__}: {error}")
        save(result_path, result)
        print(variant["variant"], "search failed:", entry["search_error"], flush=True)
        continue
    save(result_path, result)
    for index, source in enumerate(batch.candidates[:settings["max_candidates_per_variant"]], start=1):
        folder = HERE / "images" / "vocab-000083" / variant["variant"]
        folder.mkdir(parents=True, exist_ok=True)
        raw, jpg = folder / f"{index:02d}.img", folder / f"{index:02d}.jpg"
        candidate = {"candidate_id": f"vocab-000083-{variant['variant']}-{index:02d}",
                     "retrieval_rank": index, "title": source.get("title"),
                     "source_url": source.get("source_page_url"), "image_url": source["image_url"],
                     "status": "DOWNLOAD_FAILED", "error": None, "raw_path": None,
                     "raw_sha256": None, "image_path": None, "image_sha256": None}
        entry["candidates"].append(candidate)
        save(result_path, result)
        try:
            download_candidate_image(source["image_url"], raw, timeout=settings["timeout_seconds"],
                                     retries=settings["download_retries"],
                                     retry_delay=settings["retry_delay_seconds"])
            normalize_image_to_jpeg(raw, jpg)
            candidate.update(status="DOWNLOADED", raw_path=raw.relative_to(ROOT).as_posix(),
                             raw_sha256=digest(raw), image_path=jpg.relative_to(ROOT).as_posix(),
                             image_sha256=digest(jpg))
        except Exception as error:
            candidate["error"] = f"{type(error).__name__}: {error}"
            raw.unlink(missing_ok=True)
            jpg.unlink(missing_ok=True)
        save(result_path, result)
        print(candidate["candidate_id"], candidate["status"], flush=True)
result["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
save(result_path, result)
