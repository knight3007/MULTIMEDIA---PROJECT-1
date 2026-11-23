# B-003.1 import-to-media adapter

This adapter reads an **accepted B-002 private import JSON**, verifies the normalized payload fingerprint, and writes a separate processing plan. It does not parse Excel again or call Qwen, search, SigLIP or gTTS. The plan is private preparation metadata, **not** a runtime Content Pack.

From repository root:

```powershell
.\.venv\Scripts\python.exe -B "collect data script\import_pipeline_adapter.py" "reports\b002_import_demo\fixture_private_import.json"
```

Output is created exclusively at `baseline/imports/<import_id>/processing_manifest.json`. A second run with the same import ID fails rather than replacing evidence. Import IDs and item IDs must be canonical UUIDv4; each planned query/candidate/image/audio path is derived from the item ID inside that import's private directory. The adapter rejects redirected private roots and candidate paths outside the current item's directory. The source B-002 JSON and the benchmark files are read-only.

The [three-item manifest](../baseline/imports/imp-3e130d77-9848-4f67-b52a-aab79c2512c7/processing_manifest.json) came from the actual B-002 fixture import. All three items preserve `item_id`, physical `source_row`, English, Japanese, Vietnamese and `target_sense`; all start `pending`, review pending, quality/technical/distribution unknown and image/audio null. Its SHA-256 is `ce831dc7f560e7808ddabff50f1b21cd369b59b9cbed0e59ae1cdbbcd17c4cee`. These are planned paths; no media files were generated.

## Existing boundaries and integration calls

| Stage | Existing callable to reuse in B-003.2 | Adapter evidence and constraint |
|---|---|---|
| Query | `QwenQueryGenerator.generate_batch(words)` and `normalize_query` in `query_generator.py` | English inputs are the accepted import rows. `record_query` uses the existing normalizer; model ID is retained. `prepare_queries` defaults to a global benchmark cache, so use an import-local cache or generator directly. Learner `target_sense` is context, not an approved semantic decision. |
| Retrieval | `search_images(query, ...)` and `normalize_ddg_results` in `imagecollector.py` | `record_candidates` uses the existing URL/result normalizer and binds each candidate to `item_id`; provider/source URLs are private provenance. No result is approved. |
| Candidate validation | `validate_image_bytes` and `normalize_image_to_jpeg` in `imagecollector.py` | `record_candidate_file` validates local bytes, checks private path containment and records SHA-256. JPEG conversion retains FIX-001 white compositing. B-003.2 must save normalized bytes/hashes separately. |
| Ranking | `SiglipImageScorer.score_batch(query, paths)` in `image_scorer.py` | `record_rank` stores finite scores and candidate hashes; it cannot set `image`, review approval or `ready`. |
| Image review | New human decision input after retrieval/ranking | `image_review.decision` remains null until review. `NO_SUITABLE_IMAGE` can be recorded as a failed item with image null and an image-stage error. Do not copy A-003 selections or the internal-only `because` override by matching text. |
| Audio | `synthesize_gtts_mp3(reading, destination, timeout=...)` and `validate_audio` in `audiocollector.py` | Japanese input and provider/locale are recorded; output is planned under the item ID. Existing `stage_japanese_audio.py` relies on canonical registry and 1–10 benchmark IDs, so call lower-level functions from an isolated per-import runner. |
| Pack metadata | B-001 `content_pack_v1.md` | This task records pack ID and pending item state only. B-003.2 must validate actual assets, provenance, review evidence and pack state before a future exporter. No `ready` or public eligibility is inferred. |

`stage_vocabulary_images.py`, `stage_japanese_audio.py`, `imagecollector.main`, `dataset_builder.py` and canonical validators use benchmark IDs, global paths or registry state. They cannot receive imported `item-UUIDv4` IDs unchanged. The adapter uses their lower-level reusable functions and keeps all outputs in `baseline/imports/<import_id>/`; it does not edit those legacy modules. Processing transitions available now are `pending → processing` (`claim_item`) and `processing → failed` (`record_failure`). Successful media and owner review transitions need B-003.2 work and evidence; a ranked image alone remains unreviewed.

## B-003.2 executable work

Request separate authorization for a small live import batch, providers/model revisions, per-stage request limits/timeouts and output budget. Then implement an import-local runner that:

1. Loads this manifest and checks the B-002 import ID, payload hash and item mapping before work; persists each immutable transition without overwriting prior evidence.
2. Calls the existing lower-level Qwen, retrieval, candidate validation/JPEG, SigLIP and gTTS functions against import-local paths. Bind every query, candidate, score and media hash to its `item_id`; retain source/model metadata and sanitized errors.
3. Obtains explicit image and content review. A missing/rejected image remains unavailable. `because` must not inherit the benchmark's internal-only asset by text; any deliberate asset reuse must carry its restriction and stay out of public packs.
4. Validates both asset bytes and B-001 state prerequisites before `needs_review` or `ready`; a future Content Pack exporter must be a separate, verified step. No Game UX/UI work is implied.

Offline checks: `.\.venv\Scripts\python.exe -B -m unittest "collect data script/test_import_pipeline_adapter.py" -v`. Tests feed synthetic search results and a local fixture PNG to the adapter; these are **not** real AI/network outputs. B-002's Unicode 15.1/16.0 mismatch and public-upload resource limits remain open.
