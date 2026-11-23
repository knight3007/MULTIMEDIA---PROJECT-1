# A-002-PILOT verification — icon search on 20 items

Date: 2026-11-22. Repo `D:/MULTIMEDIA - PROJECT 1`, branch `main`, HEAD `936d9fdd27810e50a144fb6399e647b1ba18c371`. No commit or push.

## Takeover reconstruction

- The checkpoint showed A-002-PILOT as IN_PROGRESS under a previous Codex root session. On takeover (12:28 +07), `run_pilot.py` was still running: PID 22180/18360, started 12:19:44 by the Codex app, with 15/20 IDs written.
- The Claude Code session did not write to the experiment directory while that process ran. It waited for the process to exit (12:32:51), then watched for 2 more minutes for further writes (none appeared) before taking over the write scope.
- Retrieval was not rerun. No search or download was duplicated. All retrieval numbers below come from the previous agent's single run.

## Evidence

| Check | Result |
|---|---|
| Unique benchmark IDs | 20/20 unique, same order in manifest, `selected_vocabulary.csv` and `retrieval_results.json` |
| Selection criteria | All 20 have A-001 image learning = FAIL (asserted in `run_pilot.py`). Covers time (today, tomorrow, yesterday, always), action verbs (go, write, study, work, sleep, drink, understand, remember, swim), abstract words (easy, difficult, experience, important, different, because) and weather (rain). Includes the examples swim, go, today and tomorrow. No simple concrete nouns. |
| Query transformation | Every query equals `english + " icon"`. No Qwen call. |
| Search | 20/20 SUCCESS through `imagecollector.search_images` (DDG `wt-wt`, moderate safesearch, 7 results each). 0 failures and 0 rate limits recorded. 20 real searches. |
| Downloads | 130 candidate records, 129 DOWNLOADED, 1 failed (`vocab-000078-07`, HTTP 403). |
| Hashes | All 258 recorded files (129 raw `.img` + 129 `.jpg`) exist and match SHA-256. 0 orphan files on disk. |
| Baseline A | 20/20 baseline staging images exist and match the recorded SHA-256. |
| SigLIP | 20/20 SCORED with `google/siglip2-so400m-patch16-384`, scored against the icon query. Selection is the top score. |
| Production untouched | No file under `data/`, `baseline/` or `collect data script/` modified after 12:00 on 2026-11-22. No tracked diff under `data/`. |
| Gallery | Served over a temporary 127.0.0.1 server: 20 cards, 169/169 images loaded (20 A + 20 B + 129 candidates), 0 broken. 5 review labels plus NOT_REVIEWED, 20 note fields. JSON export produced a `HUMAN_REVIEW_DRAFT_NOT_AUTO_APPROVAL` file with 20 meta items. The test draft was removed from localStorage afterwards. |
| Tests | `unittest discover -s "collect data script"`: Ran 160, OK. `validate_vocabulary.py`: 100 rows, 0 structural issues. |

## Recorded deviations from production defaults

- Timeout 12 s vs 20 s; search retries 1 vs 2; download retries 0 vs 2.
- All candidates are kept under the experiment directory.
- Searches ran on a different date than the baseline, and the baseline candidate pools were not retained.

## Not established

- Human A/B preference: 0/20.
- Rights and licences of icon sources.
- Effect on simple nouns.
- Statistical significance.

AI visual notes: `reports/image_pipeline_experiments/A002_ICON_PILOT_20/automated_visual_observations.md` (preliminary only).
