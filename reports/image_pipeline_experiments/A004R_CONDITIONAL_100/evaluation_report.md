# A-004R conditional-query experiment

100/100 IDs have explicit outcomes. This is an internal benchmark, not production selection or rights clearance.

## Execution

- Routing: {'NORMAL': 62, 'ICON': 10, 'SPECIAL_REVIEW': 28}.
- Outcome: {'RANKED_NEW': 9, 'OWNER_REFERENCE': 6, 'NO_SUITABLE_IMAGE': 1, 'INTERNAL_OVERRIDE': 1, 'BLOCKED_QUERY': 26, 'REUSED_A004': 57}.
- New searches: 9 (six ICON, three NORMAL), all ranked. A-004 reused rankings: 57; owner references: six; explicit no-image: one; internal-only override: one; query blockers: 26.
- Owner references and A-004 cache are never counted as fresh retrieval or fresh ranking. Every new search used at most seven candidates, one SigLIP pass, no retry.
- A default Python attempt stopped on duplicate OpenMP runtime before search/scoring; it was reset after verifying no search attempt. Live work used the repository .venv, as A-004 did.

## Preliminary quality

- Nine fresh top images: 5 PASS for educational suitability, two NEEDS_REVIEW, two FAIL. These are visual desk judgments, not owner approval.
- Water has bottle advertising/answer text; understand has prominent answer text and watermark. Their SigLIP top-1 results are rejected at the preliminary gate. Apple and rain need source-mark review.
- Across 100 rows, suitability labels are {'NEEDS_REVIEW': 12, 'PASS': 33, 'NOT_ASSESSED': 34, 'FAIL': 21}; 57 reused A-004 labels remain tagged REUSED_A004_AI_PRELIMINARY. The 34 owner/special/blocked rows have no new candidate assessment.
- A-001 baseline, A-004 default-query image and A-004R new image are separate columns in the evaluation matrix and gallery. A-004R is newly paired for only nine IDs; six ICON queries are too few to claim a dataset-wide quality gain.
- For the six new ICON searches, A-004→A-004R preliminary educational labels: sleep FAIL→PASS, write FAIL→PASS, remember FAIL→PASS, rain NEEDS_REVIEW→NEEDS_REVIEW, understand FAIL→FAIL; swim had no A-004 image and is now PASS. This is a small, partly unpaired comparison.
- For the three new NORMAL searches: apple PASS→NEEDS_REVIEW (source mark), car PASS→PASS, water had no A-004 image and is now FAIL (advertising/text). A-001 images remain available for direct owner comparison in the gallery.
- Six earlier owner-quality selections are preserved by exact path/hash and excluded from the nine fresh results. `sometimes` remains NO_SUITABLE_IMAGE; `because` remains INTERNAL_ONLY_TEMPORARY. Public rights remain unverified for all images.

## Review and limits

- Owner feedback and JSON export are available in `review_gallery.html`; generated candidates are NOT_REVIEWED and NOT_PROMOTED.
- The 26 BLOCKED_QUERY items require explicit semantic query repair or contextual decisions before retrieval. Five other A-003 holdouts remain unreviewed separately.
- No Qwen or SigLIP weights changed; no canonical vocabulary, production media, previous experiment or owner decision was overwritten.
