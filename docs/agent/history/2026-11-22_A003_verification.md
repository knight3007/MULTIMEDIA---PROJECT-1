# A-003 verification — conditional image search holdout

Date: 2026-11-22. Session: Claude Code on `main`, HEAD `936d9fdd27810e50a144fb6399e647b1ba18c371`. No commit or push.

## Interjection handled first (D-016)

- The owner asked to put the "because" V3-01 image "into the dataset".
- Adding `data/image/en/because.jpg` plus metadata and rebuilding produced a diff limited to vocab-000081. However, it changed the `unified_dataset_v1.json` hash `644c2dc9…`, which six historical experiment manifests pin as an input, and caused 1 failure and 12 errors in the collector suite.
- The change was fully reverted. `git checkout` restored the file with CRLF line endings, so the builder was rerun to restore the original LF bytes. The SHA-256 is back to `644c2dc9…`, the blob equals the index, and the suite is back to 160 OK.
- Git may still list the file as modified because of cached file timestamps; `git diff --quiet` exits 0.
- Owner chose the internal override file: `data/vocabulary/internal_image_overrides_v1.json`, recorded as decision D-016. Tests: 160 OK.

## A-003 run

- The sample was frozen with `run_a003.py --freeze` before any request: 12 IDs; the SHA-256 of `frozen_sample.csv` is in the manifest. Excluded IDs were asserted in code. No substitution.
- 24/24 searches SUCCESS (12 NORMAL, 12 ICON). Settings were identical for both arms: production defaults of timeout 20 s, search retries 2, download retries 2, page size 7, DDG `wt-wt` moderate.
- Candidates: NORMAL 81 records / 74 downloaded; ICON 77 / 73. *sometimes icon* returned only 1 result. Failures were HTTP 402/403/404 and non-image payloads.
- SigLIP (`siglip2-so400m-patch16-384`, CUDA) ranked 24/24 arms against the arm's own query, plus shared scores against the bare English word.
- The run took longer than the 10-minute foreground limit and finished in the background. Because results are written per pair, nothing was lost or repeated.

## Checks

| Check | Result |
|---|---|
| Unique IDs / pairs | 12 / 24; queries match the frozen normal query and `english + " icon"` exactly |
| Hashes | 294 files (147 raw + 147 JPEG) match; 0 orphans; 0 missing |
| Frozen inputs | imagecollector.py, image_scorer.py, collector_common.py, the A-001 matrix and unified_dataset_v1.json all equal their freeze-time hashes |
| Isolation | Only `data/vocabulary/internal_image_overrides_v1.json` (D-016) is new under data/. Pilot directories, the causal directory, phase0 reports, baseline and source are unmodified. |
| Gallery | Served on 127.0.0.1:8767 in the pane's tab. 12 cards with NORMAL (blue) and ICON (purple) arms; 183/183 images loaded; preference select, per-arm NO_SUITABLE_IMAGE checkbox and notes. Export produced `HUMAN_REVIEW_DRAFT_NOT_AUTO_APPROVAL` with 12 items. The patched functions were restored immediately, the page reloaded and the draft cleared. No horizontal overflow at 375 px. Server stopped. |
| Tests | collector suite 160 OK; kaggle_batch 19 OK; validate_vocabulary 0 structural issues |

## Finding

`normalize_image_to_jpeg` and `score_batch` use `.convert("RGB")` without compositing transparency, so transparent pixels become black.
- A-003: ICON has 29 transparent candidates and 8 black squares; NORMAL has 3 and 0.
- A002_ICON_PILOT_20: 61 of 129 candidates were transparent, and 10 of 20 selected icons were flattened.
- Not fixed (that would be a production change). Proposed as the first fix in the report.

## Not established

- Human labels (0/12).
- Rights.
- Results after the alpha fix.
- Random-sample generalization.
