"""Private B-003.1 handoff from an accepted Excel import to media stages.

This module plans per-item work and records local evidence. It never invokes a
model, network provider, or content-pack exporter.
"""

import argparse
import hashlib
import json
import math
import re
import sys
import uuid
from pathlib import Path

from collector_common import PROJECT_ROOT
from excel_vocabulary_importer import payload_hash
from imagecollector import IMAGE_PROVIDER, normalize_ddg_results, validate_image_bytes
from image_scorer import DEFAULT_SIGLIP_MODEL
from query_generator import DEFAULT_QWEN_MODEL, normalize_query
from audiocollector import AUDIO_LOCALE, AUDIO_SOURCE


STAGES = ("query", "image_retrieval", "candidate_validation", "image_ranking",
          "image_review", "audio_generation", "pack_metadata")
QUALITY_FIELDS = ("semantic_correctness", "image_relevance", "image_visual_quality", "audio_pronunciation")
ERROR_STAGES = {"import", "query", "image", "audio", "validation", "review"}
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def valid_id(value, prefix):
    if not isinstance(value, str) or not value.startswith(prefix):
        return False
    raw = value[len(prefix):]
    try:
        return str(uuid.UUID(raw)) == raw and uuid.UUID(raw).version == 4
    except ValueError:
        return False


def load_import(path):
    """Check B-002's persisted mapping, including its normalized payload hash."""
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    return check_import(record)


def check_import(record):
    """Validate a persisted mapping or a caller-supplied in-memory mapping."""
    if (not isinstance(record, dict) or record.get("contract_version") != 1
            or not valid_id(record.get("import_id"), "imp-")
            or not valid_id(record.get("pack_id"), "pack-")
            or not isinstance(record.get("rows"), list) or not record["rows"]
            or not SHA256.fullmatch(str(record.get("workbook_sha256")))
            or not SHA256.fullmatch(str(record.get("normalized_payload_sha256")))):
        raise ValueError("Invalid B-002 import record")
    seen = set()
    for row in record["rows"]:
        if (not isinstance(row, dict) or not valid_id(row.get("item_id"), "item-")
                or type(row.get("source_row")) is not int or row["source_row"] < 2
                or any(not isinstance(row.get(k), str) or not row[k] for k in ("english", "japanese", "vietnamese"))
                or row.get("target_sense") is not None and (not isinstance(row["target_sense"], str) or not row["target_sense"])):
            raise ValueError("Invalid B-002 import row")
        if row["item_id"] in seen:
            raise ValueError("Duplicate imported item ID")
        seen.add(row["item_id"])
    if payload_hash(record["rows"]) != record["normalized_payload_sha256"]:
        raise ValueError("Imported normalized payload hash mismatch")
    return record


def import_directory(project_root, import_id):
    if not valid_id(import_id, "imp-"):
        raise ValueError("Invalid import ID")
    root = Path(project_root).resolve()
    private = root / "baseline" / "imports"
    if private.resolve() != private:
        raise ValueError("Private import root is redirected")
    destination = private / import_id
    if destination.resolve() != destination:
        raise ValueError("Private import directory is redirected")
    return destination


def build_manifest(record, project_root=PROJECT_ROOT):
    """Plan work using the pack's pending state without creating a runtime pack."""
    check_import(record)
    directory = import_directory(project_root, record["import_id"])
    items = []
    for row in record["rows"]:
        item_id = row["item_id"]
        items.append({**row, "status": "pending", "review_status": "pending",
                      "quality": {**{key: "unknown" for key in QUALITY_FIELDS}, "evidence": []},
                      "technical_integrity": "unknown", "distribution": {"status": "unknown", "evidence": None},
                      "image": None, "audio": None, "errors": [],
                      "planned_paths": {"query": f"queries/{item_id}.json",
                                        "candidates": f"candidates/{item_id}",
                                        "image": f"images/{item_id}.jpg",
                                        "audio": f"audio/{item_id}.mp3"},
                      "stages": {
                          "query": {"input": row["english"], "model": DEFAULT_QWEN_MODEL, "output": None},
                          "image_retrieval": {"provider": IMAGE_PROVIDER, "candidates": []},
                          "candidate_validation": {"verified_candidates": []},
                          "image_ranking": {"model": DEFAULT_SIGLIP_MODEL, "scores": []},
                          "image_review": {"decision": None, "candidate_id": None},
                          "audio_generation": {"input": row["japanese"], "provider": AUDIO_SOURCE,
                                               "locale": AUDIO_LOCALE, "output": None},
                          "pack_metadata": {"output": None},
                      }})
    return {"manifest_version": 1, "purpose": "PRIVATE_MEDIA_PROCESSING_PLAN",
            "import_id": record["import_id"], "pack_id": record["pack_id"],
            "normalized_payload_sha256": record["normalized_payload_sha256"],
            "workspace": directory.relative_to(Path(project_root).resolve()).as_posix(),
            "items": items}


