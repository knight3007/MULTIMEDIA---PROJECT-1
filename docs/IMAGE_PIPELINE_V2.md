# Image pipeline v2 (candidate)

Status: **CANDIDATE, not frozen** (2026-11-23, decision D-020 PROPOSED). Validation iteration 3 met the routing criteria (PHOTO 44/44, NON_PHOTO 34/35, CURATE 1/1) but missed 100% valid queries (99/100), and the review found example-copying in some queries; see `validation_report.md`. Freezing needs an owner decision.

## Evidence it is based on

The owner-reviewed final selection covers all 100 benchmark words: `reports/image_pipeline_experiments/A004R_FINAL_SELECTION/final_selection_manifest.json` (reviewer HD, 100/100 PASS images). The query strategy that produced each approved image:

| Word kind | Approved strategy (count) | Examples |
|---|---|---|
| Concrete nouns: food, animals, places, objects, people | Qwen `<word> <class>` photo (58) | apple fruit, hospital institution |
| Verbs, adjectives, greetings, question words | Descriptive `… icon` (21) or `<word> icon` (10) | person reading book icon, person waving hello icon |
| Time and abstract nouns | Descriptive `… illustration` scene (10) | tomorrow next day calendar illustration |
| Connectors | Hand-curated (1) | because |

Failures seen across A-002 to A-004R motivated the remaining rules:
- **Sense drift** from noun-class suffixes on non-nouns: "buy action", "book object", "sun illumination".
- **Brand and word collisions**: "Action" store and rifles, "Being Single", Apple logos.
- **Transparency flattened to black** (fixed by FIX-001).
- **SigLIP preferring text or logos.**

## Pipeline per item

1. **Approved reuse.** If EN, JP and VN all match an entry in `data/vocabulary/approved_images_v1.json` exactly (case- and space-insensitive), reuse that image. Its `usage_restriction` and `rights` are carried over (`because` stays `INTERNAL_ONLY_TEMPORARY`). Matching on text alone never reuses an image.
2. **Classify and write the query (Qwen3-1.7B, prompt v2 `TYPED_PROMPT`).** Output is `TYPE | query`.

   | TYPE | Route | Query style (enforced in code) |
   |---|---|---|
   | CONCRETE | PHOTO | The word exactly once plus one broad class. Must not end in icon or illustration. |
   | ACTION, STATE, SOCIAL | ICON | Descriptive phrase; the suffix ` icon` is enforced. |
   | TIME, ABSTRACT | SCENE | Descriptive phrase; the suffix ` illustration` is enforced. |
   | CONNECTOR | CURATE | No search. Status `NEEDS_CURATION`: a person picks or curates an image, or records `NO_SUITABLE_IMAGE`. |

   Non-photo queries must not contain `action`, `object`, `single`, `logo`, `brand`, `word`, `text` or `letters`. An invalid output gets one corrective retry and then fails explicitly.
3. **Search.** DuckDuckGo via `imagecollector.search_images`, 7 results, 20 s timeout, 2 retries with a 2 s delay. A search failure is recorded as `SEARCH_FAILED` and never produces an image.
4. **Download and normalize.** `download_candidate_image` with 2 retries, then `normalize_image_to_jpeg` (white compositing of transparency, FIX-001).
5. **Technical rejection** (`technical_rejection`): shorter side < 100 px; near-uniform image (luma stddev < 6); baked-in checkerboard (two near-equal light grey levels covering ≥ 45 % of the image and alternating on both axes). Semantic problems (wrong sense, prominent text, watermarks) are left to the reviewer.
6. **Rank and propose.** SigLIP `google/siglip2-so400m-patch16-384` scores the usable candidates against the query. The top one becomes a **proposal**, the next 4 are kept as alternatives, and the status is always `needs_review`. With no usable candidate the result is `NO_SUITABLE_IMAGE`.
7. **Review.** A person confirms or changes the proposal. Nothing becomes approved or public automatically, and rights stay unknown until cleared.

## Code (files recorded in freeze_manifest.json)

- `collect data script/visual_query_policy.py`: `POLICY_VERSION = "image-pipeline-v2"`, `TYPED_PROMPT`, routing and styling, rejection, `propose`, `lookup_key`.
- `collect data script/image_pipeline_v2.py`: `process_item` for one item (dependencies injectable) and the `run`/CLI batch.
  - Usage: `.\.venv\Scripts\python.exe -B "collect data script\image_pipeline_v2.py" items.json out_dir`, where `items.json` is `[{item_id, english, japanese, vietnamese}]`.
  - Qwen is released before SigLIP loads.
- `collect data script/query_generator.py`: unchanged v1 prompt and cache. `_generate_raw` accepts `system_prompt` (v1 is the default).
- `collect data script/imagecollector.py`, `image_scorer.py`: FIX-001.
- `data/vocabulary/approved_images_v1.json`: 100 owner-approved images. It is not read by `dataset_builder`, so `unified_dataset_v1.json` stays frozen at `644c2dc9…`.
- Tests: `collect data script/test_image_pipeline_v2.py` (offline, with mocks).

SHA-256 values of the frozen files are recorded in `reports/image_pipeline_experiments/PIPELINE_V2_VALIDATION/freeze_manifest.json`.

## Validation

See `reports/image_pipeline_experiments/PIPELINE_V2_VALIDATION/`. Expected routes were frozen from the owner selection **before** any v2 inference (`expected_routes.csv`, `acceptance_criteria.json`). Prompt examples use only non-benchmark words. The results are in `validation_report.md`.

## Out of scope

- Running v2 on Excel imports (B-003.2 runner wiring): `process_item` is the integration point, and live import processing still needs its own authorization.
- Public release or rights clearance.
- Game UX/UI (D-014).
- Promotion into `data/image/en/` or `unified_dataset_v1.json`.
