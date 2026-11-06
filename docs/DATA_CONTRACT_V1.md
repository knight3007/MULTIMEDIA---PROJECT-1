# Vocabulary data contract v1 — implementation checkpoint

**Current status (2026-10-28):** The offline v1 builder is implemented. The sections headed “Original design notes” below preserve the proposal and illustrative pre-approval examples for traceability; this checkpoint states the actual behavior when they differ.

## Implemented sources and regeneration

- Source vocabulary: `data/vocabulary/{en,jp,vn}.txt`, 100 physical rows each. The only new semantic text correction is Vietnamese row 38, `bạn bè` → `bạn`; the earlier approved EN row 91 whitespace cleanup remains in place.
- Persistent ID registry: `data/vocabulary/id_registry_v1.json`, exactly 100 unique IDs `vocab-000001` … `vocab-000100`. Each entry stores its current exact EN/JP/VN triple, original row hint and edit history. Row 38's old triple is in its history. The builder matches exact triples, so reordering retains IDs; an unrecorded edit, ambiguous mapping or count change fails. `vocabulary_registry.initialize_registry(rows, path)` is an explicit one-time operation using exclusive file creation; the builder never initializes or rewrites the registry. Future additions require explicit registry assignment before a build.
- Semantic ledger: `data/vocabulary/semantic_decisions_v1.json`. Exactly rows 4, 9 and 38 have `owner_approved` records. The other 20 flagged rows have context-only annotations and remain `needs_decision`; 77 unflagged rows remain `unreviewed`. `target_sense` is null outside the three approvals. Optional written forms are annotations; the original kana remains both display and reading.
- Builder: `collect data script/dataset_builder.py`. Run `.\.venv\Scripts\python.exe "collect data script/dataset_builder.py"`. Output: `data/vocabulary/unified_dataset_v1.json` with `schema_version: 1` and exactly 100 records. It runs offline, reads only the normal production asset directories, validates source/registry/metadata/media, writes UTF-8 JSON through a temporary file and atomic replacement, and emits no timestamp. A validation failure leaves the prior manifest intact.
- Regeneration does not run Qwen, DDG, SigLIP or gTTS. The three MP3 files in `baseline/gtts-smoke-2026-10-28/` are excluded from production coverage.

## Implemented record and asset adjustments

The original v1 record shape below is retained with three additive fields: `decision_provenance` (`owner_approved` or null), `annotation_status` (`context_added_pending_review` or null), and `image.effective_search_query` (approved intent if present, otherwise the recorded model query). `image.final_search_query` is the query recorded for the **existing saved JPEG**, so for rice/chicken it remains `rice grain`/`chicken animal`; `image.target_search_sense` and `image.effective_search_query` are the approved future retrieval intent. The difference is intentional evidence of mismatch, not a cache rewrite. `image.semantic_suitability` is `mismatch` for those two, otherwise `unverified`. The builder never emits a public asset URL yet.

At this checkpoint, 10 production JPEGs and metadata files exist; all 10 manifest image entries are `needs_review`, including two known mismatches. The other 90 images are `missing`. Production Japanese MP3 coverage is 0/100, so all audio entries are `missing`. Physical asset presence is distinct from semantic approval. A later asset review is required before any image or audio becomes `available` or receives a public URL. Invalid or orphaned metadata and malformed existing media fail the build rather than being silently promoted.

The image collector applies approved query intents only with the canonical vocabulary file, after Qwen query preparation and before DDG retrieval and SigLIP ranking. Its cache check requires the effective query and provider, and an approved cache also requires `human_approved` query provenance. If an old JPEG or metadata conflicts, the collector fails that word without replacing either file. Row 38 has an approved singular sense but no approved image intent, so image collection holds that item and continues the rest of the batch. Therefore a normal image run cannot yet replace the two mismatched files; use a separately reviewed migration/output path later. The existing Qwen cache is unchanged.

## Original design notes and pre-approval examples

**Historical status:** this was the Phase I design draft before the three owner approvals and builder implementation. Its example records and “future” language below describe that earlier point in time; consult the implementation checkpoint above and the generated manifest for current values. No backend or frontend implements this contract yet.

## Purpose and boundaries

One internal record links the three source vocabulary strings to an intended meaning and any collected media. The offline builder will eventually produce records; a future backend or static publisher will expose only approved fields and safe asset URLs. The web/game will play stored MP3s locally and will never call Google Translate during playback.

The current source of truth is the physical row pairing in `data/vocabulary/{en,jp,vn}.txt`, with Qwen cache, JPEG metadata, and gTTS MP3 metadata as supporting evidence. The present 10 JPEGs and three isolated smoke MP3s do not imply a complete dataset. This document does not change collectors or create a manifest.

## Record shape

