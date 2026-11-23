# Content Pack Contract v1

Status: **PROPOSED implementation contract**, B-001, 2026-11-22. UTF-8 JSON plus relative media files, independent of framework/transport. This is a new interchange format, not a replacement for `unified_dataset_v1.json`. [Excel input](excel_v1.md) defines IDs; [adapters](integration_notes.md) explain compatibility. Fixtures are synthetic only.

## Envelope and record shape

All listed keys are required unless explicitly optional. Nullable fields must be present with null. Integers are positive safe JSON integers (`<= 9007199254740991`). Reject unknown core fields in v1 to catch typos; optional `extensions` object may carry namespaced, non-executable metadata and is ignored by v1 consumers. Reject unsupported contract_version and duplicate JSON keys. No implicit locale coercion.

| Object | Fields and types |
|---|---|
| Pack | `contract_version: 1`, `pack_id: pack-UUIDv4`, `pack_version: integer`, `import_id: imp-UUIDv4`, `test_only: boolean`, `items: Item[]`; optional `extensions` |
| Item | `item_id: item-UUIDv4`, `source_row: integer >=2`, `english: string`, `japanese: string`, `vietnamese: string`, `target_sense: string|null`, `status: Status`, `review_status: pending|approved|rejected`, `quality: Quality`, `technical_integrity: unknown|pass|fail`, `distribution: Distribution`, `image: Asset|null`, `audio: Asset|null`, `errors: Error[]`; optional `extensions` |
| Quality | `semantic_correctness`, `image_relevance`, `image_visual_quality`, `audio_pronunciation`: each `unknown|pass|fail`; `evidence: Evidence[]` |
| Evidence | `dimension`: one of four quality keys or `technical_integrity` or `content_review`; `reviewer: string`, `basis: string`, `asset_sha256: string|null` |
| Distribution | `status: unknown|permitted|restricted`, `evidence: string|null` (sanitized source/license/permission reference) |
| Asset | `path: string`, `mime_type: string`, `sha256: 64 lowercase hex`, `size_bytes: positive integer`, `source: Source|null` |
| Source | `provider: string|null`, `url: string|null` (public HTTPS only), `query: string|null`, `model: string|null`, `revision: string|null`; no credentials or machine paths |
| Error | `stage: import|query|image|audio|validation|review`, `code: nonempty string`, `message: nonempty safe text`, `retryable: boolean` |

Text fields use normalized Excel values, and blank target_sense is null. IDs unique within the pack, source_row provenance never drives identity. Accepted imports have no duplicate identity keys. Item order is presentation order. No upper item count of 100. An empty pack is invalid. `pack_version` starts at 1, increments on every persisted change (including status/review changes); `(pack_id,pack_version)` is immutable. Older snapshots/asset hashes remain addressable until a deliberate retention decision. There is no independent item version: compare the enclosing snapshot version and asset hashes.

Image supports `image/png` or `image/jpeg`; audio supports `audio/mpeg` or `audio/wav`. File bytes must match declared type, size and SHA-256 before technical pass; decode/valid audio and correct item association are also required. Actual provider results may be found/downloaded rather than generated; `source` records this without implying provenance or approval. Quality evidence must cover each dimension marked pass/fail; image/audio observations bind to the corresponding hash. Semantic evidence uses null hash. `review_status=approved` requires `content_review` evidence; approved status alone cannot substitute for per-dimension results. Evidence describes who assessed what; external systems still must enforce reviewer trust.

## Processing state and review transitions

`status` summarizes item processing/readiness; it is distinct from technical, quality, reviewer and distribution fields. Every transition is persisted into a new pack_version. Starting state: pending, review pending, all quality unknown, technical unknown, image/audio null, errors empty, distribution unknown.

