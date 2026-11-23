# A-003 — Controlled evaluation of conditional image search

Status: **automated stages complete; human review pending (0/12).** Internal experiment. Production pipeline, Qwen prompts, routing, registry, `data/` and `unified_dataset_v1.json` (hash `644c2dc9…`) are unchanged. Game UX/UI remains undecided. Decisions D-015/D-016 ("because" V3-01 internal-only via an override file) are preserved and not reopened.

## Design

- **Holdout**: 12 IDs frozen in `frozen_sample.csv` before any request (git HEAD `936d9fdd2781`, sample SHA-256 in the manifest), with no substitution.
  - 6 CONCRETE: apple, cat, mountain, house, car, book.
  - 3 DIFFICULT_ACTION: eat, buy, receive.
  - 3 DIFFICULT_ABSTRACT: happy, hungry, sometimes.
  - Excluded: the 20 icon-pilot IDs, the causal ID 081, 086 *why* (its baseline query is already "why icon", which would confound the arms) and 038 *friend* (no baseline query).
  - The sample is chosen, not random: it covers the task's named examples and spans semantic groups and A-001 outcomes (PASS and FAIL). It is not the earlier pilot.
- **Arms**:
  - A NORMAL = the A-001 `effective_image_query` (cached Qwen output; Qwen not called).
  - B ICON = `<english> icon`.
  - Arm order alternates per item (NORMAL first on odd positions) to spread time effects.
- **Identical settings for both arms**: DuckDuckGo `wt-wt`, moderate safesearch, 7 results; production defaults of timeout 20 s, search retries 2, download retries 2, retry delay 2 s; 2 s pause.
- **Scoring**:
  - SigLIP `google/siglip2-so400m-patch16-384` with the unchanged `score_batch`.
  - **Query score**: each arm is scored against its own query (production rule) and the top score is selected.
  - **Shared score**: both arms are scored against the bare English word. This is a cross-arm yardstick only.

## Technical results

| Metric | NORMAL | ICON |
|---|---|---|
| Search success | 12/12 | 12/12 |
| Candidates / downloaded | 81 / 74 | 77 / 73 |
| Ranked (SigLIP) | 12/12 | 12/12 |
| Transparent (alpha) downloads | 3 | 29 |
| Flattened to a black square | 0 | 8 |
| Mean search / download time per arm (s) | 0.71 / 10.44 | 0.61 / 5.12 |

There were no search failures, timeouts or rate limits. Download failures (HTTP 402/403/404, non-image payloads) are listed per arm in `comparison_matrix.csv`. *sometimes icon* returned only 1 result.

**Technical defect found, affecting the icon strategy.** `imagecollector.normalize_image_to_jpeg` and `SiglipImageScorer.score_batch` call `.convert("RGB")` on transparent PNG/WebP images without compositing them onto a background, so transparent areas become black.
- Icon results are much more often transparent: ICON 29 vs NORMAL 3 candidates in this run.
- Here, 8 ICON candidates became solid black squares, 6 of 7 for *car icon*.
- SigLIP also ranks these blacked-out versions.
- In the earlier A002_ICON_PILOT_20, 61 of 129 candidates and **10 of 20 selected icons** had transparency flattened. Their black backgrounds come from this defect, not from the source images.

## Per-item comparison (AI preliminary; human 0/12)

| ID | Word | Category | Normal query | N dl | N selected | N shared | I dl | I selected | I shared | AI preference | Issue |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 001 | apple | CONCRETE | `apple fruit` | 5/7 | NORMAL-06 | -1.406 | 6/7 (đen 0) | ICON-07 | -0.852 | **BOTH_GOOD** | pool_brand_collision |
| 011 | cat | CONCRETE | `cat animal` | 7/7 | NORMAL-07 | -3.062 | 7/7 (đen 0) | ICON-01 | -3.641 | **BOTH_GOOD** | alpha_artifacts |
| 016 | mountain | CONCRETE | `mountain place` | 7/7 | NORMAL-01 | -3.617 | 7/7 (đen 0) | ICON-06 | -1.727 | **BOTH_GOOD** | watermark_in_pool |
| 021 | house | CONCRETE | `house building` | 6/7 | NORMAL-01 | -6.195 | 7/7 (đen 1) | ICON-05 | -3.828 | **ICON_BETTER** | normal_query_sense |
| 028 | car | CONCRETE | `car vehicle` | 7/7 | NORMAL-04 | -4.820 | 7/7 (đen 6) | ICON-01 | -3.781 | **NORMAL_BETTER** | alpha_black_squares |
| 031 | book | CONCRETE | `book object` | 7/7 | NORMAL-06 | -3.211 | 5/6 (đen 0) | ICON-01 | -1.766 | **ICON_BETTER** | normal_query_sense |
| 057 | eat | DIFFICULT_ACTION | `person eating` | 7/7 | NORMAL-06 | -6.078 | 6/7 (đen 0) | ICON-07 | -14.750 | **NORMAL_BETTER** | icon_semantic_failure |
| 059 | buy | DIFFICULT_ACTION | `buy action` | 6/7 | NORMAL-01 | -10.953 | 7/7 (đen 0) | ICON-06 | 0.789 | **ICON_BETTER** | icon_selected_text |
| 063 | receive | DIFFICULT_ACTION | `receive action` | 5/5 | NORMAL-01 | -5.203 | 7/7 (đen 0) | ICON-03 | 2.586 | **BOTH_BAD** | ranking_miss_icon_pool_good |
| 045 | happy | DIFFICULT_ABSTRACT | `happy emotion` | 6/6 | NORMAL-01 | -3.383 | 6/7 (đen 0) | ICON-04 | -1.484 | **BOTH_GOOD** | alpha_artifacts |
| 046 | hungry | DIFFICULT_ABSTRACT | `hungry appetite` | 6/7 | NORMAL-01 | -1.484 | 7/7 (đen 1) | ICON-01 | -0.227 | **ICON_BETTER** | normal_text_heavy |
| 083 | sometimes | DIFFICULT_ABSTRACT | `sometimes event` | 5/7 | NORMAL-04 | -5.430 | 1/1 (đen 0) | ICON-01 | -15.078 | **BOTH_BAD** | no_suitable_image |