| Field | Type | Required | Rule |
|---|---|---:|---|
| `schema_version` | integer | Yes | Exactly `1` for this design. A breaking change increments it. |
| `vocab_id` | string | Yes | Immutable, unique ID from a persisted registry; never derived at runtime from row or text. |
| `source_row_index` | integer | Yes | Current 1-based physical row for provenance only; it can change on reorder. |
| `english` | nonempty string | Yes | Original EN display term, without structural trailing whitespace after approved cleanup. |
| `japanese` | object | Yes | `display` and `reading` are required nonempty strings; `written_form` is optional string or null. Current kana may be both display and reading. |
| `vietnamese` | nonempty string | Yes | Meaning used for both EN and JP in the learning item; never silently machine-translated. |
| `target_sense` | string or null | Yes | Null until a specific meaning is owner-approved. A recommendation cannot populate this as approved data. |
| `part_of_speech` | string or null | No | Use when it prevents ambiguity; avoid inventing a value for every row. |
| `usage_note` | string or null | No | Register, context, or example guidance after review. |
| `review_status` | enum | Yes | `unreviewed`, `needs_decision`, or `approved`; independent of asset status. |
| `image` | object | Yes | English JPEG association, query and provenance, technical reference, asset state. |
| `audio` | object | Yes | Japanese reading, gTTS MP3 reference, technical reference, asset state. |

`review_status=approved` requires an explicit decision record naming the stable ID, target sense or accepted broad sense, reviewer, decision time, and rationale. The 77 unflagged rows start `unreviewed`; the 23 flagged rows start `needs_decision`. This mapping is a proposed migration rule, not a claim that a registry or manifest exists now.

### Image object

| Field | Type | Rule |
|---|---|---|
| `status` | `missing` / `needs_review` / `available` | `missing`: no valid production JPEG. `needs_review`: file parses but its semantic suitability is unknown or disputed. `available`: valid production JPEG with approved intended sense and image review. Parsing alone never yields `available`. |
| `path` | relative path or null | Internal source path, e.g. `data/image/en/apple.jpg`; must exist and decode if non-null. Never return a Windows absolute path to clients. |
| `url` | root-relative URL or null | Future public path, e.g. `/assets/images/en/apple.jpg`; null until the image is approved for consumption. |
| `source_english` | string | Must match record `english`; prevents a wrong-word metadata join. |
| `target_search_sense` | string or null | Approved image meaning/search intent, distinct from a model-generated query; null before approval. |
| `final_search_query` | string or null | Exact query sent to both DDG and SigLIP for the saved image. |
| `query_provenance` | `model_generated_unreviewed` / `human_approved` / null | Indicates how the final query was selected, not whether an image is good. |
| `provider` | string or null | Existing provider is `duckduckgo`. |
| `ranking` | object or null | Existing winner metadata may identify `siglip2`, model and raw score. A score is not a calibrated probability or human approval. |
| `metadata_ref` | relative path or null | Existing `data/image/en/_metadata/<word>.json` when present. |

The current image metadata uses `word`, `search_query`, `provider`, URLs, and optional `image_selection`; it has no final output-path or human-review field. The builder must check word/query alignment and JPEG decoding rather than treating metadata existence as sufficient. Rows 4 and 9 currently have technically valid but semantically drifted images, so their proposed status is `needs_review` with no public URL.

### Audio object

| Field | Type | Rule |
|---|---|---|
| `status` | `missing` / `needs_review` / `available` | `missing`: no valid production MP3. `needs_review`: MP3/metadata parse but quality or mapping awaits review. `available`: valid production MP3 and required review policy satisfied. Smoke files never count as production assets. |
| `reading` | nonempty string | Must equal `japanese.reading`; it can differ from `japanese.display` or `written_form`. |
| `path` | relative path or null | Internal `data/audio/jp/<safe-stem>.mp3` path; null if absent. Legacy WAV is never an MP3 substitute. |
| `url` | root-relative URL or null | Future `/assets/audio/ja/<safe-stem>.mp3` path; null until approved for consumption. |
| `provider` | string | Current `google_translate_gtts`, not Google Cloud TTS. |
| `locale` | string | `ja` for the current Japanese collector. |
| `voice` | object | Current `{"tld":"com","slow":false}`; preserve exact options for cache matching. |
| `format` | string | `mp3` for the current collector. |
| `duration_seconds` | nonnegative number or null | From a validated MP3, null when missing. |
| `size_bytes` | positive integer or null | Match file size when an MP3 is present. |
| `cache_identity` | string or null | Future digest of exact reading, provider, locale, voice and format; independent of `vocab_id`. Null before collection. |
| `metadata_ref` | relative path or null | Existing `data/audio/jp/_metadata/<reading>.json` when present. |

