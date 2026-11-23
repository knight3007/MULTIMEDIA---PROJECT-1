# A-002-CAUSAL verification — "because" causal-concept pilot

Date: 2026-11-22. Session: Claude Code on `main`, HEAD `936d9fdd27810e50a144fb6399e647b1ba18c371`. No commit or push.

## Startup

- Git state: the only tracked diffs were the pre-existing `comand.txt` and `schedule/20-9 list`.
- No `A002_CAUSAL_CONCEPT_PILOT` directory existed, so there was nothing to resume.
- No python process was running.
- The A002_ICON_PILOT_20 batch was not rerun.

## Target

- `vocab-000081` (because / なぜなら / bởi vì), confirmed in the A-001 matrix and in row 81 of `data/vocabulary/{en,jp,vn}.txt`.
- `semantic_decisions_v1.json` review_status is `needs_decision`. The usage note says なぜなら is sentence-initial and often paired with から.

## Variants

All queries are exact; there was no Qwen call. V4 was written into `run_causal.py` and `query_variants.csv` before the search ran.

| Variant | Query | Search | Candidates | Downloaded | Notes |
|---|---|---|---|---|---|
| V1 | cause and effect pictogram | SUCCESS | 7 | 5 | V1-02 HTTP 400, V1-06 HTTP 403 |
| V2 | reason and result visual illustration | SUCCESS | 7 | 7 | |
| V3 | cause effect visual sequence illustration | SUCCESS | 7 | 7 | V3-01 = V2-01 URL; reused, no second download |
| V4 | child opening umbrella in the rain illustration | SUCCESS | 6 | 6 | 7 raw results, 6 valid after normalization |

## Checks

| Check | Result |
|---|---|
| Real searches | 4 |
| Candidate records | 27; 25 DOWNLOADED; 24 unique images |
| SHA-256 | 48/48 files (raw + JPEG) match; 0 orphans; 0 missing |
| SigLIP | `google/siglip2-so400m-patch16-384` on CUDA, production `score_batch`. Query scores for all 4 variants. Fixed-text scores ("an illustration in which one event causes another event to happen") for all candidates, the ORIGINAL image and the 7 ICON candidates. |
| Query consistency | `query_variants.csv` matches `retrieval_results.json`; ≤7 candidates per variant |
| Isolation | A-001 matrix and icon-pilot `retrieval_results.json` hashes equal the manifest values. No file under `data/`, `baseline/`, `collect data script/`, `A002_ICON_PILOT_20/` or `phase0_quality_review/` modified after 12:50. |
| Gallery | Served via temporary 127.0.0.1:8766: 6 option cards, 38/38 images loaded, 0 broken, no horizontal overflow, 7 choices plus NOT_REVIEWED. Export produced `HUMAN_REVIEW_DRAFT_NOT_AUTO_APPROVAL` with choice and candidate. The test draft was removed from localStorage and the server stopped. |

## Not established

- Owner choice at retrieval time (later recorded; see the decision section below).
- Rights of the stock sources (watermarks seen: Adobe Stock, alamy, dreamstime, AIDCPR).
- Any generalization to other connectors.

The AI verdict `NO_SUITABLE_VISUAL_FOUND` is preliminary.

## Owner decision (added 2026-11-22)

- Owner chat: "tôi chọn v3-01", recorded as V3_BEST, candidate V3-01 (= V2-01). Image hash re-verified when `owner_review_decision.json` was written.
- The owner reported exporting JSON, but no file was found in Downloads, the project, or `C:/Users/dotha` (depth 5). Cause: the agent's export test had overridden `HTMLAnchorElement.prototype.click` in in-app tab-2, the tab the owner used. The tab's fields still held the agent's test values (TEST_AGENT/V2_BEST) plus the owner's candidate entry V3-01. That stale draft was cleared.
- Lesson: run export tests in a throwaway tab, or reload the tab after the test.
- `comparison.csv` and `experiment_report.md` were re-rendered to show the decision.