AI preliminary tally of the selected outputs:
- CONCRETE: {'BOTH_GOOD': 3, 'ICON_BETTER': 2, 'NORMAL_BETTER': 1}
- DIFFICULT: {'NORMAL_BETTER': 1, 'ICON_BETTER': 2, 'BOTH_BAD': 2, 'BOTH_GOOD': 1}

The ICON selection had the higher shared-word SigLIP score in 9/12 items. That is not quality evidence: SigLIP rewards printed words and logos, and both arms were scored against the bare word.

- **apple**: Normal: Selected: red/green apples photo; clear. Icon: Selected: flat red-apple icon; clear. Pool risk: 4/6 icons are the Apple Inc. logo (brand ambiguity).
- **cat**: Normal: Selected: cat photo; clear. Icon: Selected: line-art cat face; clear. Pool: 4 candidates have alpha/fake checkerboard silhouettes.
- **mountain**: Normal: Selected: alpine peaks over village (= A-001 image); clear. Icon: Selected: blue mountain pictogram; clear. Pool: ICON-ICONS watermarks on 05/07.
- **house**: Normal: Selected: house under construction; normal query 'house building' drifts to construction (query-sense defect, as in A-001). Icon: Selected: white house pictogram; clear. 03 flattened to a black square.
- **car**: Normal: Selected: classic car in desert; clear. Icon: Selected: car icon with 'shutterstock' text watermark; 6/7 candidates flattened to black squares (transparent PNGs).
- **book**: Normal: Selected: 'BOOK OBJECT ART' exhibition poster, wrong referent; pool is book clip-art collections with alamy footers. Query 'book object' drifts. Icon: Selected: dark stacked-books icon (alpha flattened, dark); 03 open book and 06 book stack are clearer.
- **eat**: Normal: Selected: woman eating salad; clear action. Icon: All candidates show a music artist (name collision on 'eat icon'); semantically wrong.
- **buy**: Normal: Selected: 'Action' retail store (brand match); pool is action figures; wrong meaning. Icon: Selected: 'BUY' button with hand: answer-revealing text. Pool 01/02/05 shopping-cart icons are text-free and clear.
- **receive**: Normal: Selected: give-vs-receive flowchart (= A-001 image); text-heavy. Pool: worksheets/screenshots. Icon: Selected: 'Receive icons' web page with text, a ranking miss. Pool 01 (hand receiving box) and 07 (box between hands) are good.
- **happy**: Normal: Selected: 3D smiling emoji (= A-001 image); clear. Icon: Selected: laughing emoji on black (alpha flattened); clear. 01 has an ICON-ICONS watermark.
- **hungry**: Normal: Selected: 'Hunger vs Appetite' infographic (= A-001 image); text-dominant. Icon: Selected: drooling emoji thinking of a burger; text-free, clear. Pool: several person-thinking-of-food icons, some flattened to dark backgrounds.
- **sometimes**: Normal: Selected: event poster with 'Sometimes' text; pool is text or grammar slides. Icon: Only 1 result: a visual-search web page screenshot; unusable.

## Decision gate (preliminary; 12 items, AI desk review, no human labels)

1. **Does "icon" improve difficult words on this sample?** It helped buy and hungry (the selected or pool images are clearly better). It hurt *eat* (name collision returned a musician). Receive had a good icon pool but a text page was selected. Neither arm worked for *sometimes*; happy was good in both. The result is **mixed, not a general improvement**: 2 better, 1 worse, 1 tie, 2 both bad out of 6.
2. **Does it harm simple concrete words?** Sometimes.
   - Car: the icon selection carries a shutterstock watermark, and 6/7 candidates were black squares.
   - Apple: the icon pool is dominated by the Apple Inc. logo, though the selected icon is fine.
   - Cat and mountain were fine in both arms.
   - House and book were *better* as icons, but only because their Qwen normal queries ("house building", "book object") drift. That is a query-sense problem, not evidence for icons.
