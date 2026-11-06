# Controlled media production plan — 2026-10-29

**Current checkpoint:** no bulk collection was run. Image replacement history and current licensing decisions are in [image_replacement_review.md](image_replacement_review.md); no image was promoted. The [five-word Japanese audio pilot](japanese_audio_pilot_review.md) and [Batch 2](japanese_audio_batch_2_review.md) staged ten valid MP3s in total; the owner approved listening quality for those exact hashes. [Batch 3](japanese_audio_batch_3_review.md) staged ten more MP3s for IDs 011–020, pending listening review. Production still has 10 images under review, 90 missing images and 100 missing Japanese MP3s; the saved dataset still has no public media URLs.

## Environments and preflight

| Work | Environment | Current dependency file | Verified CLI |
|---|---|---|---|
| Images, Qwen, DDG, SigLIP2, builder/tests | `.venv` | `requirements.txt` | `imagecollector.py`: `--vocabulary`, `--qwen-model`, `--qwen-batch-size`, `--qwen-cache`, `--page-size`, `--siglip-model`, `--siglip-device`, `--siglip-dtype`, `--limit`, `--timeout`, `--retries`, `--retry-delay`, `--rate-limit-delay`; replacement staging runner: bounded timeout/retry/page size and SigLIP device/dtype flags |
| Japanese gTTS MP3 | `.venv-audio` | `requirements-audio.txt` | `stage_japanese_audio.py`: repeated `--vocab-id`, `--run-id`, `--resume`, `--timeout`, `--retries`, `--retry-delay`, `--rate-limit-delay`, `--no-smoke-reuse`; legacy direct collector retains its existing CLI |

Both `pip check` commands passed on 2026-10-29. Keep the environments separate because their `click` requirements conflict. Before each production run, record Git status, manifest/registry/ledger hashes, source row count, free disk, model cache readiness, existing asset hashes and a writable isolated staging location. Confirm DDG connectivity with a single isolated request before scheduling more images. Do not change the Qwen prompt/cache or SigLIP model to work around a network failure.

The current image CLI writes directly to `data/image/en/` and takes a cumulative `--limit`, not an ID range or safe output directory. The two-item [replacement staging runner](../collect%20data%20script/stage_image_replacements.py) is intentionally restricted to rows 4 and 9. **Before collecting the other 90 images**, add and test an explicit-ID, bounded-batch staging mode that reuses the current Qwen → DDG → SigLIP path and records each ID/query/candidate/result in a unique run directory. Do not use a temporary reordered vocabulary file: that can invalidate Qwen cache alignment and stable ID joins. The existing image collector refuses to overwrite a conflicting JPEG/metadata pair, but direct production output does not provide the review/promotion boundary desired for all new images.

## Two known replacements

The earlier failed DDGS run is historical. Later Bing staging and a rights-reviewed Commons chicken candidate succeeded; see [image_replacement_review.md](image_replacement_review.md). The command below is retained as the historical two-target procedure and is not part of the audio pilot:

```powershell
.\.venv\Scripts\python.exe "collect data script/stage_image_replacements.py" --timeout 8 --retries 1 --retry-delay 1 --page-size 3 --rate-limit-delay 1 --siglip-device auto --siglip-dtype auto
```

This runner reads the current dataset decisions and uses `cooked rice` and `chicken meat` directly. It does not call Qwen, rewrite its cache, or touch production paths. Each run gets a unique `baseline/media-staging/images/<run-id>/` directory and a manifest with ID, target sense, query, retrieval outcome, selected source URL, SigLIP selection, local JPEG and validation/failure state. Review the old and staged image side by side. The owner must approve each actual candidate before the separate promotion procedure in [image_replacement_review.md](image_replacement_review.md). The 2026-10-29 attempt returned two DDG timeouts and no candidate; do not treat it as success.

## Ninety missing images

After the explicit-ID staging mode is tested, start with one ID, then batches of at most five. Use `--page-size 3`, `--timeout 8`, `--retries 1`, `--retry-delay 1` and at least one second between words as initial bounded settings. Record each run's ID list, successful/failed counts, exact query provenance, DDG URLs, candidate validation, SigLIP scores and staged paths. Retry only failed IDs in a new run after checking the cause; a failed URL must not stop the rest of a batch. Keep all candidates and failures outside production until review. A high SigLIP score is a ranking result, not semantic approval.

The 20 flagged, still-pending semantic entries need individual sense review before their images can be called suitable. The 77 unflagged entries are also not independently approved; collected files remain `needs_review` until image review is recorded. Use the stable `vocab_id` and current source triple for every batch record; filenames and source row hints are not identity. The current query cache contains only ten generated records, so subsequent image batches may invoke local Qwen and require its model/runtime. Stage and validate the exact query used for both DDG and SigLIP. Do not silently edit the signed Qwen cache.

