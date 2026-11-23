# B-001 contract fixtures

All files here are **synthetic test data**. No workbook row or content-pack pass/review field is an AI result, owner semantic approval or distribution permission. `content_pack_states.json` has `test_only=true`; never publish it as learner content. The image is a 16×16 blue square and audio is a 440 Hz tone, not pronunciation. They exist only to exercise offline file references/checksums. They do not prove educational relevance.

| Workbook | Expected outcome |
|---|---|
| `excel_valid.xlsx` | Three accepted rows 2–4, four supported headers; rain has optional target_sense |
| `excel_missing_column.xlsx` | Missing vietnamese header, INVALID_HEADER at row 1; no import |
| `excel_blank_row.xlsx` | Skip physical row 3 with warning; retain rows 2 and 4 |
| `excel_duplicate.xlsx` | Normalized/casefold duplicate row 3 relates to row 2; atomic rejection |
| `excel_unicode.xlsx` | Decomposed dakuten and Vietnamese accents normalize to がっこう and trường học |

`expected.json` records these expectations. The three-row valid workbook traces to the first three content fixture items; two extra synthetic records illustrate pending and processing. Ready/failed/needs_review are also represented. Ready has distribution unknown intentionally, demonstrating local readiness is independent of public eligibility. IDs use import/pack/item UUID namespaces, never benchmark IDs.

From repository root:

```powershell
.\.venv\Scripts\python.exe -B tests/fixtures/b001/verify_fixtures.py
```

This standard-library checker reads only the known fixture ZIP/XML, JSON and two tiny media files. It checks normative invariants used by these examples and negative mutations. It is **not a production importer/schema validator**, does not run AI/network or mutate production, and does not certify real content quality. The Unicode examples cover defined vectors only; production parsers must implement the full Unicode policy. It also constructs a 101-item example in memory; no 101-row fixture duplication needed.