| Transition | Exact prerequisite / effect |
|---|---|
| `pending → processing` | Valid accepted row; worker claims this item and records attempt privately. No gameplay inference. |
| `processing → needs_review` | Both assets exist, technical pass, no active processing errors; content needs review or contains a review concern. Valid files alone lead here. |
| `processing → failed` | Any stage cannot complete required output; errors contains at least one actionable error. Technical or quality results reflect actual evidence, not invented success. |
| `needs_review → ready` | Both assets, technical pass, all four quality dimensions pass with matching evidence, review approved, errors empty. Distribution may remain unknown/restricted for local use. |
| `needs_review → failed` | Reviewer rejects; review rejected and a review-stage error explains why. A quality fail can remain needs_review while a correction/replacement is pending. |
| `failed → pending` | Explicit retry/correction action; errors moved to private attempt history and cleared in new snapshot. Invalidate affected checks/review; retain unrelated evidence only if text/asset hashes unchanged. |
| `needs_review or ready → pending` | Explicit text/asset-affecting edit or regeneration request; clear item review approval, invalidate affected quality/technical/distribution evidence, schedule new processing. Same item_id retained. |
| `ready → needs_review` | Approval withdrawn or quality concern discovered, with new evidence; review pending, ready invariant no longer holds. |
| `ready or needs_review → failed` | Preparation validator confirms missing/corrupt/mismatched media: technical fail, review pending, validation-stage error; retain prior snapshot as history and invalidate affected asset-quality checks. Runtime itself only reports the local diagnostic. |

Other direct jumps are invalid. No pending→ready or processing→ready shortcut. On resume after worker crash keep processing until reconciled from saved attempt/output checks; do not mint new import/item IDs. `failed` always has errors; other states have errors empty (review concerns are quality evidence until a rejection makes them errors). Retrying is explicit, not triggered by opening the pack in gameplay.

Offline validation rechecks technical facts. A missing/corrupt media file disables that item; runtime reports a local diagnostic and asks for repair/download outside gameplay. It must not call AI, silently mark ready, or mutate an immutable signed-off snapshot. A later preparation operation may persist a new failed snapshot with a validation-stage error, then retry via pending. A rights-only change creates a new pack_version/distribution decision but does not change AI quality or item ready status.

## Local readiness versus public release

`ready` means content reviewed and technically playable locally. `public_eligible(item)` is **derived**, never an independent stored boolean: item ready AND distribution permitted with nonempty evidence AND pack.test_only=false. Distribution is aggregate across both assets; only permitted when both uses are supported. If either asset has known restrictions, aggregate restricted; otherwise unknown until sufficient evidence. Restricted/unknown never become permitted just because the project is academic/non-commercial. Full benchmark rights audit is not required for quality review or MVP local development.

Preparation snapshots may include all five states. A runtime reads ready items only and shows unavailable states without generation. A public release is a **new immutable snapshot of the selected eligible subset**, same pack_id, new version; exclude other items, their assets, private errors and raw workbooks. Reject release if the selected subset is empty or contains ineligible items. Do not require every original import item eligible to publish a subset. Explain partial availability in the UI rather than suggesting all Excel rows completed.

## Offline storage and safe references

`path` is pack-relative `assets/<sha256>.png|jpg|mp3|wav`, extension matching MIME. No absolute/drive/UNC/file/http paths, `..`, backslash, query, fragment, percent encoding or symlink escape. Multiple item references may share identical asset bytes only when independently associated/reviewed. Bind resolution to pack root, not server root: works below a GitHub Pages project prefix or in local/offline storage. `source.url` is provenance only, never a gameplay media dependency; redact signed/credential URLs, userinfo, query and fragment. Null is preferable to leaking a private endpoint.

Cache the pack JSON and referenced bytes together; verify checksum/type/size before activating. Progress saves reference `(pack_id,item_id)` and loaded pack_version; keep the previous complete snapshot until the new one verifies. If offline storage fails/quota is exceeded, retain previous pack and report error; do not promise guaranteed storage duration. Model IDs/revisions and source metadata are descriptive, never executable input. Browser rendering treats imported text as text, not HTML. Secrets, private stack traces, local paths and raw import files are excluded from runtime/public serialization, including free-text evidence/provider/query/error fields. Exporters must use sanitized, allowlisted diagnostics rather than copying arbitrary worker log strings. No detection regex can guarantee absence of every possible secret.

## Examples and verification

`tests/fixtures/b001/content_pack_states.json` contains all five statuses, including ready with distribution unknown and failed/needs_review. Its pack is `test_only=true`; pass/approval values are simulated contract states with `fixture-simulator` evidence. The tiny PNG and tone WAV have real checksums but do not represent AI or language-quality approvals. The fixture verifier checks schema keys, states/ready prerequisites, safe references, bytes/hash, import expectations, namespace isolation and a generated in-memory 101-item shape. It does not implement ingestion/generation/runtime or certify real content.