## One hundred production Japanese MP3s

The current production directory is `data/audio/jp/`, with `data/audio/jp/_metadata/`; it still has no MP3s. `stage_japanese_audio.py` reads the canonical EN/JP/VN files and persisted ID registry, selects 1–10 explicit stable IDs, and redirects the existing gTTS collector to a unique `baseline/media-staging/audio/<run-id>/` directory. It writes a per-ID manifest with reading, source row, provider/voice, relative MP3 and metadata paths, duration, size, SHA-256, cache origin and failure. Valid smoke files are copied only after complete MP3, path, reading, provider, locale, voice, size, duration and row-key checks; the old smoke files remain untouched. The [five-word pilot](japanese_audio_pilot_review.md) used this path successfully.

The **completed second controlled batch** selected IDs 6–10 explicitly with this command:

```powershell
.\.venv-audio\Scripts\python.exe "collect data script/stage_japanese_audio.py" --vocab-id vocab-000006 --vocab-id vocab-000007 --vocab-id vocab-000008 --vocab-id vocab-000009 --vocab-id vocab-000010 --timeout 12 --retries 1 --retry-delay 2 --rate-limit-delay 1
```

The pilot and Batch-2 listening gates were satisfied before further collection. Wait for Batch-3 per-hash listening decisions before any further expansion. After each later run, inspect its manifest and listen to every new MP3. If a run stops partway, rerun with the same exact `--vocab-id` list plus `--run-id <existing-id> --resume`. A valid staged MP3/metadata pair with the recorded hash becomes a cache hit; a failed item with no artifact can be attempted again. A corrupt file, missing/stale metadata, or SHA mismatch is reported as a conflict and preserved for review. To retry such an item after investigation, use a **new** run ID; do not overwrite the old evidence. The direct collector now also refuses existing MP3/metadata conflicts and stops retrying if a valid MP3 was written but metadata failed.

Use bounded timeouts and at least one second between new requests, including after a transient failure. A 403/429 is not retried; the staging runner skips later new provider requests in that batch while still allowing verified local cache reuse. Record per-ID failures and do not bypass provider limits. Avoid a reordered temporary vocabulary file, which would break row-bound keys and stable ID association. Cache hits and verified smoke copies avoid unnecessary downloads; never count a WAV as an MP3.

No staged file changes production availability. After per-hash listening and usage-rights review, a separate authorized promotion must back up any old production MP3/metadata, verify staged bytes and metadata, atomically install the chosen file/metadata with canonical `data/audio/jp/` paths, and rebuild/check the unified dataset. The current builder will still mark a valid production MP3 `needs_review` with a null public URL; a tested media-approval rule is required before public/game-ready exposure.

The three validated smoke files (`りんご`, `バナナ`, `いちご`) **can be reused without changing their MP3 bytes**, but they are not production assets now. First verify reading, provider `google_translate_gtts`, locale `ja`, voice `{tld: com, slow: false}`, format, complete frames, duration, size and hashes. With a separate promotion decision, copy bytes to their canonical production paths, create new metadata whose `audio` path points to `data/audio/jp/<reading>.mp3`, retain the smoke originals and record source paths/hashes in a provenance log. Copying the old metadata unchanged would fail production cache validation because its `audio` path names `baseline/`. Rebuild the dataset afterward; current valid production audio still receives `needs_review` and null public URL until an audio review policy is recorded.

## Storage, promotion and QA

The existing 10 final JPEGs total 1,421,747 bytes (median 139,412 bytes), and three smoke MP3s total 22,080 bytes. At preflight the workspace volume reported 96,741,998,592 free bytes. Final media may be small, but raw DDG candidates can be much larger; recheck free space before every batch and keep at least a comfortable gigabyte of headroom for temporary candidates, backups and models. Do not extrapolate exact final size from the ten samples.

Maintain a per-run manifest under `baseline/media-staging/` and a checklist of IDs: `missing → staged/failed → human reviewed → backed up/promoted → manifest rebuilt/QA`. Preserve failed outputs as evidence; do not overwrite old JPEGs, MP3s or metadata. For promotion, verify the candidate and metadata, obtain per-asset owner approval, back up old files with hashes, use same-directory temporary files plus atomic replacement, rebuild `data/vocabulary/unified_dataset_v1.json`, and compare stable IDs, provenance, asset paths and counts. Add a persisted media-review record and tested builder rule before claiming an asset is `available` or exposing a public URL; the current builder intentionally keeps all present media in `needs_review`.

After each batch, run the focused collector/builder tests, full offline suite, vocabulary validator and builder, then manually inspect sampled images and listen to MP3s. Record actual commands, exit codes, failures and asset hashes in `CODEX_PROGRESS.md`. Do not start backend/game integration from technical presence alone.
