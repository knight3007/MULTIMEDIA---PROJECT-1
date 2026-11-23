# A-001 first quality round — preliminary

**Run:** A-001 / 22/11/2026, existing-output review only. Every query/image label below is **AI preliminary**, not independent human ground truth. All 100 IDs assessed; 99 selected images viewed through newly generated contact sheets, with seven full-resolution follow-ups. No inference, download or new audio listening. Current primary selected assets (including staged replacements for 004/009) are distinct from old production assets. Historical labels are retained in the JSON matrix; new labels do not rewrite them. License is context only, excluded from quality scores.

## Decision gate

**First evidence-based review package complete; final human-verified quality evaluation remains NEEDS_REVIEW.** B-002/Web Game work remains paused by the current user instruction. Audio has been accepted PASS for all 100 by the owner during this session and needs no further listening review. Main work is correcting selected images and the query/retrieval/ranking decisions feeding them.

| Metric | PASS | FAIL | NEEDS_REVIEW | UNKNOWN | P+F denominator | PASS/(P+F) |
| --- | --- | --- | --- | --- | --- | --- |
| query_overall | 37 | 22 | 41 | 0 | 59 | 62.71% |
| query_correct_meaning | 75 | 16 | 9 | 0 | 91 | 82.42% |
| image_relevance | 44 | 27 | 28 | 1 | 71 | 61.97% |
| image_visual_quality | 39 | 47 | 13 | 1 | 86 | 45.35% |
| image_learning_suitability | 27 | 55 | 17 | 1 | 82 | 32.93% |
| audio_pronunciation_review | 100 | 0 | 0 | 0 | 100 | 100.0% |
| image_technical | 99 | 0 | 0 | 1 | 99 | 100.0% |
| audio_technical | 100 | 0 | 0 | 0 | 100 | 100.0% |

Each row uses N=100 vocabulary IDs; counts are also percentages of the total set. Query composite PASS requires all six checks; correct meaning alone is a different metric. Definitive P+F denominators are reported explicitly and exclude uncertain IDs. No UNKNOWN is counted as PASS. Image N=99 available files + 1 missing ID (038). Query/image labels are AI preliminary, **zero new independent human per-item query/image labels**. Audio 100/100 is a separate current owner batch acceptance, not an inferred consequence of MP3 existence.

## Answers for next decisions

1. **Qwen level:** original parsed query meaning: 75 PASS / 16 FAIL / 9 NEEDS_REVIEW; composite suitability: 37 / 22 / 41. This is not controlled model accuracy or proof of 100/100. Two original query mismatches (004/009) have approved target evidence; remaining linguistic judgments need owner review.
2. **Images:** relevance 44 PASS / 27 FAIL / 28 NEEDS_REVIEW / 1 UNKNOWN; learning suitability 27 / 55 / 17 / 1. Technical validation passes for 99 files, which does not make their content correct. Primary rice/chicken replacements differ from old production images; both versions retained in matrix evidence.
3. **Severe failures:** 035 shirt retrieves a nasal diagram; 041/042 time words become watches; 043/085/087 title matches; 051/065 action queries yield portraits; dense charts/preview text contaminate many outputs. See 03/05 reports and contact sheets.
4. **Change model?** Insufficient comparative evidence. Fix sense/visual intent and retrieval/acceptance first; preserve candidates/scores before diagnosing ranking. No proof a 4B model or Native runtime solves these failures.
5. **First corrections:** owner decides uncertain meanings/selected image labels; specify noun/action/time-aware queries; reject wrong titles, text-dominated previews and irrelevant one-candidate pools; retain complete evidence for later ranking tests. No changes made to pipeline.
6. **Next experiments:** frozen small failure/control set, fixed-input prompt comparison, then fixed-query retrieval and retained-candidate ranking comparison, only with separate execution authorization. No model/media/network run in this round.
7. **A-002 entry:** user requests it; consume this matrix and owner labels, confirm current asset hashes and choose diagnostic cases. Missing full candidate/score history must stay MISSING_EVIDENCE. A-002 can inspect known cases but cannot claim ranking root cause or rerun models/download without additional authorization. Do not auto-start A-002 or B-002.

## Evidence gaps and interpretation

- 94 accepted raw decoded query outputs missing; all 100 parsed queries verified against existing cache.
- Exact generation revisions for these historical 100 items missing. Original cache signature/correction prompt evidence is stored per ID, not replaced with a later benchmark revision.
- Full historical candidate list/bytes and complete SigLIP score ordering are missing for all 98 applicable search-selected primary assets. ID009 is a curated direct replacement (no comparative pool); ID038 was blocked before retrieval. 99 selected-image scores exist, including the curated score, but no score threshold is inferred. Counts identify the one-candidate cases, not every rejected alternative.
- ID038 selected image missing due an approved-image-intent gate, not a corrupted media file.
- No new agent audio listening; current owner acceptance governs all 100 audio. Historical listening records remain preserved for provenance.
- No independent human query/image labels collected by the agent. Gallery enables owner review and export. Quality is separate from rights/public eligibility; no full copyright audit performed.

## Outputs and verification

`evaluation_matrix.csv` / JSON: 100 IDs, full reconstruction and six query dimensions, image observations, audio evidence, hashes, historical labels, missing evidence and attribution. `02_semantic_assessment.md`, `03_image_assessment.md`, `04_audio_assessment.md`, `05_error_attribution.md`: per-ID judgments and denominators. `review_gallery.html` + local JS/CSS: owner package; `06_human_review_instructions.md`: use/export instructions. `owner_audio_acceptance.json`: current batch acceptance bound to 100 hashes. `statistics.json`, evidence/baseline hashes and authoring label table preserve provenance. `verification.md` records checks and browser results.