def write_manifest(import_record_path, project_root=PROJECT_ROOT):
    record = load_import(import_record_path)
    manifest = build_manifest(record, project_root)
    directory = import_directory(project_root, record["import_id"])
    directory.mkdir(parents=True, exist_ok=False)
    path = directory / "processing_manifest.json"
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return path, manifest


def item_for(manifest, item_id):
    matches = [item for item in manifest["items"] if item["item_id"] == item_id]
    if len(matches) != 1:
        raise ValueError("Unknown or duplicate item ID")
    return matches[0]


def claim_item(manifest, item_id):
    item = item_for(manifest, item_id)
    if item["status"] != "pending":
        raise ValueError("Only a pending item can enter processing")
    item["status"] = "processing"
    return item


def record_query(manifest, item_id, query):
    item = item_for(manifest, item_id)
    if item["status"] != "processing" or item["stages"]["query"]["output"] is not None:
        raise ValueError("Item must be processing with no recorded query")
    item["stages"]["query"]["output"] = normalize_query(query)


def record_candidates(manifest, item_id, raw_results):
    item = item_for(manifest, item_id)
    if (item["status"] != "processing" or item["stages"]["query"]["output"] is None
            or item["stages"]["image_retrieval"]["candidates"]):
        raise ValueError("A processing item needs a validated query before retrieval evidence")
    candidates = normalize_ddg_results(raw_results)
    item["stages"]["image_retrieval"]["candidates"] = [
        {"candidate_id": f"{item_id}-candidate-{index:02d}", **candidate,
         "raw_path": None, "raw_sha256": None, "score": None}
        for index, candidate in enumerate(candidates, 1)]
    return candidates


def record_candidate_file(manifest, item_id, candidate_id, path, project_root=PROJECT_ROOT):
    """Attach locally validated candidate bytes; never select or approve them."""
    item = item_for(manifest, item_id)
    if item["status"] != "processing":
        raise ValueError("Item must be processing")
    candidates = item["stages"]["image_retrieval"]["candidates"]
    candidate = next((c for c in candidates if c["candidate_id"] == candidate_id), None)
    if candidate is None or candidate["raw_sha256"] is not None:
        raise ValueError("Unknown image candidate")
    directory = import_directory(project_root, manifest["import_id"])
    target = Path(path).resolve()
    if not target.is_file() or not target.is_relative_to(directory / "candidates" / item_id):
        raise ValueError("Candidate file must be inside this item's private candidate directory")
    data = target.read_bytes()
    validate_image_bytes(data)
    sha = hashlib.sha256(data).hexdigest()
    candidate["raw_path"] = target.relative_to(directory).as_posix()
    candidate["raw_sha256"] = sha
    item["stages"]["candidate_validation"]["verified_candidates"].append(candidate_id)
    return sha


def record_rank(manifest, item_id, candidate_id, score):
    """Store SigLIP evidence without mutating image, review or ready status."""
    item = item_for(manifest, item_id)
    candidates = item["stages"]["image_retrieval"]["candidates"]
    candidate = next((c for c in candidates if c["candidate_id"] == candidate_id), None)
    if (item["status"] != "processing" or candidate is None
            or candidate["raw_sha256"] is None or candidate["score"] is not None):
        raise ValueError("Only a validated candidate on a processing item can be ranked")
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score):
        raise ValueError("Rank score must be finite")
    candidate["score"] = float(score)
    item["stages"]["image_ranking"]["scores"] = [
        {"candidate_id": c["candidate_id"], "score": c["score"], "raw_sha256": c["raw_sha256"]}
        for c in candidates if c["score"] is not None]


def record_failure(manifest, item_id, stage, code, message, retryable=False):
    item = item_for(manifest, item_id)
    if item["status"] != "processing" or stage not in ERROR_STAGES or not code or not message:
        raise ValueError("Failure requires a processing item, valid stage, code and message")
    item["status"] = "failed"
    if code == "NO_SUITABLE_IMAGE" and stage in {"image", "review"}:
        item["stages"]["image_review"]["decision"] = "NO_SUITABLE_IMAGE"
    item["errors"].append({"stage": stage, "code": code, "message": message, "retryable": bool(retryable)})


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("import_record", type=Path, help="Accepted B-002 private import JSON")
    args = parser.parse_args()
    try:
        path, manifest = write_manifest(args.import_record)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        parser.exit(1, f"Adapter error: {error}\n")
    print(json.dumps({"manifest": str(path), "import_id": manifest["import_id"],
                      "item_count": len(manifest["items"]), "status": "pending"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
