# B-002 Excel vocabulary importer

Run from the repository root in PowerShell. Python's standard library is sufficient; no Excel package or AI service is required.

```powershell
# Validate and preview; writes no file. Exit 0 means valid, exit 1 means validation errors.
.\.venv\Scripts\python.exe -B "collect data script\excel_vocabulary_importer.py" "C:\path\to\words.xlsx"

# After reviewing the preview, create a private import record. Existing output is never overwritten.
.\.venv\Scripts\python.exe -B "collect data script\excel_vocabulary_importer.py" "C:\path\to\words.xlsx" --output "C:\path\to\private_import.json"

# Resume/check an accepted import; use the import_id printed by the previous command.
.\.venv\Scripts\python.exe -B "collect data script\excel_vocabulary_importer.py" "C:\path\to\words.xlsx" --resume "C:\path\to\private_import.json" --import-id "imp-<UUIDv4>"
```

Input is an unencrypted, non-macro `.xlsx` with exactly one visible sheet named `Vocabulary`. Row 1 has lowercase text headers `english`, `japanese`, `vietnamese`, and optionally `target_sense` in any order. Data starts at Excel row 2. Required values are text. Blank optional sense becomes null. The importer trims Unicode 15.1 White_Space at the edges, applies NFC, preserves internal spaces and display case, skips fully blank rows with warnings, and rejects duplicate normalized records. There is no 100-row limit.

Preview JSON includes `valid`, normalized `rows` with physical `source_row`, sorted `diagnostics`, and a deterministic `normalized_payload_sha256` for valid input. Each diagnostic has `code`, `severity`, `sheet`, `row`, `column`, `message`, and `related_row`. Any error prevents acceptance. Warnings allow acceptance after the learner reviews the preview. An invalid file never erases an existing import. The accepted private JSON adds fresh `imp-`, `pack-` and per-row `item-` UUIDv4 IDs, source workbook SHA-256 and warning records. It stays separate from the benchmark dataset and experimental media; it is not a runtime content pack. A fresh import mints fresh IDs even for identical input. Resume checks the accepted import ID and normalized payload hash, then returns the stored mapping unchanged.

Example using the existing synthetic fixture:

```powershell
.\.venv\Scripts\python.exe -B "collect data script\excel_vocabulary_importer.py" "tests\fixtures\b001\excel_valid.xlsx" --output "reports\b002_import_demo\fixture_private_import.json"
```

The recorded example output is [fixture_private_import.json](../reports/b002_import_demo/fixture_private_import.json): 3 rows, source rows 2–4, `rain` target sense `rain weather`, payload SHA-256 `d7efbaf23abac2e23c637c8e8f24089763dc12a45d0547f9884154a77a20eaaf`. This is synthetic test input, not approved learning content.

Test commands:

```powershell
.\.venv\Scripts\python.exe -B -m unittest "collect data script/test_excel_vocabulary_importer.py" -v
.\.venv\Scripts\python.exe -B tests/fixtures/b001/verify_fixtures.py
.\.venv\Scripts\python.exe -B -m unittest discover -s "collect data script" -p "test_*.py" -q
.\.venv\Scripts\python.exe -B -m unittest discover -s kaggle_batch/tests -p "test_*.py" -q
```

Limitations: B-002 here only accepts and records vocabulary. It does not generate media, run quality review, create a playable content pack, or implement UI. The Python runtime's Unicode database is 16.0; the explicit White_Space set follows Unicode 15.1, while NFC/casefold use the runtime database. For newly assigned Unicode characters, that could differ from Unicode 15.1. The importer parses ZIP/XML into memory and has no deployment resource budget; a hosted upload service should set byte/decompression/time limits before accepting untrusted files.
