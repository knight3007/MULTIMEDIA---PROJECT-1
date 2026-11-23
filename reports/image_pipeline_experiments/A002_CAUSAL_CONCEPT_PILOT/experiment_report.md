# A002_CAUSAL_CONCEPT_PILOT — "because" (vocab-000081)

Status: **automated retrieval complete; owner selected V3-01.** Internal experiment only; production query strategy, Qwen prompts, routing, registry and media unchanged. Game UX/UI remains undecided.

## Owner decision

- **V3_BEST: candidate `V3-01`** (same image as `V2-01`). Recorded 2026-11-22T06:21:50.586946+00:00 from the owner's chat message "tôi chọn v3-01". No gallery export file exists (see `owner_review_decision.json` for why).
- Image SHA-256 `8dd3e8a22f6474a4a5dd3eb8adca453e61dfd7ca5aa65b2abc0e6036cfe2d7ab`; source https://stock.adobe.com/de/images/cause-and-effect-as-action-purpose-and-outcome-imminence-outline-diagram-labeled-educational-simple-scheme-with-situation-or-event-reason-and-consequence-vector-illustration-motive-and-result-factor/542231271.
- Open issues: Printed English labels (CAUSE AND EFFECT, CAUSE, EFFECT) remain in the image. Vertical Adobe Stock watermark; rights not cleared (D-003/META-001) and not eligible for public use as is. Image encodes cause->effect order (closer to 'therefore'); owner's reasons not stated.
- This is an experiment preference only. Nothing is promoted to production and the query strategy is unchanged.

## Target and meaning

- `vocab-000081` · EN *because* · JP *なぜなら* · VN *bởi vì* (A-001 matrix and `data/vocabulary/*.txt` row 81).
- なぜなら is a sentence-initial connective that introduces the reason for a statement already made (often closed with から). It is not interchangeable with clause-final から/ので in every context. `semantic_decisions_v1.json` marks this ID `needs_decision`.
- "because" presents the **effect first, then its reason** (B, because A). "therefore" runs the other way (A, therefore B). A left-to-right cause→effect picture is closer to "therefore"/"cause and effect" than to "because".

## Why `because icon` falls short

"because" names a logical relation between two events, not an object or an action. The icon search returned mostly ∴/∵-style dot symbols and a three-node graph (mathematical notation, some of which mean *therefore*). Its two pictorial candidates (a person with a question mark beside rain) are ambiguous.

## Variants (exact; V4 written and recorded before searching, no Qwen)

| Option | Query | Search | Downloaded | Selected | SigLIP(query) | SigLIP(fixed) | Best by fixed text |
|---|---|---|---|---|---|---|---|
| ORIGINAL | `because cause` | REFERENCE (A-001, not re-searched) | 0/0 | ORIGINAL | NOT_RUN | -9.047 | - |
| ICON | `because icon` | REFERENCE (A002_ICON_PILOT_20, not re-searched) | 7/7 | vocab-000081-01 | -4.078 | -11.875 | vocab-000081-06 |
| V1 | `cause and effect pictogram` | SUCCESS | 5/7 | V1-05 | 5.070 | -1.352 | V1-05 |
| V2 | `reason and result visual illustration` | SUCCESS | 7/7 | V2-05 | 4.836 | -8.211 | V2-01 |
| V3 | `cause effect visual sequence illustration` | SUCCESS | 7/7 | V3-01 | 3.273 | 1.648 | V3-01 |
| V4 | `child opening umbrella in the rain illustration` | SUCCESS | 6/6 | V4-03 | 2.633 | -9.359 | V4-01 |

- V4 rationale: Agent-written before searching (no Qwen): one frame can show both the cause (rain falling) and the result (child opening an umbrella), a familiar child-level situation, and the query avoids the word 'because' to reduce grammar slides and printed captions. Known risk: may read as 'rain' or 'umbrella' rather than the causal relation.
- Failed downloads: V1-02 (CollectionError: HTTP Error 400: Bad Request); V1-06 (CollectionError: HTTP Error 403: Forbidden). Duplicate URLs reused without a second download: V3-01 = V2-01.
- 4 real searches (DuckDuckGo `wt-wt`, moderate safesearch, 7 results each); retry/timeouts match A002_ICON_PILOT_20 (12 s, search retry 1, download retry 0).

## SigLIP results and limits

