# A-004R verification — 2026-11-23

Branch `main`, HEAD `936d9fdd27810e50a144fb6399e647b1ba18c371`. Existing uncommitted files were preserved. No commit/push. [Integration audit](../../../reports/image_pipeline_experiments/A004R_CONDITIONAL_100/integration_status_report.md) was written before the runner or live work and identified the A-004 default-query call path. A-002/A-003 ICON arms had not been integrated; FIX-001 and SigLIP were already implemented.

## Frozen routing and live run

- `routing_matrix.csv` SHA-256 `c99c15e4b0dd567889e44335bb342018096431c5f5815ef113417bd8ca2fa85c`, 100 unique IDs. Strategy: 62 NORMAL, 10 ICON, 28 SPECIAL_REVIEW. Execution source: nine NEW_RETRIEVAL (six ICON, three NORMAL), 57 A004_REUSE, six OWNER_REFERENCE, 26 BLOCKED_QUERY, one NO_SUITABLE_IMAGE, one INTERNAL_OVERRIDE.
- Offline guards validated canonical dataset/frozen vocabulary, A-004 manifest/query/retrieval/evaluation hashes, six A-003.3 owner image hashes, because override hash and FIX-001 function bindings. `run_a004r.py verify` validates frozen source versions. No Qwen run, model download or production write.
- First batch of ten IDs: apple/car NORMAL new queries; sleep/write/swim ICON new queries; hungry/eat owner references; sometimes NO_SUITABLE_IMAGE; because INTERNAL_ONLY_TEMPORARY; today BLOCKED_QUERY. All five new searches ranked. The executed ICON queries had literal `<english> icon`; NORMAL queries lacked that suffix. New candidate raw/JPEG hashes matched.
- Remaining nine batches completed from the frozen matrix. Final 100 statuses: nine RANKED_NEW, 57 REUSED_A004, six OWNER_REFERENCE, 26 BLOCKED_QUERY, one NO_SUITABLE_IMAGE, one INTERNAL_OVERRIDE. Nine actual new search calls, nine SigLIP passes, 61 candidate records, 56 valid raw/JPEG pairs, five failed downloads. `candidate_rankings.csv` has 449 rows, including clearly tagged reused A-004 candidates. No cached result was claimed as a fresh retrieval.
- Initial system-Python attempt stopped at duplicate OpenMP initialization before any search/scoring. The single `ATTEMPTED` placeholder was verified `search_attempted=false`, `score_attempted=false` and reset. Live batches then ran with repository `.venv` as A-004 had done. No retry of a search or ranking was needed.

## Quality and browser evidence

- A-004R nine fresh top images were inspected together in `new_top_contact_sheet.jpg`: educational suitability AI_PRELIMINARY five PASS, two NEEDS_REVIEW, two FAIL. Water bottle advertising/text and understand answer text/watermark led to preliminary rejection. Apple/rain have small source marks requiring review. Owner approval of every new candidate remains NOT_REVIEWED and public eligibility UNKNOWN_RIGHTS_NOT_CLEARED.
- The A-004→A-004R ICON comparison is limited to six new searches: sleep/write/remember FAIL→PASS; rain NEEDS_REVIEW→NEEDS_REVIEW; understand FAIL→FAIL; swim had no A-004 image. NORMAL apple PASS→NEEDS_REVIEW, car PASS→PASS, water no A-004 image→FAIL. No dataset-wide improvement claim; 57 A-004 reused labels are marked as reuse, not new assessments.
- Local browser loaded `review_gallery.html`: 100 cards shown, `RANKED_NEW` filter displayed exactly nine, first image decoded, zero console errors/warnings. The page exposes owner feedback and JSON export, but no test export was treated as a human decision. Owner references and internal-only restrictions appeared separately.

## Regression and protected inputs

- `.venv/Scripts/python.exe -B -m unittest discover -s reports/image_pipeline_experiments/A004R_CONDITIONAL_100 -p test_*.py -q`: **5 OK** (routing, owners, restrictions, FIX-001, ID rejection, isolation).
- `.venv/Scripts/python.exe -B -m unittest discover -s "collect data script" -p "test_*.py" -q`: **174 OK**.
- `.venv/Scripts/python.exe -B -m unittest discover -s kaggle_batch/tests -p "test_*.py" -q`: **19 OK**.
- `.venv/Scripts/python.exe -B "collect data script/validate_vocabulary.py"`: **100 physical rows, zero structural issues**. `git diff --quiet -- data/vocabulary/unified_dataset_v1.json`: exit 0. `git diff --check`: exit 0 with pre-existing line-ending warnings.
- Protected SHA-256 unchanged: canonical dataset `644c2dc9899077dad15d2e2916d7dc3d1cef49ecd151ea406115bb3da19481bd`; A-003.3 owner manifest `fa478187a3ddf454e5ae5f3d25a87e839585e32d16a6c26c9a3104664e3d651f`; because override `00770e7c7c2fee26b2d4eda515ab51c3a82f927938043c150eff2feba5319799`; A-004 retrieval `028b186818b34f6133380a267c63a554be217b5f565475746b9835f7eb7966c8`.

## Final artifact hashes

| A-004R file | SHA-256 |
|---|---|
| `experiment_manifest.json` | `6092b0c37bd879a55ed8b694b81458291363d6ea8fa397d10e1b95251545f982` |
| `retrieval_results.json` | `bd9e345cac27fc10e3389c6f40b447ed790b00c953a06e13503efd6f417fa621` |
| `candidate_rankings.csv` | `46075c65eca715fce29b8310818391a6b55e0909f3054921e5a1fcfec1a1383b` |
| `evaluation_matrix.csv` | `2b2491f0e1d74b3958191539bb69fc639675bca77478c550e547cf34dba13974` |
| `review_gallery.html` | `439b6d62c0e4d64b8326dd497f2edf3ef6a4ad38b6731da820c69b372fab5085` |
| `evaluation_report.md` | `02335b49e9608b1902816d974f74f3d0edbd71a0f2ce3f44a4f563f30a226d31` |

Next action: owner reviews the internal gallery and exports JSON; a separately scoped task can validate and consolidate it. Twenty-six blocked queries need semantic repair/contextual decisions before retrieval. Five other A-003 holdouts remain unreviewed. No B-003.2, production routing or Game UX/UI started.
