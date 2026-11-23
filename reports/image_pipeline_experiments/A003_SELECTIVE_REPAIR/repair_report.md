# A-003.2 — Selective image repair for owner review

Date: 2026-11-23 (Asia/Saigon). Branch `main`, HEAD `936d9fdd27810e50a144fb6399e647b1ba18c371`. This is an **internal proposal**, not an approval or production change. The seven owner statements are preserved verbatim in A-003.1 `owner_feedback.json` and repeated in `proposed_image_selections.csv`. No new human labels were inferred for receive, book, or house.

## Existing candidates first

| Word | Proposal | Evidence and owner status |
|---|---|---|
| hungry | Keep `vocab-000046-ICON-01`, SHA-256 `14c6d40a…b0b56bfb0f` | Owner preferred the ICON result over the text-heavy NORMAL result. This candidate is clear; preference is recorded, promotion is still pending. |
| eat | Keep `vocab-000057-NORMAL-06`, SHA-256 `d4c2831a…c139ac91d0dc9918` | Owner preferred ORIGINAL. This image shows someone eating; no search was repeated. |
| receive | Offer `vocab-000063-ICON-07`, SHA-256 `930991ac…d208956973d04d7`, for review | Current `ICON-03` is intrinsically a screenshot of an icon listing with prominent text and several small symbols. `ICON-07` shows a parcel moving between hands on a cleaner field. `ICON-02` is also semantically clear, but its hands and box occupy nearly the whole image, so it is a weaker response to the owner's “oversized” concern. The A-003 gallery uses `object-fit: contain`; no code path crops or distorts the selected JPEG. The precise element the owner called oversized is still unknown. |
| buy | Offer `vocab-000059-ICON-01`, SHA-256 `56ac488b…c22a061e` | Owner prefers the ICON arm. Selected `ICON-06` prints “BUY” prominently; `ICON-01` depicts a cart and money without the English answer. `ICON-05` is a simpler cart alternative. No candidate has been owner-approved. |
| house | Offer `vocab-000021-NORMAL-05`, SHA-256 `e660532e…a33bc4e` | Direct visual inspection confirms a complete constructed house. Selected NORMAL-01 is an unfinished frame. The baseline and selected production image were not changed. |
| book | Offer existing `vocab-000031-ICON-03`, SHA-256 `f467af64…c4c71d` | Dataset meaning is English **book**, Japanese **ほん**, Vietnamese **sách**: a physical book. ICON-03 shows an open book without answer text; current NORMAL-06 is an exhibition poster. Because a viable candidate already exists, no new book search was run. `open book on table` is recorded as an **unexecuted** fallback query only if the owner rejects ICON-03. |
| sometimes | Propose `NO_SUITABLE_IMAGE` | Dataset meaning is English **sometimes**, Japanese **ときどき**, Vietnamese **thỉnh thoảng**: occasional frequency. Both original A-003 selections were rejected by the owner. New calendar and weather pools are technically valid but do not reliably distinguish “sometimes” from dates, future plans, or changing weather. The gallery shows the closest examples for review; no image is forced. |

All candidate IDs, full SHA-256 values, image paths, source URLs and available A-003/A-003.1 SigLIP scores are in `proposed_image_selections.csv` and the gallery. Scores support comparison only; they are not an educational quality threshold. Existing assets are referenced by path and were not copied into the repair directory.

## Targeted retrieval

Queries were frozen in `repair_manifest.json` before any request. Only `vocab-000083` triggered new search/download. Existing `book` ICON-03 satisfies the existing-candidate-first rule, so `book` used **0** new queries.

| Variant | Exact query | Search | Candidates | Valid JPEGs |
|---|---|---:|---:|---:|
| S1 | `some days calendar activity illustration` | SUCCESS | 7 | 7 |
| S2 | `occasional rain sunny days illustration` | SUCCESS | 7 | 6 |

Total: **2 successful searches, 14 candidate records, 13 downloaded/normalized images, 1 download failure**. The initial sandbox attempts for the same two queries timed out; the exact frozen queries succeeded after retry with network access. No third variant, other vocabulary item, query expansion, model download or SigLIP run was added. Results and failures are retained in `targeted_retrieval_results.json`.

Provider and validation: existing `imagecollector.search_images` and `download_candidate_image` with DuckDuckGo, region `wt-wt`, moderate safesearch, 7 results per query, 20-second timeout, 2 retries, 2-second retry delay; `normalize_image_to_jpeg` uses FIX-001 white alpha compositing and 1024×1024 maximum output. Source hashes and HEAD are in `repair_manifest.json`.

The S1 results are mostly day-of-week calendars and activity planners. S2 results are weather scenes; one has a Shutterstock mark. S1-03 marks a few calendar dates but does not clearly teach “sometimes” without explanation. S2-07 shows sunshine/cloud/rain panels but depicts weather change, not the frequency word by itself. The `NO_SUITABLE_IMAGE` proposal is therefore a conservative visual judgment, not a claim that no visual could ever represent the word.

## Review and boundaries

Open `review_gallery.html` locally. It shows the A-003 comparison image, proposed image or no-image outcome, relevant alternatives, the A-001 baseline, the exact owner statement, meaning, source links, scores and truncated hash. Each of seven items has `ACCEPT_PROPOSED`, `KEEP_ORIGINAL`, `NONE_SUITABLE`, `NEEDS_REVIEW`, notes and JSON export. All forms start unselected; exported decisions are a human-review draft tied to candidate hashes. No approval is fabricated.

Pending owner choice: receive ICON-07, buy ICON-01, house NORMAL-05, book ICON-03, and the `sometimes` no-image proposal. Hungry ICON-01 and eat NORMAL-06 preserve the owner's A/B preference, but final promotion/rights decisions remain separate. New images may have licensing or watermark limitations; no public eligibility is asserted. Game UX/UI remains **UNDECIDED**. Canonical dataset, production image directory, overrides, search routing, model and historical A-003/A-003.1 results were not edited.
