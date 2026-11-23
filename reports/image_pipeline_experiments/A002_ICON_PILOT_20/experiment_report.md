# A-002 icon pilot — automated retrieval report

Experiment `A002_ICON_PILOT_20`; 20 selected IDs. Source A-001 matrix SHA-256 `0e066ed052f07ca7de59a8b75a723aaba9ca89be364c6c2827785b1577b23e5f`. Query variant is exactly `<english> icon`; no Qwen rerun. Provider and SigLIP settings are in `experiment_manifest.json`.

- Search SUCCESS: 20/20; FAILED: 0; NOT_RUN: 0.
- Candidate images downloaded and retained: 129; items with at least one downloaded image: 20/20.
- Items scored by SigLIP: 20/20. Selection without scoring uses first valid result and is labeled accordingly.
- Items with no suitable image: **UNKNOWN until human review**. Technical download success is not educational suitability.
- Human A/B decisions: 0. Do not call a winner before owner review.

## Differences from the production collector (recorded, not hidden)

- Same: `imagecollector.search_images` (DuckDuckGo via `ddgs`, region `wt-wt`, safesearch `moderate`), `DEFAULT_PAGE_SIZE` 7 candidates (below the 10-candidate cap), `download_candidate_image`/`normalize_image_to_jpeg`, and `SiglipImageScorer` with `google/siglip2-so400m-patch16-384`, ranking candidates against the search query and selecting the top score.
- Different: timeout 12 s (production default 20 s); search retries 1 (production 2); download retries 0 (production 2); 2 s pause between items; every downloaded candidate is normalized to JPEG and kept under `images/<vocab_id>/` instead of only the winner in `data/image/en/`.
- Baseline A images come from the original Qwen-query run (staging paths/hashes in `selected_vocabulary.csv`). The original search candidates were not retained, so A has no candidate pool to compare against B.
- Searches run on a different date than the original run, so search results can differ for reasons other than the query change.

## Per-item results

| ID | English | Icon query | Search | Downloaded | Ranking | Selected | Score |
|---|---|---|---|---|---|---|---|
| vocab-000019 | rain | `rain icon` | SUCCESS | 6/6 | SCORED | vocab-000019-05 | 2.1484 |
| vocab-000041 | today | `today icon` | SUCCESS | 7/7 | SCORED | vocab-000041-01 | 5.0547 |
| vocab-000042 | tomorrow | `tomorrow icon` | SUCCESS | 7/7 | SCORED | vocab-000042-07 | 6.6641 |
| vocab-000043 | yesterday | `yesterday icon` | SUCCESS | 7/7 | SCORED | vocab-000043-01 | 6.1797 |
| vocab-000047 | easy | `easy icon` | SUCCESS | 7/7 | SCORED | vocab-000047-02 | 7.7891 |
| vocab-000048 | difficult | `difficult icon` | SUCCESS | 7/7 | SCORED | vocab-000048-06 | 3.4609 |
| vocab-000051 | go | `go icon` | SUCCESS | 6/6 | SCORED | vocab-000051-04 | 6.8203 |
| vocab-000053 | write | `write icon` | SUCCESS | 7/7 | SCORED | vocab-000053-04 | 1.5391 |
| vocab-000054 | study | `study icon` | SUCCESS | 7/7 | SCORED | vocab-000054-03 | -0.1719 |
| vocab-000055 | work | `work icon` | SUCCESS | 5/5 | SCORED | vocab-000055-01 | 0.1641 |
| vocab-000056 | sleep | `sleep icon` | SUCCESS | 6/6 | SCORED | vocab-000056-06 | 2.9141 |
| vocab-000058 | drink | `drink icon` | SUCCESS | 6/6 | SCORED | vocab-000058-01 | -0.6797 |
| vocab-000061 | understand | `understand icon` | SUCCESS | 7/7 | SCORED | vocab-000061-07 | 2.4766 |
| vocab-000062 | remember | `remember icon` | SUCCESS | 6/6 | SCORED | vocab-000062-06 | 1.2266 |
| vocab-000065 | swim | `swim icon` | SUCCESS | 7/7 | SCORED | vocab-000065-03 | 2.9766 |
| vocab-000075 | experience | `experience icon` | SUCCESS | 4/4 | SCORED | vocab-000075-04 | -2.1562 |
| vocab-000077 | important | `important icon` | SUCCESS | 7/7 | SCORED | vocab-000077-07 | 1.5547 |
| vocab-000078 | different | `different icon` | SUCCESS | 6/7 | SCORED | vocab-000078-06 | -3.9688 |
| vocab-000081 | because | `because icon` | SUCCESS | 7/7 | SCORED | vocab-000081-01 | -4.0781 |
| vocab-000082 | always | `always icon` | SUCCESS | 7/7 | SCORED | vocab-000082-02 | 0.0312 |

Failed downloads: vocab-000078-07 (CollectionError: HTTP Error 403: Forbidden).

SigLIP scores are comparable only within one item's candidate pool. They are not comparable across items or with the baseline, which was scored against a different query text.

AI-preliminary visual notes, which are not human decisions: `automated_visual_observations.md`.

See `comparison.csv` for baseline query/image/hash, icon query/selected image/hash, scores and blank human fields. `retrieval_results.json` preserves candidate IDs, URLs, titles, paths, hashes, errors and timings. Open `review_gallery.html` locally for side-by-side inspection and JSON export. This is internal evaluation only; Game UX/UI remains undecided. No production media or query strategy was replaced.