3. **Which categories benefit?** Depictable actions, states and objects whose normal query returns infographics, brand pages or the wrong sense: buy, hungry, (receive pool), house, book. This matches the A-002 pilot pattern for motion verbs and weather.
4. **Which remain unresolved?**
   - Frequency and time adverbs (*sometimes*; *always/today/tomorrow* earlier relied on printed text).
   - Logical connectors (*because*: curated internal image only).
   - Words whose "<word> icon" collides with a name or brand (*eat*, *apple*).
5. **Is a conditional strategy justified?** **Partly, as a candidate source rather than a fixed routing rule.** A single word-category switch is not supported, because icon results also failed on an action (eat) and hurt a concrete noun (car). What the evidence supports better: generate **both pools** for non-concrete or low-confidence items, then reject bad candidates and let a person choose, rather than rely on SigLIP's top score.
6. **What evidence is missing?**
   - Human A/B labels for these 12 (and per-item labels for the 20-word pilot; the owner's feedback was qualitative).
   - A larger randomized sample per category.
   - Results after the alpha fix, since 10 of 20 pilot icons and several A-003 icons were scored and shown with black backgrounds.
   - Inter-rater agreement.
   - Rights for icon sources (ICON-ICONS, shutterstock, alamy marks).
   - Any measure of text or answer leakage.
7. **Minimal production changes that would be needed (proposal, not implemented)**:
   - (a) Composite RGBA/LA/P-with-transparency images onto white before `.convert("RGB")`, in both `normalize_image_to_jpeg` and `score_batch`, with a unit test using a transparent PNG.
   - (b) An optional second query arm, `<english> icon`, behind an explicit per-item flag or list. Never a default for all words; the normal arm is kept.
   - (c) Record both pools and a `NO_SUITABLE_IMAGE` outcome in metadata instead of always selecting a top score.
   - (d) A small manual-curation override path (the D-016 override file is a working precedent).
   - Qwen prompts and routing would not change.
8. **Proceed to integration or revise?** **Revise first; do not integrate yet.** Recommended order: alpha fix (low risk, clear defect) → owner reviews these 12 pairs → decide whether to adopt the dual-pool, human-in-the-loop approach for flagged words.

## Proposed `NO_SUITABLE_IMAGE` outcome (documentation only)

Reject a candidate when any of these hold; return `NO_SUITABLE_IMAGE` when no candidate in any arm survives:

1. **Semantic**: wrong referent or sense (brand or name collision, e.g. *eat icon* musician, Apple logo, "Action" store; construction for *house*).
2. **Text or answer leakage**: the target word or its translation is printed prominently, or text is the main content (BUY button, grammar slides, infographics, posters).
3. **Watermark or stock overlay** covering the subject (shutterstock, alamy, ICON-ICONS, Adobe Stock). This is flagged separately from rights.
4. **Technically invalid**: non-image payload, too small, mostly uniform or near-black after normalization, fake checkerboard "transparency".
5. **Ambiguity or learning unsuitability**: abstract notation (∴/∵), unrelated collage, or a scene that teaches a different word (*rain/umbrella* for "because").

Fallback order (proposal):
- Normal pool → icon pool (flagged words only) → manual curation or override file → leave the image **missing** with reason `NO_SUITABLE_IMAGE`.
- Never force the top SigLIP score.
- SigLIP can pre-sort, and automated checks can handle 4 (uniform or black detection) and part of 3. Rules 1, 2 and 5 need either an OCR/text detector (not present today) or human review.
- `dataset_builder` already supports `status: missing`, so this outcome needs no schema change for the record. Only the metadata reason field is new.

## Recommended conditional strategy (proposal)

| Category | Proposal | Evidence level |
|---|---|---|
| A — Concrete nouns | Keep the normal Qwen query. Fix query-sense drift (house, book) through `semantic_decisions` overrides, not icons. | Weak–moderate (6 items; owner's earlier qualitative OK) |
| B — Depictable actions/states | Fetch the normal and icon pools; a person picks, with rejection rules applied. Do not auto-select the icon top score. | Weak (pilot 20 qualitative + A-003 3 of 6 positive) |
| C — Abstract, time and connector words | Manual curation or override, a contextual or multi-panel image, or `NO_SUITABLE_IMAGE`. Do not generalize the "because" approach without per-word evidence. | Weak (because + sometimes) |

**Limitations**: 12 items chosen rather than randomly sampled, a single run, one provider, search results that drift over time, AI desk review only, black-flattened icons, and no rights review. No general effectiveness claim.

## Files

`experiment_manifest.json`, `frozen_sample.csv`, `retrieval_results.json`, `comparison_matrix.csv`, `review_gallery.html`, `images/<vocab_id>/<NORMAL|ICON>/NN.{img,jpg}`, `run_a003.py`, `render_a003.py`.
