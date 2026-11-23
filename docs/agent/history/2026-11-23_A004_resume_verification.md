# A-004 resumed benchmark verification — 2026-11-23

Task resumed from the 10-ID image checkpoint; no Qwen output, valid prior candidate or successful prior SigLIP rank was rerun. Branch `main`, HEAD `936d9fdd27810e50a144fb6399e647b1ba18c371`. The previous approval-credit block did not recur: one 10-ID resource-gate batch completed, then eight remaining 10-ID batches completed using the frozen runner. No paid API, account switch, new model download or production change.

## Frozen inputs and execution

- Dataset SHA-256 `644c2dc9899077dad15d2e2916d7dc3d1cef49ecd151ea406115bb3da19481bd`; frozen vocabulary SHA-256 `123381049a47bc59b42b9fb677f3e80ed640c64c0006a96d62193999adf75ff5`. Runner/source hashes matched the manifest.
- Qwen `Qwen/Qwen3-1.7B` snapshot revision `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`: 100 existing attempts, 93 SUCCESS, six FAILED (`vocab-000051`, `000052`, `000057`, `000060`, `000064`, `000065`) and one `BLOCKED_SEMANTIC_DECISION` (`vocab-000038`). No new Qwen call.
- DuckDuckGo `ddgs`, backend auto, `wt-wt`, moderate safe search, seven candidates maximum, one query per eligible ID, 20-second timeout, zero configured retries. Frozen SigLIP `google/siglip2-so400m-patch16-384` revision `dd658faac399427308559e2c3ac1e99cbe43845d`, CUDA float16, one ranking pass per valid set. FIX-001 white alpha preprocessing remained unchanged. Ten image batches of ten IDs are recorded in the manifest, with per-ID atomic ledgers.
- Final image states: 100/100 represented; 93 real search attempts and 93 successful search calls; 620 candidate records, 548 successful raw/JPEG pairs, 72 failed downloads; 92 ranked IDs, seven `SKIPPED_QUERY`, one `NO_VALID_CANDIDATES` (vocab-000008 water, sole candidate HTTP 404). No other processing failure. The ID008 URL failure is preserved; no unjustified retry.

## Verification

- `finalize_a004.py` checked all 548 raw and JPEG file SHA-256 values, decoded/verified image formats, score/rank consistency, unique 100 IDs, ten distinct image batches, frozen dataset/vocabulary/source/runner hashes, 99 available A-001 image hashes and 100/100 existing audio hashes. No audio regenerated.
- `evaluation_matrix.csv` has 100 IDs. All 92 ranked top images have AI_PRELIMINARY assessments; image semantic relevance 48 PASS / 23 NEEDS_REVIEW / 21 FAIL; educational suitability 30 PASS / 13 NEEDS_REVIEW / 49 FAIL. The other eight have no new image to assess. AI_PRELIMINARY query desk review: 48 PASS / 23 NEEDS_REVIEW / 22 FAIL / seven blocked. Comparisons with A-001: ten improved / 74 unchanged / eight degraded / eight not comparable. All such quality labels are analyst judgments, not human approval.
- Gallery: `render_gallery.py` produced 100 cards, valid alternatives, candidate rank and score, status, notes, labels and `NO_SUITABLE_IMAGE` choice. Static check found 739 image tags with zero unresolved local paths. In a live localhost browser, all 100 cards rendered, first image loaded, search/filter narrowed to vocab-000008, reset to 100/100, and JSON export downloaded a 100-review draft with `NO_SUITABLE_IMAGE`. Console errors/warnings: zero. The test draft was deleted and the test form reset; no owner decision was recorded.
- Offline regression: `unittest discover -s "collect data script" -p "test_*.py" -q` **174 OK**; `unittest discover -s kaggle_batch/tests -p "test_*.py" -q` **19 OK**. `validate_vocabulary.py`: 100 physical rows, zero structural issues. `git diff --quiet -- data/vocabulary/unified_dataset_v1.json`: exit 0; `git diff --check`: exit 0 with pre-existing LF/CRLF warnings. No commit/push.

## Artifact hashes

| File under `reports/image_pipeline_experiments/A004_FULL_100_RERUN/` | SHA-256 |
|---|---|
| `experiment_manifest.json` | `268a0baf9e965e04b78d3d9e448e050272fcc8c2ef2ba4b9b55c46c6e7b1ba58` |
| `query_results.json` | `60fbd529c4da3948e588085c1643688439c060d9b27203f3474db95731b7b596` |
| `retrieval_results.json` | `028b186818b34f6133380a267c63a554be217b5f565475746b9835f7eb7966c8` |
| `candidate_rankings.csv` | `86ce5acd6da9347155b5544a72304fe336c9d57274e109bd8cf56762297b5ffd` |
| `evaluation_matrix.csv` | `e55a2b2065d3c190fb0c1c20ffe0243f21f52f9b9140a608ae475294b7959c9c` |
| `review_gallery.html` | `fa6685c9c75c5bc09f53f00198a142338b133dffda3cb17f27b57fa81212fd07` |

Owner next reviews the internal gallery and exports JSON. `NO_SUITABLE_IMAGE` in the A-003.3 sometimes decision and the D-015/D-016 because internal-only override remain separately recorded. No A-004 image was promoted or rights-cleared. B-003.2 and Game UX/UI remain paused/undecided.
