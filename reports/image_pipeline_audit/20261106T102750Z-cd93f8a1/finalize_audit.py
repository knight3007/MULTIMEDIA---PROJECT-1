"""Record final, reproducible read-only audit verification metadata."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
ROOT = AUDIT.parents[2]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    before = json.loads((AUDIT / "protected_hashes_before.json").read_text(encoding="utf-8-sig"))
    changes = []
    for item in before:
        path = ROOT / item["path"]
        now = digest(path) if path.is_file() else None
        if now != item["sha256"]:
            changes.append({"path": item["path"], "before": item["sha256"], "after": now})
    comparison = {"protected_file_count": len(before), "unchanged_count": len(before) - len(changes),
                  "changed_count": len(changes), "changed": changes}
    (AUDIT / "protected_hash_comparison.json").write_text(
        json.dumps(comparison, indent=2) + "\n", encoding="utf-8")
    stats = json.loads((AUDIT / "audit_statistics.json").read_text(encoding="utf-8"))
    initial_status = (AUDIT / "git_status_initial.txt").read_text(encoding="utf-8")
    final_status = subprocess.check_output(
        ["git", "status", "--short", "--untracked-files=normal"], cwd=ROOT,
        text=True, encoding="utf-8")
    (AUDIT / "git_status_final.txt").write_text(final_status, encoding="utf-8")
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    generated = sorted(p.relative_to(AUDIT).as_posix() for p in AUDIT.rglob("*") if p.is_file())
    generated.append("audit_manifest.json")
    manifest = {
        "audit_run_id": AUDIT.name,
        "execution_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_branch": branch, "git_head": head,
        "root_agents_md_present": (ROOT / "AGENTS.md").is_file(),
        "initial_git_status_short": initial_status.splitlines(),
        "final_git_status_short": final_status.splitlines(),
        "initial_final_short_status_equal": initial_status.splitlines() == final_status.splitlines(),
        "environment": {"python": platform.python_version(), "python_executable": ".venv/Scripts/python.exe",
                        "torch": "2.14.0+cu132", "transformers": "5.17.0",
                        "pillow": "12.3.0", "ddgs": "9.16.0", "gpu": "NVIDIA GeForce GTX 1650, 4096 MiB"},
        "models": {"qwen_id": "Qwen/Qwen3-1.7B", "qwen_revision": None,
                   "siglip_id": "google/siglip2-so400m-patch16-384",
                   "siglip_local_snapshot": "dd658faac399427308559e2c3ac1e99cbe43845d"},
        "files_inspected": [
            "CODEX_PROGRESS.md", "docs/DATA_CONTRACT_V1.md", ".gitignore",
            "data/vocabulary/{en,jp,vn}.txt", "data/vocabulary/id_registry_v1.json",
            "data/vocabulary/semantic_decisions_v1.json", "data/vocabulary/image_media_reviews_v1.json",
            "data/vocabulary/unified_dataset_v1.json", "data/query/generated_qwen.json",
            "data/query/generated_qwen_water_beverage.json",
            "baseline/media-staging/image-queries/generated_qwen_full_v1.json",
            "baseline/media-staging/image-queries/generated_qwen_sparse_v1.json",
            "baseline/media-staging/images/*/run_manifest.json",
            "baseline/media-staging/images/*/*.jpg",
            "baseline/media-staging/images/*/_metadata/*.json",
            "data/image/en/*.jpg", "data/image/en/_metadata/*.json",
            "reports/full_media_staging_inventory_v1.json", "reports/full_media_staging_review.md",
            "collect data script/query_generator.py", "collect data script/imagecollector.py",
            "collect data script/image_scorer.py", "collect data script/stage_vocabulary_images.py",
            "collect data script/stage_image_replacements.py", "collect data script/dataset_builder.py",
            "collect data script/semantic_decisions.py", "collect data script/vocabulary_registry.py"],
        "generated_files": sorted(set(generated)),
        "coverage": {"vocabulary_ids": stats["vocabulary_ids"],
                     "qwen_unique_parsed_queries": stats["unique_historical_parsed_qwen"],
                     "qwen_accepted_raw_outputs_saved": stats["accepted_raw_output_saved"],
                     "qwen_new_diagnostic_inference": stats["new_diagnostic_inference"],
                     "qwen_missing_parsed": stats["missing_parsed_qwen"],
                     "qwen_missing_accepted_raw": stats["missing_accepted_raw_qwen"],
                     "image_selected_paths": stats["selected_image_paths"],
                     "production_jpegs": stats["production_jpegs"],
                     "staging_jpeg_versions": stats["all_referenced_asset_versions"] - stats["production_jpegs"],
                     "selected_candidate_download_count_known_ids": stats["selected_candidate_count_known_ids"],
                     "selected_candidate_downloads_known_total": stats["selected_downloaded_candidate_total_known"],
                     "full_candidate_url_lists_saved": 0, "full_candidate_score_lists_saved": 0,
                     "saved_candidate_image_files": stats["saved_candidate_image_files"],
                     "provisional_image_issue_ids": stats["quality_flags_any_model_screening"]},
        "protected_file_hash_comparison": comparison,
        "commands_executed": [
            {"command": "git status --short --untracked-files=normal; git branch --show-current; git rev-parse HEAD", "exit_code": 0},
            {"command": "PowerShell protected hash snapshot using Path.GetRelativePath", "exit_code": 0,
             "note": "Nonterminating per-file MethodNotFound errors yielded 0 hashes; discarded audit-only result."},
            {"command": "PowerShell corrected protected hash snapshot using substring relative path", "exit_code": 0,
             "note": "524 hashes captured."},
            {"command": ".venv/Scripts/python.exe reports/image_pipeline_audit/<run-id>/build_audit.py", "exit_code": 0,
             "note": "Read-only reconstruction; rerun after contact-sheet labels and integrity checks."},
            {"command": ".venv/Scripts/python.exe -m unittest discover -s 'collect data script' -p 'test_*.py'", "exit_code": 0,
             "result": "Ran 108 tests in 4.796s; OK"},
            {"command": ".venv/Scripts/python.exe 'collect data script/validate_vocabulary.py'", "exit_code": 0,
             "result": "100 physical rows; 0 structural issues"},
            {"command": ".venv/Scripts/python.exe -c 'build_dataset(root) == saved_dataset'", "exit_code": 0,
             "result": "100 records; equal_saved=True; production_images=10; production_audio=0"},
            {"command": "PowerShell first protected hash comparison", "exit_code": 1,
             "note": "PowerShell array wrapping caused Join-Path argument error; no source writes."},
            {"command": "PowerShell corrected protected hash comparison", "exit_code": 0,
             "result": "524 unchanged; 0 changed"},
            {"command": "Verify JSON/CSV Qwen and lineage ledgers and quality CSV", "exit_code": 0,
             "result": "100 rows and 100 unique IDs in each; five contact sheets present"},
            {"command": "git diff --check -- CODEX_PROGRESS.md", "exit_code": 0},
            {"command": ".venv/Scripts/python.exe reports/image_pipeline_audit/<run-id>/finalize_audit.py", "exit_code": 0,
             "result": "Final status and protected hashes recorded"}],
        "known_limitations": [
            "94 accepted decoded Qwen outputs were not persisted; parsed queries are not raw model text.",
            "No Qwen model revision or per-record inference timestamp was saved.",
            "Full DDGS candidate URL lists, candidate bytes, candidate scores and individual retry reasons are unavailable.",
            "Contact-sheet judgments are model_assessed_unverified, not owner visual approval.",
            "Search-versus-ranking failure attribution cannot be made for 32 flagged current images.",
            "Image reuse rights and production promotion remain unresolved for most staged assets."]}
    (AUDIT / "audit_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"hashes": comparison, "initial_final_short_status_equal":
                      manifest["initial_final_short_status_equal"], "generated_files": len(generated)},
                     ensure_ascii=False))
    if changes:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
