# Fixed-subset benchmark design for the next phase

The subset is frozen before any new inference: `001, 004, 009, 011, 014, 018, 019, 023, 035, 038, 041, 043, 047, 051, 052, 054, 057, 059, 065, 069, 077, 082, 085, 088, 093` (25 stable IDs). It includes common objects, owner-approved sense conflicts, a missing-intent item, ambiguous and abstract terms, verbs/adjectives, preview/watermark examples, and apparently usable images. Selection is deliberately not restricted to easy nouns.

## Stage 1: smallest query-only paired test

1. Freeze the existing ledger `02_qwen_queries_100.json`, source triples and owner decisions by SHA-256.
2. Run the **same** `Qwen/Qwen3-1.7B` runtime for only these 25 IDs with one versioned target-sense-aware prompt. Keep `max_new_tokens=32`, greedy decoding, non-thinking mode, model revision and batch size recorded. Write decoded raw text, parse status, latency and failure reason to a new isolated diagnostic cache. Never alter historical caches.
3. Blindly randomize baseline/new query order for a bilingual reviewer. Label: correct intended meaning, concrete/visually depictable, ambiguous or wrong sense, and inappropriate text/brand lure. Record rationale and reviewer identity. ID 038 may be labeled for sense but remains blocked from image search until image intent is approved.
4. Compare paired query semantic correctness and failure counts. Report per-category changes and all 25 examples; do not claim population significance from this small set.

## Stage 2: candidate-level test only after Stage 1

For a later separately approved run, fix search backend, region, safe-search setting, request budget and candidate count. Save all result positions, URLs, fetch outcomes, content hashes, previews and source pages. Score a *fixed downloaded pool* with current SigLIP2, then any alternative ranker, using the same textual target. Human reviewers label candidate relevance and visible marks. This separates search recall from ranker precision. Hold out a second subset before tuning thresholds.

| Metric | Current audit value | Required next evidence |
|---|---|---|
| Query semantic correctness | Not measured by independent human labels | Blind paired labels for 25 IDs |
| Candidate Recall@3/5 | Not computable: alternative candidates and labels absent | Saved complete pool and human relevance labels |
| Top-1 suitability | 54 provisional visual flags among 99 selected assets; not a formal accuracy estimate | Blind per-image labels |
| Top-3/Top-5 suitability | Not computable | Candidate previews and labels |
| Watermark/restricted-source rate | Visible marks triaged; 89 new image licenses unknown | Exact-page rights review and consistent watermark labels |
| Technical image coverage | 99/100 IDs | Same stable IDs, separate from approval |
| Processing time | Search seconds in many manifests; Qwen and complete request timing not consistently persisted | Per-stage timestamps and wall-clock totals |
| GPU memory / request cost | 4 GiB GPU hardware known; per-item peak and request cost not measured | Peak VRAM telemetry, DDGS calls, model time |
| Failure rate | No unresolved selected-image technical failure; ID 038 semantic block | Per-stage attempts, 403/429 and rejected-candidate logs |

Do not interpret SigLIP logits as probabilities, compare candidate scores across different model variants without calibration, or treat an automated quality score as owner approval. The first implementation task is the bounded query-only experiment above; model replacement and bulk recollection wait for evidence.