The current audio metadata names these values `word`, `reading`, `locale`, `voice`, `audio`, `source`, `format`, `size`, `duration_seconds`, `status`, and row-bound `key`. A future builder maps them explicitly and verifies the MP3 frames, duration, path, and provider/options. Its cache identity should be SHA-256 over a canonical UTF-8 serialization of `[reading, provider, locale, voice, format]`; a changed voice or reading invalidates the audio cache without changing the vocabulary ID.

## Stable IDs and review provenance

At first migration, allocate IDs such as `vocab-000001` through `vocab-000100` once and persist a versioned ID registry alongside the source vocabulary. The exact sample IDs below are **illustrative and not allocated**. The registry stores ID, initial source triple, current row hint, and explicit edit/reconciliation history. `source_row_index` is a locator, never identity.

On later imports, uniquely matching unchanged triples may retain their IDs across reorder. A changed display text, Japanese spelling, or meaning requires an explicit old-ID-to-new-row reconciliation in the registry; the builder must stop on ambiguous or duplicate matches rather than allocate a new ID silently. New entries receive new unused IDs. Never reuse retired IDs or regenerate all IDs from sorted order, row numbers, or a text hash.

Approved sense decisions live in a separate versioned ledger keyed by `vocab_id`, with reviewer, timestamp, rationale, `target_sense`, and optional approved `image_search_intent`. This design keeps source vocabulary, human decisions, model query cache, and generated media distinct. Pending proposals in the Phase H report are not ledger approvals.

## Query and asset selection

1. For an approved `image_search_intent`, use that exact query for both DuckDuckGo retrieval and SigLIP ranking. Record `human_approved` provenance and decision version. This selection sits after Qwen cache lookup and before search/ranking; the current Qwen prompt and cache format stay unchanged.
2. If a target sense is approved but no image intent is approved, hold image collection for that ambiguous item. Do not fall through to a potentially conflicting Qwen query.
3. Without an approved decision, keep the existing Qwen-generated query and mark `model_generated_unreviewed`. A recommendation never overrides runtime behavior.
4. Existing image cache validation uses provider and selected query; a new approved query must not reuse an image saved under an old query. A future implementation must additionally check metadata word and provenance. Preserve existing assets until an isolated replacement has been reviewed.

No query override is implemented in this task. The current cache signature is tied to ordered vocabulary, model and prompt; its 10 cached records remain untouched. A future implementation must handle cache invalidation from order changes without editing the existing cache by hand.

## Example records

These are design illustrations, **not validated production records**. IDs are placeholders. Public URLs are null while approval is pending. The normal audio directory currently has no MP3s; the three smoke MP3s are intentionally excluded.

### Unflagged but unreviewed: apple

```json
{
  "schema_version": 1,
  "vocab_id": "vocab-000001",
  "source_row_index": 1,
  "english": "apple",
  "japanese": {"display": "りんご", "reading": "りんご", "written_form": null},
  "vietnamese": "quả táo",
  "target_sense": null,
  "part_of_speech": "noun",
  "review_status": "unreviewed",
  "image": {
    "status": "needs_review",
    "path": "data/image/en/apple.jpg",
    "url": null,
    "source_english": "apple",
    "target_search_sense": null,
    "final_search_query": "apple fruit",
    "query_provenance": "model_generated_unreviewed",
    "provider": "duckduckgo",
    "ranking": {"method": "siglip2", "model": "google/siglip2-so400m-patch16-384"},
    "metadata_ref": "data/image/en/_metadata/apple.json"
  },
  "audio": {
    "status": "missing", "reading": "りんご", "path": null, "url": null,
    "provider": "google_translate_gtts", "locale": "ja",
    "voice": {"tld": "com", "slow": false}, "format": "mp3",
    "duration_seconds": null, "size_bytes": null, "cache_identity": null,
    "metadata_ref": null
  }
}
```

### Ambiguous target sense: rice

```json
{
  "schema_version": 1,
  "vocab_id": "vocab-000004",
  "source_row_index": 4,
  "english": "rice",
  "japanese": {"display": "ごはん", "reading": "ごはん", "written_form": null},
  "vietnamese": "cơm",
  "target_sense": null,
  "part_of_speech": "noun",
  "review_status": "needs_decision",
  "image": {
    "status": "needs_review",
    "path": "data/image/en/rice.jpg",
    "url": null,
    "source_english": "rice",
    "target_search_sense": null,
    "final_search_query": "rice grain",
    "query_provenance": "model_generated_unreviewed",
    "provider": "duckduckgo",
    "ranking": {"method": "siglip2", "model": "google/siglip2-so400m-patch16-384"},
    "metadata_ref": "data/image/en/_metadata/rice.json"
  },
  "audio": {
    "status": "missing", "reading": "ごはん", "path": null, "url": null,
    "provider": "google_translate_gtts", "locale": "ja",
    "voice": {"tld": "com", "slow": false}, "format": "mp3",
    "duration_seconds": null, "size_bytes": null, "cache_identity": null,
    "metadata_ref": null
  }
}
```