- Model `google/siglip2-so400m-patch16-384`, production `score_batch` formula (raw `logits_per_text`).
- **Query score**: each candidate is scored against its own variant's query, as in production; the top score is selected. These scores are **not comparable across variants**.
- **Fixed-text score**: every candidate, plus the original image and all icon-pilot candidates, is also scored against one fixed description, "an illustration in which one event causes another event to happen". It is a weak, shared yardstick only.
  - The highest fixed-text score is V2-01/V3-01 (1.65). Next come V1-05 (-1.35) and V1-01 (-2.86).
  - The V4 child images score low (-6.9 to -11.5) even though they contain no text.
  - The original scores -9.05; the icon pick scores -11.88; the best icon-pool image (81-06) scores -6.85.
  - SigLIP rewards printed words like "cause/effect" and does not measure text independence or learner clarity.
- Query-score selection picked text-dominant images for V1 (V1-05) and V2 (V2-05). This shows that query-matched SigLIP ranking is unreliable for this category.

## Automated assessment (AI preliminary, not human)

NO_SUITABLE_VISUAL_FOUND (AI preliminary): no candidate is simultaneously text-free, watermark-free and explicit about the because-relation. Closest: V2-01/V3-01 (explicit causality, but text and watermark) and V4-02/V4-03 (text-free, but implicit causality).

| Option | Observation |
|---|---|
| ORIGINAL | Grammar slide 'Because Sentence' with example sentences; dominant English text; not text-independent. |
| ICON | Selected 81-01 is an abstract three-node graph shaped like the ∴ (therefore) sign; 81-02..05 are ∴/∵ dot symbols (mathematical notation, and ∴ is the opposite connective). 81-06/07 show a person with a question mark beside rain: closest to a reason, but ambiguous (07 has an alamy watermark). |
| V1 | All pool members are business fishbone or labelled diagrams; selected V1-05 is a 'CAUSE & EFFECT DIAGRAM' text sign. Text-dominant and abstract; poor for learners. |
| V2 | Selected V2-05 is a 'REASON / RESULT' letter-tile crossword (pure English text). Pool member V2-01 (same file as V3-01) is the strongest conceptual image: rain cloud + sun → arrow → tree, but labelled CAUSE/EFFECT and carrying a vertical Adobe Stock watermark. |
| V3 | Selected V3-01 is the same image as V2-01: a concrete cause→effect scene (rain and sun make a tree grow) with an arrow, but printed labels and a watermark. Other pool members are fishbone templates, flow charts and a text-heavy anchor chart. |
| V4 | Text-free child illustrations: rain + umbrella (selected V4-03 girl with umbrella; V4-02 boy with red umbrella has no visible watermark). The cause (rain) and the response (umbrella) are both present, but the link is implicit: a learner may read it as 'rain' or 'umbrella', not 'because'. V4-01/06 have watermarks; V4-05 has a dreamstime footer. |

Criteria applied: causality, alignment with "because" (versus cause, effect, therefore), clarity, educational use, text independence, ambiguity, clutter, later media suitability. Rights are not assessed. Adobe Stock, alamy and dreamstime watermarks suggest restricted sources (see D-003/META-001).

## Strategy assessment (options only; nothing adopted)

1. **Ordinary icon search** is not suitable for logical connectors. It returns notation or abstract glyphs, and some carry the opposite meaning (∴).
2. **Cause-and-effect diagram search** returns explicit causality but almost always printed labels, business fishbone charts or stock watermarks. It also encodes cause→effect order (closer to "therefore").
3. **Concrete contextual illustration search (V4)** gives text-free, child-friendly images. The relation stays implicit, though, and the image tends to teach the noun (rain or umbrella) instead.
4. **Multi-panel examples**: two panels, effect then reason (for example a wet or umbrella scene, then a rain cloud, with a back-pointing link). This could match "B because A" and なぜなら word order, but search is unlikely to find it ready-made; it would need curation or composition.
5. **Manual curation for abstract connectors** (because, therefore, but, if…): a small, human-picked set reviewed against the criteria above. For this category it is likely more reliable than automated ranking.

Similar words for possible future pilots (identified only, not searched): therefore, so, but, if, although and other connectors, where they exist in the benchmark. A separate authorization is required.

## Files

`experiment_manifest.json`, `query_variants.csv`, `retrieval_results.json` (all candidates, URLs, titles, hashes, both scores, errors), `comparison.csv`, `review_gallery.html`, `images/V1..V4/NN.{img,jpg}`, `run_causal.py` (resumable runner), `render_causal.py` (offline renderer).
