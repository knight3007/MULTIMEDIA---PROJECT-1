# A-004 partial-run verification — 2026-11-23

Status: **PARTIAL, stopped after the owner requested only a report of work already run.** The automatic approval reviewer rejected the command to continue 90 image IDs because the workspace was out of credits. It explicitly said this was a review failure, not a safety determination, and not to bypass the approval check. That command did not execute. No network retry or cached-image substitution was attempted afterward.

## Frozen configuration and execution

- Source: 100 unique IDs in `data/vocabulary/unified_dataset_v1.json`, SHA-256 `644c2dc9899077dad15d2e2916d7dc3d1cef49ecd151ea406115bb3da19481bd`; 100-row `frozen_vocabulary.csv` and exact Git/status/model/prompt/provider/scoring/environment information in [manifest](../../reports/image_pipeline_experiments/A004_FULL_100_RERUN/experiment_manifest.json). Branch `main`, HEAD `936d9fdd27810e50a144fb6399e647b1ba18c371`.
- Model preflight: Qwen3-1.7B local snapshot loaded offline, dtype float16 with CUDA/CPU offload; SigLIP `google/siglip2-so400m-patch16-384` local snapshot loaded offline on CUDA float16. No new model download. Source hashes frozen before inference; FIX-001 white transparency compositing source verified.
- Qwen phase: 100 IDs attempted once each, raw outputs saved atomically. 94 normalized queries valid; 93 effective queries available, six invalid `verb` outputs, one approved semantic decision missing image-search intent (ID038). No correction pass or query cache substitution.
- Image phase: IDs 001–010 attempted; 10 searches succeeded, 64 candidate records, 50 raw/JPEG downloads valid and 14 failed, 9 SigLIP rankings, one ID with no valid candidate (ID008; sole URL HTTP 404). The 90 other IDs were not attempted. One search/ID, at most 7 candidates/ID, 20 s timeout, 0 retries, one SigLIP score pass/ID. Per-ID attempts and batch progress are saved atomically in `query_results.json`, `retrieval_results.json` and manifest. A rejected continuation performed no work.
- `finalize_partial.py` verified all 50 raw and JPEG SHA-256 values and JPEG/underlying image validity, 100 unique evaluation-matrix IDs, per-candidate score associations, frozen dataset and vocabulary hashes; its [archived report](../../reports/image_pipeline_experiments/A004_FULL_100_RERUN/evaluation_report_partial_10.md) and `evaluation_matrix_partial_10.csv` preserve the then-current results. Nine top-1 images and relevant pools were visually inspected in contact sheets, with judgments marked AI_PRELIMINARY. Audio: 100/100 existing A-001 references matched SHA-256; no regeneration.

## Regression and integrity checks

- `.\.venv\Scripts\python.exe -B -m unittest discover -s "collect data script" -p "test_*.py" -q`: **174 tests OK**.
- `.\.venv\Scripts\python.exe -B -m unittest discover -s kaggle_batch/tests -p "test_*.py" -q`: **19 tests OK**.
- `.\.venv\Scripts\python.exe -B "collect data script\validate_vocabulary.py"`: **100 physical rows, 0 structural issues**.
- `git diff --quiet -- data/vocabulary/unified_dataset_v1.json`: exit 0, content unchanged. `git diff --check`: exit 0 with existing CRLF conversion warnings only. No production image/audio, registry, A-002/A-003, owner decision, B-002 or B-003.1 asset was written.

Output directory: `reports/image_pipeline_experiments/A004_FULL_100_RERUN/`. Created experiment scripts, frozen config/vocabulary, raw query and retrieval ledgers, 50 raw+JPEG pairs, candidate/evaluation CSVs, contact sheets and partial report. **No full review gallery or owner export** was built after the owner narrowed the request to the report; image-quality review is 9/100 AI_PRELIMINARY only. B-003.2 remains paused; Game UX/UI remains undecided. Next action is owner/workspace-credit resolution followed by a new explicit request if the remaining 90 image IDs should run from the frozen ledger; do not bypass approval or silently repeat completed IDs.
