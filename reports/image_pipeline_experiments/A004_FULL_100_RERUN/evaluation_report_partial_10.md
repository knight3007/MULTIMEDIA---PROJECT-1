# A-004 partial run report — 2026-11-23

**Status: PARTIAL, stopped by owner after automatic approval review reported that the workspace was out of credits.** The continuation command for the remaining 90 image IDs was rejected before execution. This is **not** a completed 100-word image rerun. No gallery or human review export was produced for this partial run.

## Frozen execution and actual counts

- Frozen vocabulary: **100/100 unique IDs**, dataset SHA-256 `644c2dc9899077dad15d2e2916d7dc3d1cef49ecd151ea406115bb3da19481bd`; exact configuration, Git state, model revisions and code hashes are in `experiment_manifest.json`.
- Qwen local 1.7B: **100/100 IDs attempted exactly once**, raw output retained; **94/100 syntactically valid normalized queries**, of which **93/100 effective queries** can proceed. Six outputs (`go/read/eat/help/choose/swim verb`) failed the existing query validator; ID038 has a valid Qwen query but lacks owner-approved image search intent. No correction retry or old cache was used.
- Image search: **10/100 IDs attempted**, **10/10 searches succeeded**. The remaining **90/100 IDs were not attempted** due to the approval-credit block. Search settings: one query/ID, up to seven results, 20 s timeout, zero retries. Query status for the unrun image IDs remains in `query_results.json`.
- Candidate downloads: **50 successful**, **14 failed** among **64 candidate records** from the ten attempted IDs. Each successful raw/JPEG file exists and matches its recorded SHA-256.
- SigLIP: **9/10 attempted IDs ranked once**; **1/10** had no valid download. Proposed top-ranked JPEGs: **9/100 benchmark IDs**; these are unapproved suggestions. ID008 water returned one URL, which failed with HTTP 404.
- Audio: existing A-001 references **100/100 hash-match**, missing reference 0, missing file 0, mismatch 0. No audio was regenerated.

## Image quality (AI_PRELIMINARY, 9 visually inspected new top-1 images)

- Semantic relevance: **8/9 PASS**, **1/9 NEEDS_REVIEW**; 91 benchmark IDs lack a new image judgment. Educational suitability: **5/9 PASS**, **1/9 NEEDS_REVIEW**, **3/9 FAIL**. These are analyst observations, not human verification or public-rights approval.
- A-001 comparison on these same **9/100** IDs: **1 improved, 5 unchanged, 3 degraded** (AI_PRELIMINARY). New images are different hashes from A-001; visual descriptions, not a human-verified improvement rate, support these labels. ID008 and 90 unrun IDs are **not comparable**.
- Main observed problems: ID007 milk top-1 is a text-heavy collage and no clearly clean plain-milk candidate appears in its saved pool (retrieval/presentation concern); ID009 chicken meat top-1 has a Depositphotos watermark while a cleaner lower-ranked cooked-chicken candidate exists (ranking/presentation concern); ID010 breakfast top-1 is a multi-panel collage while a clearer lower-ranked meal exists (ranking/presentation concern); ID003 strawberry top-1 includes unripe fruit/clutter while a clearer isolated fruit ranks lower (presentation/ranking concern). ID008 is a candidate URL/download failure, not a proven semantic retrieval failure. No SigLIP blame is assigned without the saved pool.
- `NO_SUITABLE_IMAGE` is an available review outcome; no new owner rejection was inferred. Prior A-003.3 selections and `because` internal-only override were neither copied into this run nor promoted.

## Evidence and limits

`query_results.json` retains raw Qwen output; `retrieval_results.json` retains URL/source, per-candidate errors and score/rank; `candidate_rankings.csv` and `evaluation_matrix.csv` summarize all attempted candidates and all 100 IDs. [Top-1 contact sheet](top1_contact_sheet.jpg), [A-001 comparison sheet](a001_first_batch_contact_sheet.jpg) and [selected pools](candidate_diagnosis_sheet.jpg) support preliminary inspection. The first ten IDs are an ordered slice, not a random sample; no 100-word quality rate can be extrapolated. Full owner review gallery/export was not built because the owner asked to complete only the report of work already run. Game UX/UI remains undecided.

The 90 image IDs remain unexecuted. The exact blocker was automatic approval review failure: **workspace out of credits**. The system stated this was a review failure, not a safety determination, and instructed not to bypass the approval check. Resume only after credits/approval are restored and the owner explicitly asks to continue; the frozen run ledgers prevent rerunning completed IDs. B-003.2 remains paused.
