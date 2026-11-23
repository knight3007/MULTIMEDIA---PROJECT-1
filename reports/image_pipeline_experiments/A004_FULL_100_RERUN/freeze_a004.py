"""Freeze the A-004 inputs/configuration before any model or network execution."""
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "collect data script"))
import imagecollector as image
import image_scorer
import query_generator as query


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(model):
    base = Path(os.environ.get("HF_HUB_CACHE", Path.home() / ".cache/huggingface/hub"))
    paths = list((base / model / "snapshots").glob("*"))
    return [{"revision": path.name, "path": str(path), "config_exists": (path / "config.json").is_file()}
            for path in paths if path.is_dir()]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    HERE.mkdir(parents=True, exist_ok=True)
    manifest_path = HERE / "experiment_manifest.json"
    if manifest_path.exists():
        raise SystemExit("A-004 freeze already exists; preserve it")
    dataset_path = ROOT / "data/vocabulary/unified_dataset_v1.json"
    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    records = data["records"]
    if len(records) != 100 or len({r["vocab_id"] for r in records}) != 100:
        raise SystemExit("Expected exactly 100 unique benchmark IDs")
    baseline_path = ROOT / "reports/phase0_quality_review/a001_20261122/preliminary_unverified_baseline_v1.csv"
    with baseline_path.open(encoding="utf-8-sig", newline="") as stream:
        baseline = {r["vocab_id"]: r for r in csv.DictReader(stream)}
    if set(baseline) != {r["vocab_id"] for r in records}:
        raise SystemExit("A-001 baseline IDs do not match benchmark")
    vocab_path = HERE / "frozen_vocabulary.csv"
    with vocab_path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["vocab_id", "source_row_index", "english", "japanese",
                                                   "vietnamese", "target_sense", "expected_semantic_meaning",
                                                   "semantic_decision_status", "previous_image_path", "previous_image_sha256"])
        writer.writeheader()
        for r in records:
            old = baseline[r["vocab_id"]]
            writer.writerow({"vocab_id": r["vocab_id"], "source_row_index": r["source_row_index"],
                             "english": r["english"], "japanese": r["japanese"]["display"],
                             "vietnamese": r["vietnamese"], "target_sense": r["target_sense"] or "",
                             "expected_semantic_meaning": old["expected_semantic_meaning"],
                             "semantic_decision_status": old["semantic_decision_status"],
                             "previous_image_path": old["selected_image_path"],
                             "previous_image_sha256": old["selected_image_sha256"]})
    import torch, transformers
    manifest = {
        "task_id": "A-004", "status": "FROZEN_NOT_STARTED", "dataset_schema_version": data["schema_version"],
        "dataset_path": "data/vocabulary/unified_dataset_v1.json", "dataset_sha256": sha(dataset_path),
        "vocabulary_count": 100, "frozen_vocabulary_path": "reports/image_pipeline_experiments/A004_FULL_100_RERUN/frozen_vocabulary.csv",
        "frozen_vocabulary_sha256": sha(vocab_path),
        "a001_baseline_sha256": sha(baseline_path),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "git_branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
        "git_status_short_before": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
        "query": {"model": query.DEFAULT_QWEN_MODEL, "local_snapshots": snapshot("models--Qwen--Qwen3-1.7B"),
                  "prompt_sha256": hashlib.sha256(query.SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
                  "max_new_tokens": query.MAX_NEW_TOKENS, "do_sample": False,
                  "raw_generation_attempts_per_id": 1, "normalize_function": "query_generator.normalize_query",
                  "approved_semantic_query_override": "semantic_decisions.select_effective_query"},
        "retrieval": {"provider": image.IMAGE_PROVIDER, "client": "ddgs", "backend": "auto",
                      "region": image.DDG_REGION, "safesearch": image.DDG_SAFESEARCH,
                      "page_size": 7, "queries_per_id": 1, "timeout_seconds": 20,
                      "search_retries": 0, "download_retries": 0, "retry_delay_seconds": 2},
        "ranking": {"model": image_scorer.DEFAULT_SIGLIP_MODEL,
                    "local_snapshots": snapshot("models--google--siglip2-so400m-patch16-384"),
                    "method": "SiglipImageScorer.score_batch(query, raw_candidate_paths); descending raw logits",
                    "passes_per_id": 1},
        "preprocessing": {"method": "imagecollector.normalize_image_to_jpeg",
                          "alpha_compositing": "image_scorer.flatten_to_rgb white (FIX-001)",
                          "max_image_size": list(image.MAX_IMAGE_SIZE), "jpeg_quality": image.JPEG_QUALITY},
        "source_code_sha256": {p.name: sha(p) for p in [ROOT / "collect data script/query_generator.py",
                                                        ROOT / "collect data script/imagecollector.py",
                                                        ROOT / "collect data script/image_scorer.py",
                                                        ROOT / "collect data script/semantic_decisions.py"]},
        "environment": {"python": sys.version.split()[0], "platform": platform.platform(),
                        "torch": torch.__version__, "transformers": transformers.__version__,
                        "cuda_available": torch.cuda.is_available(), "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None},
        "batches": [], "completed_query_ids": [], "completed_image_ids": [], "blockers": []}
    with manifest_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print("frozen", len(records), manifest["dataset_sha256"], manifest_path)


if __name__ == "__main__":
    main()