The owner-review recommendation is cooked rice and a future `cooked rice` image search intent. Neither is approved or written into the example record.

### Confirmed image drift: chicken

```json
{
  "schema_version": 1,
  "vocab_id": "vocab-000009",
  "source_row_index": 9,
  "english": "chicken",
  "japanese": {"display": "とりにく", "reading": "とりにく", "written_form": null},
  "vietnamese": "thịt gà",
  "target_sense": null,
  "part_of_speech": "noun",
  "review_status": "needs_decision",
  "image": {
    "status": "needs_review",
    "path": "data/image/en/chicken.jpg",
    "url": null,
    "source_english": "chicken",
    "target_search_sense": null,
    "final_search_query": "chicken animal",
    "query_provenance": "model_generated_unreviewed",
    "provider": "duckduckgo",
    "ranking": {"method": "siglip2", "model": "google/siglip2-so400m-patch16-384"},
    "metadata_ref": "data/image/en/_metadata/chicken.json"
  },
  "audio": {
    "status": "missing", "reading": "とりにく", "path": null, "url": null,
    "provider": "google_translate_gtts", "locale": "ja",
    "voice": {"tld": "com", "slow": false}, "format": "mp3",
    "duration_seconds": null, "size_bytes": null, "cache_identity": null,
    "metadata_ref": null
  }
}
```

The owner-review recommendation is chicken meat and a future `chicken meat` image search intent. The existing bird image must not be promoted as approved.

### Kana homophone: flower

```json
{
  "schema_version": 1,
  "vocab_id": "vocab-000015",
  "source_row_index": 15,
  "english": "flower",
  "japanese": {"display": "はな", "reading": "はな", "written_form": null},
  "vietnamese": "hoa",
  "target_sense": null,
  "part_of_speech": "noun",
  "review_status": "needs_decision",
  "image": {
    "status": "missing", "path": null, "url": null,
    "source_english": "flower", "target_search_sense": null,
    "final_search_query": null, "query_provenance": null,
    "provider": null, "ranking": null, "metadata_ref": null
  },
  "audio": {
    "status": "missing", "reading": "はな", "path": null, "url": null,
    "provider": "google_translate_gtts", "locale": "ja",
    "voice": {"tld": "com", "slow": false}, "format": "mp3",
    "duration_seconds": null, "size_bytes": null, "cache_identity": null,
    "metadata_ref": null
  }
}
```

Written form 花 is recommended for review, but the existing kana display and reading are preserved.

## Migration design for a later implementation

1. **Read source rows without losing indices.** Validate 100/100/100 UTF-8 rows, nonempty fields, duplicates, and any ordering drift. A structural error aborts manifest publication with file, language, and physical line number.
2. **Create and persist the ID registry once.** Review the initial 100 row-to-ID assignments. On reruns, match unchanged triples uniquely; require explicit reconciliation for changed text, reordered ambiguous duplicates, split/merged senses, or retired records. Never create a new ID for a known item solely because its row moved.
3. **Apply explicit decisions.** Join approved review-ledger entries by `vocab_id`; set `needs_decision` for flagged entries without approval and `unreviewed` for the rest. An absent ledger row cannot become `approved`.
4. **Link existing media carefully.** For images, infer current filename from EN only at the migration boundary, verify JPEG decode and metadata word/query/provider, and retain `image_selection` provenance. For audio, use the current Japanese reading to locate MP3 and metadata, validate frames, duration, size, provider, locale and voice. Row-bound audio `key` is provenance, not the primary key. Ignore `baseline/` smoke assets and never treat WAV as MP3.
5. **Represent gaps and incremental collection.** Missing query, image, and audio remain explicit `missing`. A technically valid but unreviewed/drifted file remains `needs_review`. A later offline collection may add media without changing IDs or silently overwriting an approved manifest. The builder itself does not call Qwen, DDG, SigLIP, or gTTS.
6. **Publish through a stable boundary.** Internal records keep relative paths and provenance. Future static serving maps approved assets to root-relative `/assets/images/en/...` and `/assets/audio/ja/...` URLs; clients receive null for missing/unapproved media and use a fallback. No absolute local path or smoke path leaks into a public record.
7. **Validate and version.** Fail clearly on duplicate/missing IDs, invalid UTF-8, count/order mismatch, unsafe paths, metadata disagreement, malformed media, unresolved join, or unknown schema/status value. Produce a report distinguishing structural errors, semantic review, and media gaps. Write a new manifest atomically only after validation; preserve the last good output on failure. Add optional fields compatibly; use a new schema version for breaking changes.

The next implementation phase should test a small three-item fixture including a valid image, a drifted image, and missing audio before building all 100 records. Product schema freeze waits for owner decisions and end-to-end consumer verification.
