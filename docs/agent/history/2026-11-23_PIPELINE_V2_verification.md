# PIPELINE-V2 verification

Date: 2026-11-23. Branch `main`.

- **Owner export:** `D:/Download/A004R-followup-review-2026-11-23.json` was copied to `A004R_FINAL_SELECTION/owner_followup_export.json` (identical SHA).
  - `finalize.py` checked the task ID, plan export SHA and 100 unique IDs.
  - Carried-forward rows equal the frozen plan; open rows are PASS with existing path and hash.
  - Every selected file's SHA matches. The origin of each image was traced to its experiment and query.
- **Registry:** `build_registry.py` wrote `data/vocabulary/approved_images_v1.json` (100 entries, unique EN+JP+VN keys, hashes verified; `because` keeps INTERNAL_ONLY_TEMPORARY). The dataset SHA is still `644c2dc9…`.
- **Code:** `query_generator.py` was briefly given a `system_prompt` parameter. That broke 13 tests guarding benchmark inputs (the hash is pinned), so it was reverted; `git diff` is empty. Prompt v2 generation lives in `visual_query_policy.generate_typed_raw`, which mirrors the original logic.
- **Technical rejection:**
  - The detector was calibrated on real data: none of the 100 approved images is rejected.
  - Of 1,171 historical candidates, 3 are rejected: 2 at 96 px and 1 true checkerboard. Two earlier false positives (a maze and a slide) were removed by requiring two balanced levels with at least 45% coverage.
- **Tests:** `test_image_pipeline_v2` 13 OK; the collector suite was rerun before the commit (see the commit message).
- **Validation:** 3 prompt iterations (iter01 to iter03), expected routes frozen before inference, prompt examples outside the benchmark (tested).
  - Iter03: PHOTO 44/44, NON_PHOTO 34/35, CURATE 1/1, valid 99/100 → NOT PASSED.
  - Iter01 used an earlier code path (a `system_prompt` parameter); iter02 and iter03 use the final `generate_typed_raw`.
- **Cleanup:** 5 project `__pycache__` folders deleted (regenerable). Experiment media, logs and empty folders are kept locally.
- **Push:** the owner chose code and docs only, straight to `main`, without the personal notes or the Kaggle notebook. Images (.jpg, .img, .mp3, .png, .wav outside test fixtures) and the 5.6 MB follow-up gallery stay local.
