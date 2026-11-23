# FIX-001 verification — transparency compositing

Date: 2026-11-22. Branch `main`, HEAD `936d9fdd27810e50a144fb6399e647b1ba18c371`, uncommitted. Owner approval: "Sửa lỗi nền đen" (D-017).

- Diff: `image_scorer.py` +15/−1, `imagecollector.py` +2/−1, `test_collectors.py` +33.
- New tests:
  - `test_transparent_images_are_flattened_onto_white_not_black` covers RGBA PNG, palette PNG with transparency, LA PNG and RGBA WebP.
  - `test_flatten_to_rgb_keeps_opaque_images_unchanged`.
- Negative control: with the old `.convert("RGB")` temporarily restored, the transparent test failed with corner pixels (0,5,2), (0,5,2), (0,0,0) and (0,2,0). The fix was restored and confirmed (`grep` count 1).
- JPEG chroma noise put a white corner at 244, so the threshold is ≥ 230; black is ≈ 0.
- Suites: collector 162 OK; kaggle_batch 19 OK; validate_vocabulary 0 structural issues; `git diff --check` clean.
- Import constraints: `audiocollector` still loads no image modules (existing test passes). `imagecollector` now imports `image_scorer` at module level; that module imports only PIL at top level, and the torch/transformers-free CLI test passes.
- Offline re-check (`reports/image_pipeline_experiments/ALPHA_FIX_RECHECK/recheck_results.json`): A-003 has 13 transparent arms, black squares 8→0, selection changed 4. The pilot has 18 arms, black squares 4→0, selection changed 2. The source result files' hashes were asserted unchanged. No network or Qwen use.
- Not done: no regeneration of `data/` or experiment galleries; baked-in checkerboard images are not handled.
