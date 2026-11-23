# Excel Import Contract v1

Status: **PROPOSED implementation contract**, completed under B-001, 2026-11-22. Framework independent. No importer is implemented by this document. See [content pack](content_pack_v1.md), [integration notes](integration_notes.md), and [fixtures](../../tests/fixtures/b001/README.md).

## Workbook and fields

Accept an unencrypted, non-macro `.xlsx` OOXML workbook with exactly one visible worksheet named `Vocabulary` (case sensitive). Row 1 is the header, data starts at physical Excel row 2. Column order may vary; headers must be literal text, trimmed, exact lowercase names below. Reject repeated/unknown/nontext headers. Ignore completely empty columns and formatting outside the table; reject populated columns without a header. No merged cells in the table, formulas (even with cached values), Excel error cells, external workbook relationships, embedded objects or macro content. Never execute formulas/links. File extension alone does not establish a valid workbook.

| Header | Type / presence | Meaning |
|---|---|---|
| `english` | Required nonempty text | English display/learning term |
| `japanese` | Required nonempty text | Japanese display and spoken reading for v1; kana recommended; kanji input requires pronunciation review, no automatic reading conversion promised |
| `vietnamese` | Required nonempty text | Vietnamese meaning |
| `target_sense` | Optional text or blank | Learner-supplied intended sense/context, not an approved semantic decision |

Do not coerce numbers, booleans or dates into vocabulary strings. Empty optional values become JSON null. Do not silently translate, change case for display, change kana script, remove diacritics or fill missing cells. Reject strings containing line breaks, NUL/control characters or unpaired surrogates (tab is not allowed inside a value). Stored display values use Unicode NFC after trimming Unicode White_Space at both ends (Unicode 15.1 property, not runtime-specific `trim` behavior); preserve internal spaces. NBSP at the edges is trimmed; U+200B is not whitespace and remains literal. No NFKC: full-width/half-width and katakana/hiragana distinctions remain. Log normalization warnings with physical row/column; retain raw values only in private import diagnostics, never blindly render as HTML.

## Rows, duplicates and validation result

Fully empty rows, including whitespace-only cells, are skipped with `EMPTY_ROW` warnings; retain original Excel row indices for following items. A partially empty row is an error for each missing required field. A workbook with no data rows after skips returns `NO_DATA`.

Duplicate identity key is the tuple `[NFC(english).casefold(), NFC(japanese), NFC(vietnamese).casefold(), NFC(target_sense).casefold() or null]` after trim. Casefold follows Unicode 15.1 default case folding. Compare tuple components, not concatenation without delimiters. First occurrence retains provenance; each later identical key produces a `DUPLICATE_ROW` error with `related_row` pointing to the first occurrence. Do not silently collapse rows. Different explicit target senses may distinguish two otherwise identical triples. Japanese spelling variants are not auto-deduplicated.

Validation is atomic at import acceptance: collect all structural/row errors available within resource limits, display them and preview normalized valid rows; **any error creates no accepted import, pack or generation job**. Warnings alone permit explicit learner confirmation. Fix and resubmit the file. An invalid workbook does not erase or replace an existing pack. No AI/network request is necessary to validate Excel. On corrupt/encrypted/unsupported structure, stop with a workbook error instead of guessing row content. Service deployments may enforce documented byte/row/decompression/time limits and report `RESOURCE_LIMIT`; v1 has no semantic 100-item limit.

Error/warning shape (array sorted by row then column, workbook errors first):

```json
{"code":"REQUIRED_VALUE","severity":"error","sheet":"Vocabulary","row":4,"column":"japanese","message":"Japanese text is required.","related_row":null}
```

Fields are always present; row is a positive physical row number or null for workbook/header-level errors, column is a header name or null. `sheet` is `Vocabulary` or null if the sheet is missing. Messages contain no stack trace, absolute file path or secret. Stable codes: `INVALID_WORKBOOK`, `INVALID_SHEET`, `INVALID_HEADER`, `UNSUPPORTED_CELL`, `REQUIRED_VALUE`, `INVALID_TEXT`, `DUPLICATE_ROW`, `NO_DATA`, `RESOURCE_LIMIT`; warning codes `NORMALIZED_TEXT`, `EMPTY_ROW`. Header errors use row 1; formula/type errors use their actual row/header. Original cell content is not embedded into an executable error message.

## Import, pack and stable item identity

After a validated preview is confirmed, mint `import_id = imp-<UUIDv4>` and `pack_id = pack-<UUIDv4>` using lowercase canonical UUIDs. Persist them with the accepted row→item mapping **before** dispatching generation. A new deliberate import gets new IDs even for identical bytes; a retry/resume must supply the accepted import_id and the same normalized payload hash, otherwise reject with conflict. File name, row number and timestamp are not identity.

Mint each `item_id = item-<UUIDv4>` once and persist it in that mapping. Reordering an existing pack or retrying a worker keeps item IDs; an edit through a future explicit pack editor keeps item ID but creates a new immutable pack_version and invalidates affected checks/reviews. Uploading a changed workbook is a new import in v1; automatic cross-import reconciliation is out of scope. UUID collisions must be rejected/reallocated before persisting, never overwrite an item. No item uses `vocab-000001…` benchmark IDs.

Private import record: import_id, pack_id, workbook SHA-256, contract version 1, accepted normalized rows including physical source_row and item_id, warnings, normalized payload SHA-256. Hash normalized payload as UTF-8 of the compact JSON **array of arrays** `[english,japanese,vietnamese,target_sense]` in accepted row order, `ensure_ascii=false` and no extra spaces. Row order changes this hash; do not treat a changed payload as a retry. Import records carry source rows/bytes privately; runtime packs carry only sanitized provenance. Worker attempt/session IDs belong to private logs; repeated attempts are not new imports.

## Examples and acceptance scenarios

Valid fixture has apple / りんご / quả táo, cat / ねこ / mèo, rain / あめ / mưa. They are authored test input, not benchmark imports or translation approvals. See five `.xlsx` fixtures for valid data, missing header, blank row, duplicates and decomposed Japanese/Vietnamese Unicode. Expected row/column errors and normalized text are in `expected.json`. A >100-row pack must remain representable; resource budgets are a deployment policy, not this schema's vocabulary cap.
