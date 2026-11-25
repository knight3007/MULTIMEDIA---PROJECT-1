"""Docker entry point for the existing private pipeline and final review gallery."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import sys
import traceback
import uuid
from pathlib import Path

from build_final_review_gallery import build
from content_pack_builder import validate_pack
from excel_multimedia_runner import OUTPUT_ROOT, execute, save_json
from excel_vocabulary_importer import accept, validate
from import_pipeline_adapter import build_manifest
from collector_common import PROJECT_ROOT
from image_pipeline_v2 import load_approved
from image_scorer import DEFAULT_SIGLIP_MODEL, resolve_local_model_path
from visual_query_policy import lookup_key
from excel_multimedia_runner import historical_no_suitable


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, value):
        for stream in self.streams:
            stream.write(value)
            stream.flush()

    def flush(self):
        for stream in self.streams:
            stream.flush()


def seed_reviewed_images(workbook: Path, source_run: Path) -> Path:
    """Reuse hash-verified private image choices without granting media approval."""
    workbook, source_run = workbook.resolve(), source_run.resolve()
    preview = validate(workbook)
    if not preview["valid"]:
        raise ValueError("Invalid workbook for reviewed-image reuse")
    source_import = json.loads((source_run / "import_manifest.json").read_text(encoding="utf-8"))
    if (source_import["workbook_sha256"] != hashlib.sha256(workbook.read_bytes()).hexdigest()
            or source_import["normalized_payload_sha256"] != preview["normalized_payload_sha256"]):
        raise ValueError("Reviewed-image run belongs to a different workbook")
    source_report = json.loads((source_run / "execution_report.json").read_text(encoding="utf-8"))
    source_pack_dir = source_run / source_report["active_content_pack"]
    source_pack = json.loads((source_pack_dir / "content_pack.json").read_text(encoding="utf-8"))
    if not validate_pack(source_pack, source_pack_dir)["valid"]:
        raise ValueError("Reviewed-image source Content Pack is invalid")
    source_images = {item["item_id"]: item for item in json.loads(
        (source_run / "image_selection_manifest.json").read_text(encoding="utf-8"))}
    if len(source_pack["items"]) != len(preview["rows"]):
        raise ValueError("Reviewed-image source row count differs")
    verified = []
    for row, item in zip(preview["rows"], source_pack["items"], strict=True):
        if any(row[key] != item[key] for key in ("source_row", "english", "japanese", "vietnamese", "target_sense")):
            raise ValueError("Reviewed-image source row identity differs")
        result = source_images[item["item_id"]]
        asset = item["image"]
        if (not asset or result["status"] != "AUTO_SELECTED_NEEDS_REVIEW"
                or result.get("image_sha256") != asset["sha256"]
                or item["distribution"]["status"] == "restricted"
                or result.get("usage_restriction")):
            raise ValueError(f"Image is missing or restricted from this cache: {item['english']}")
        candidate = next((c for c in result.get("candidates", [])
                          if c.get("jpeg_sha256") == asset["sha256"] and c.get("status") == "DOWNLOADED"
                          and not c.get("rejection") and isinstance(c.get("score"), (int, float))
                          and math.isfinite(c["score"])), None)
        if candidate is None:
            raise ValueError(f"Reviewed image has no matching scored candidate: {item['english']}")
        verified.append((result, candidate, source_pack_dir / asset["path"], asset["sha256"]))
    run_dir = OUTPUT_ROOT / f"run-{uuid.uuid4()}"
    run_dir.mkdir(parents=True, exist_ok=False)
    imported = accept(workbook, run_dir / "import_manifest.json")
    manifest = build_manifest(imported)
    manifest["workspace"] = run_dir.relative_to(PROJECT_ROOT).as_posix()
    manifest["pack_version"] = 1
    images = []
    for row, (old, candidate, source, digest) in zip(imported["rows"], verified, strict=True):
        item_id = row["item_id"]
        item = next(i for i in manifest["items"] if i["item_id"] == item_id)
        item["planned_paths"] = {"candidates": f"image_candidates/{item_id}",
                                 "audio_english": f"audio/{item_id}-en.mp3",
                                 "audio_japanese": f"audio/{item_id}-ja.mp3"}
        target = run_dir / "image_candidates" / item_id / "cached.jpg"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Cached image hash conflict: {row['english']}")
        candidate_id = f"{item_id}-cached"
        images.append({"item_id": item_id, "english": row["english"],
                       "policy_version": old.get("policy_version"), "route": old.get("route"),
                       "query": old.get("query"), "query_strategy": old.get("query_strategy") or old.get("route"),
                       "status": "AUTO_SELECTED_NEEDS_REVIEW", "review_status": "needs_review",
                       "proposed_candidate_id": candidate_id,
                       "candidates": [{"candidate_id": candidate_id, "status": "DOWNLOADED",
                                       "rejection": None, "score": candidate["score"],
                                       "jpeg_path": str(target), "jpeg_sha256": digest}],
                       "cache_origin": {"source_run": source_run.relative_to(PROJECT_ROOT).as_posix(),
                                        "source_item_id": old["item_id"], "image_sha256": digest}})
    save_json(run_dir / "processing_manifest.json", manifest)
    save_json(run_dir / "image_selection_manifest.json", images)
    print(f"[DOCKER] reused {len(images)} reviewed private images from {source_run}")
    return run_dir


def ensure_siglip_for_new_images(workbook: Path, resume: Path | None) -> None:
    """Populate the persistent cache only when the existing scorer will need it."""
    preview = validate(workbook)
    if not preview["valid"]:
        return  # The existing importer reports its detailed diagnostics.
    existing = set()
    if resume and (resume / "image_selection_manifest.json").exists():
        existing = {item["item_id"] for item in json.loads(
            (resume / "image_selection_manifest.json").read_text(encoding="utf-8"))}
    rows = preview["rows"]
    if resume:
        imported = json.loads((resume / "import_manifest.json").read_text(encoding="utf-8"))
        rows = imported["rows"]
    approved, no_suitable = load_approved(), historical_no_suitable()
    novel = [row for row in rows if row.get("item_id") not in existing
             and lookup_key(row["english"], row["japanese"], row["vietnamese"]) not in approved
             and lookup_key(row["english"], row["japanese"], row["vietnamese"]) not in no_suitable]
    if not novel:
        return
    model_dir = Path(resolve_local_model_path(DEFAULT_SIGLIP_MODEL))
    if model_dir.is_dir() and (model_dir / "model.safetensors").is_file():
        print(f"[DOCKER] using cached SigLIP: {model_dir}")
        return
    if os.environ.get("HF_HUB_OFFLINE", "0").lower() in {"1", "true", "yes"}:
        raise RuntimeError("SigLIP weights missing from mounted cache while HF_HUB_OFFLINE=1")
    from huggingface_hub import snapshot_download
    print(f"[DOCKER] downloading configured SigLIP model to persistent cache: {DEFAULT_SIGLIP_MODEL}")
    snapshot_download(DEFAULT_SIGLIP_MODEL)
    model_dir = Path(resolve_local_model_path(DEFAULT_SIGLIP_MODEL))
    if not (model_dir / "model.safetensors").is_file():
        raise RuntimeError("SigLIP download did not populate the scorer's expected local cache")


def run(workbook: Path, resume: Path | None = None, *, force_audio: bool = False,
        reuse_reviewed_run: Path | None = None) -> Path:
    if resume and reuse_reviewed_run:
        raise ValueError("Choose --resume or --reuse-reviewed-run, not both")
    if reuse_reviewed_run:
        resume = seed_reviewed_images(workbook, reuse_reviewed_run)
    else:
        ensure_siglip_for_new_images(workbook, resume)
    run_dir = execute(workbook, resume, force_audio=force_audio)
    summary = json.loads((run_dir / "execution_report.json").read_text(encoding="utf-8"))
    pack_name = summary["active_content_pack"]
    gallery = run_dir / "final_review_gallery.html"
    report = run_dir / "final_gallery_validation_report.json"
    if gallery.exists() != report.exists():
        raise FileExistsError("Incomplete final gallery; preserved for inspection")
    if gallery.exists():
        previous = json.loads(report.read_text(encoding="utf-8"))
        pack_path = run_dir / pack_name / "content_pack.json"
        if (previous.get("source_content_pack") != f"{pack_name}/content_pack.json"
                or previous.get("source_sha256") != hashlib.sha256(pack_path.read_bytes()).hexdigest()):
            raise FileExistsError("Final gallery belongs to another Content Pack; preserved for inspection")
        print(f"[DOCKER] reused existing final gallery: {gallery}")
    else:
        print(json.dumps(build(run_dir, pack_name), ensure_ascii=False))
    print(f"[DOCKER] run_dir={run_dir}")
    print(f"[DOCKER] content_pack={run_dir / pack_name / 'content_pack.json'}")
    print(f"[DOCKER] gallery={gallery}")
    failures = {f"image:{status}": count for status, count in summary["images"].items()
                if status.endswith("_FAILED") and count}
    failures.update({f"audio:{locale}": counts["FAILED"]
                     for locale, counts in summary["audio"].items() if counts.get("FAILED")})
    if failures:
        raise RuntimeError(f"Pipeline stages failed; see run manifests: {failures}")
    return run_dir


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--reuse-reviewed-run", type=Path)
    parser.add_argument("--force-audio", action="store_true")
    args = parser.parse_args(argv)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_ROOT / "docker_pipeline.log").open("a", encoding="utf-8") as log:
        stdout, stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = Tee(stdout, log), Tee(stderr, log)
        try:
            run(args.workbook, args.resume, force_audio=args.force_audio,
                reuse_reviewed_run=args.reuse_reviewed_run)
            return 0
        except Exception:
            traceback.print_exc()
            return 1
        finally:
            sys.stdout, sys.stderr = stdout, stderr


if __name__ == "__main__":
    raise SystemExit(main())
