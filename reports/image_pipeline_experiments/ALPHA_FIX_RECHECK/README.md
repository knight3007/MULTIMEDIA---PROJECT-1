# Alpha-fix re-check (offline)

Date: 2026-11-22. The owner approved fixing the black-background defect found in A-003 ("Sửa lỗi nền đen").

## Change (production code)

- `collect data script/image_scorer.py`: new `flatten_to_rgb(image, background=white)`. RGBA, LA, PA and palette-with-transparency images are composited onto white. Other modes use a plain `convert("RGB")`, so their behaviour is unchanged. `SiglipImageScorer.score_batch` now uses it.
- `collect data script/imagecollector.py`: `normalize_image_to_jpeg` uses `flatten_to_rgb(ImageOps.exif_transpose(...))` instead of `.convert("RGB")`.
- `collect data script/test_collectors.py`: 2 new tests.
  - Transparent RGBA PNG, palette PNG, LA PNG and RGBA WebP come out white, not black, and the opaque content is kept.
  - Opaque, greyscale and half-transparent images flatten correctly.
  - The test fails on the old code (corner pixel ≈ (0, 0, 0)) and passes with the fix.
- Not changed: queries, Qwen, routing, SigLIP model and score formula (logits), page size, dataset, registry and production images. `data/image/en/` was produced before the fix; none of its 10 images is affected (all came from opaque sources).

## Re-check of existing downloads

`recheck_alpha.py` uses no network. It re-normalizes and re-scores every arm that has a transparent raw candidate. Outputs go to `images/` and `recheck_results.json`; the original experiment files are read-only, and their hashes are asserted unchanged.

| Source | Arms with transparency | Black squares before → after | Selection changed |
|---|---|---|---|
| A003_CONDITIONAL_SEARCH | 13 | 8 → 0 | cat, mountain, buy, happy (ICON) |
| A002_ICON_PILOT_20 | 18 | 4 → 0 | easy, work |

## Observations (AI preliminary)

- *car icon* was 6/7 black squares; all are now clean car pictograms. Its earlier NORMAL_BETTER judgment was partly caused by the defect.
- The new SigLIP picks are not consistently better:
  - work → an icon-sheet collage.
  - happy → an image with an ICON-ICONS watermark.
  - buy → still a "BUY" text button.
  - This supports the A-003 recommendation: use a dual pool plus rejection rules plus a human pick, not SigLIP's top score.
- Fake checkerboard "transparency" drawn into the pixels (cat icons) is not fixed by this change. It needs a detection or rejection rule.
- The A-003 and pilot galleries still show the pre-fix images, which is historical evidence. Use this folder's `images/` to see the fixed versions.
