# A-004 complete attempt report — 2026-11-23

**All 100 vocabulary IDs have final processing states; 93/100 had real image-search attempts.** The seven query-blocked IDs were not searched. This completes the eligible image benchmark attempts, not human image approval or a claim that every ID succeeded.

## Frozen run and actual outcomes

- Dataset SHA-256 `644c2dc9899077dad15d2e2916d7dc3d1cef49ecd151ea406115bb3da19481bd`; 100 unique IDs; original Qwen output retained, with 93 effective queries, 6 invalid outputs and 1 missing approved image intent. No Qwen rerun.
- Image searches: 93/100 attempted, 93 search calls succeeded. 92 IDs ranked once by the frozen SigLIP model; 1 had no valid download; 0 other processing failures; 7 blocked before search. The only first-batch unranked item, vocab-000008, had one HTTP 404 candidate URL; the old failure was preserved and not retried.
- Candidates: 620 records, 548 valid downloads with matching raw/JPEG hashes, 72 failed downloads. No old success was redownloaded and no prior SigLIP ranking was repeated. Ten 10-ID image batches are recorded in the manifest.
- Existing A-001 audio references: 100/100 hash-match, no regeneration. Canonical vocabulary, production media and owner-approved image manifests were not changed.

## AI_PRELIMINARY evaluation

- New top-1 image semantic relevance: {'PASS': 48, 'NEEDS_REVIEW': 23, 'NOT_ASSESSED': 8, 'FAIL': 21}. Educational suitability: {'PASS': 30, 'NEEDS_REVIEW': 13, 'FAIL': 49, 'NOT_ASSESSED': 8}. Compared with A-001 images: {'UNCHANGED': 74, 'DEGRADED': 8, 'IMPROVED': 10, 'NOT_COMPARABLE': 8}. `NOT_ASSESSED` and `NOT_COMPARABLE` are excluded from any quality-rate denominator. All image judgments remain unverified by the owner.
- The query validator accepted 94 normalized outputs; 93 have an effective image intent. Desk review of all frozen effective query strings against English/Vietnamese vocabulary gives AI_PRELIMINARY query correctness {'PASS': 48, 'FAIL': 22, 'NEEDS_REVIEW': 23, 'BLOCKED': 7}. Obvious mismatches include `rain illumination`, `today timepiece`, `yesterday place`, `family institution`, `write action` and `hello object`. Seven blocked IDs and exact reasons are in [query remediation](query_remediation.json). Query syntax is not proof of semantic correctness.
- Candidate ranks are SigLIP scores, not human judgments. Review text, composition, watermarks, retrieval gaps and lower-ranked alternatives in the [internal gallery](review_gallery.html). `NO_SUITABLE_IMAGE` is an explicit owner-review choice; no new outcome is auto-approved.

## Evidence and next review

[Manifest](experiment_manifest.json), [query ledger](query_results.json), [retrieval ledger](retrieval_results.json), [candidate table](candidate_rankings.csv), [100-ID matrix](evaluation_matrix.csv) and the gallery retain status, source URLs, hashes, ranks and failures. Reviewer should inspect all 100 cards, choose an image or `NO_SUITABLE_IMAGE` where appropriate, add notes and export JSON. No public-rights approval or production promotion follows automatically. B-003.2 and Game UX/UI remain outside this task.
