# B-001 integration assessment

**2026-11-22: contract/fixtures only.** Existing application source, dataset, registry, semantic decisions and staging are not modified. Specifications [Excel v1](excel_v1.md) and [pack v1](content_pack_v1.md) are proposed for future implementation. B-001 completion means the contract/examples were verified, not an importer, service or game exists.

## Reuse and required adapters

| Existing boundary / evidence | Reusable behavior | Adapter required before arbitrary imports |
|---|---|---|
| `collect data script/vocabulary_registry.py:8-101`: `vocab-######`, exact triples, row hints/history | Stable identity and reconciliation principles | Separate import manifest/item UUID namespace. Do not insert user rows into canonical benchmark registry or identify imports by Excel row. Benchmark references, if needed, stay private mappings; no automatic text-only join. |
| `validate_vocabulary.py`: canonical EN/JP/VN TXT and expected row count | Structural checks, explicit errors | XLSX boundary validates workbook/types/Unicode/duplicates before acceptance; generic accepted rows cannot be passed through fixed-count canonical validator. No 100-item product limit. |
| `semantic_decisions.py:8-88`: hardcoded three approvals, twenty context IDs, canonical row hints | Distinction between context and owner-approved sense; no guessing approval | Per-import semantic context/reviewer evidence. Learner target_sense is input intent, not canonical approval; do not edit hardcoded benchmark ledger. |
| `stage_vocabulary_images.py:1-110` and `stage_japanese_audio.py:34-105`: canonical registry and bounded 1–10 ID batches, run manifests | Retrieval/scoring, MP3 validation, staging/resume, checksum/provenance | Generic item/job adapter, pack-local paths and isolated staging roots; translate per-item outcomes/errors to status. Existing CLI batch-size limit is scheduling, not pack length. Existing runners are not already compatible with item UUIDs. |
| `dataset_builder.py:42-153`: fixed production directories, approved ledger, all found media `needs_review`, URL null | Byte/metadata validation, read-only `build_dataset(root)` for canonical data | New pack exporter from accepted imports/staging; reuse checks after decoupling fixed root assumptions. Existing `schema_version:1` is a different format from `contract_version:1`; never overwrite canonical JSON to adopt the new schema. |
| `audiocollector.py:166-179` gTTS; audio filenames/metadata tied to reading/row | Synthesis, cache and technical validation logic | Audio per-item mapping and reading review. Proposed japanese text-as-reading does not solve kanji pronunciation. Keep provenance and validate exact output before packaging. |
| `web/`, `game/` placeholders | Intended flashcard/game flow only | Runtime pack loader/validator, cache/IndexedDB, progress store and text-safe UI; resolve assets locally and never invoke model during gameplay. |

Paths with bare filenames above are under `collect data script/`. Preserve legacy filename/key conventions in historical records; map them to item_id + content-addressed media in a future export instead of renaming existing files. Conversion must not promote unknown quality, licensing or listening decisions.

## Row-to-pack trace (fixture, not generated output)

`excel_valid.xlsx`, Vocabulary row 2 → accepted apple/りんご/quả táo/null → private import mapping allocates fixture's `imp-11111111-1111-4111-8111-111111111111`, `pack-22222222-2222-4222-8222-222222222222`, and `item-33333333-3333-4333-8333-333333333333`. Content fixture demonstrates this item after simulated technical/content approval. It remains **ineligible for public release** because test_only=true and distribution unknown. Rows 3 and 4 map to failed and needs_review examples. Rows 5–6 in that pack are additional synthetic pending/processing examples, not rows from the valid 3-row workbook.

Duplicate fixture deliberately repeats the same normalized four-field key and must reject import; blank-row fixture skips physical row 3 and retains row 4 provenance. Unicode fixture uses decomposed dakuten/Vietnamese accents; NFC values are expected without rewriting canonical source files. Same import retry uses stored IDs and payload fingerprint; a new upload is not inferred to be the old pack.

## Verification and B-002 prerequisites

Run `.\.venv\Scripts\python.exe -B tests/fixtures/b001/verify_fixtures.py` from the repository root after fixtures are available. It is a bounded fixture consistency checker, not a production XLSX importer or full JSON Schema engine. Uses stdlib ZIP/XML to inspect only authored workbook cells and the expected matrix. It verifies fixture data, normalized duplicate/error cases, pack required fields/state constraints, asset checksum/MIME/header/safe path and namespace separation. Negative mutations must reject ready-without-review, missing media, unsafe paths, duplicate item IDs, malformed enum/ID and failed-without-error. A 101-item in-memory example verifies no fixed 100 guard. No inference/network/providers involved.

Before B-002: user implementation instruction; choose XLSX parser and runtime stack; implement the above adapters/validation; select a small technically valid, content-reviewed local set or explicitly labeled synthetic prototype set; implement offline persistence and failure handling. Actual online media generation also needs host/job budget and provider decisions. These choices remain UNKNOWN/PROPOSED, not hidden prerequisites for finishing documentation. Public deployment separately needs content/technical/rights checks only for the released subset. A-001 semantic review may proceed independently.
