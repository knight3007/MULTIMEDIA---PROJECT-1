# Latest handoff — A-003.1 ranking diagnosis

Updated 2026-11-23 (Asia/Saigon) by Codex root. Repo `D:/MULTIMEDIA - PROJECT 1`, branch `main`, HEAD `936d9fdd27810e50a144fb6399e647b1ba18c371`. No commit or push. No active write claim. Prior handoff archived at [2026-11-23_before_A003_1_HANDOFF.md](history/2026-11-23_before_A003_1_HANDOFF.md).

## Status and outputs

- **A-003.1 DONE for the diagnostic scope.** [Ranking diagnosis](../../reports/image_pipeline_experiments/A003_RANKING_DIAGNOSIS/ranking_diagnosis.md), [recommended fixes](../../reports/image_pipeline_experiments/A003_RANKING_DIAGNOSIS/recommended_fixes.md), `owner_feedback.json`, `candidate_diagnosis.csv`, `scoring_comparison.csv`, two reproducibility scripts and seven visual contact sheets are under `reports/image_pipeline_experiments/A003_RANKING_DIAGNOSIS/`. [Verification](history/2026-11-23_A003_1_verification.md).
- **A-003 remains NEEDS_REVIEW.** Seven owner chat statements are preserved as `OWNER_CHAT_FEEDBACK`, with explicit selected-pair preferences only for hungry, buy, eat and sometimes. Receive, book and house report issues but no A/B winner. Five other A-003 items remain unreviewed. No 12-item gallery export is claimed.
- 89 candidate records were inspected; 82 downloaded candidates passed path/hash checks and were scored offline with frozen shared-meaning descriptions. Historical query top-1 is visually suitable in 4/14 arms; shared-meaning top-1 in 6/14 arms by a single analyst's desk labels. Shared meaning is helpful in some cases but still fails house, buy and sometimes. No production integration.
- The original A-003 gallery is pre-FIX-001; the separate [alpha recheck](../../reports/image_pipeline_experiments/ALPHA_FIX_RECHECK/README.md) shows corrected transparent images. FIX-001 code and tests remain uncommitted and unchanged by A-003.1. `because` V3-01 stays internal-only via `data/vocabulary/internal_image_overrides_v1.json` (D-015/D-016).

## Git reconciliation

The previous handoff's claim that only `comand.txt` and `schedule/20-9 list` had tracked diffs was stale. Current `git status --short` lists tracked modifications to `collect data script/image_scorer.py`, `collect data script/imagecollector.py`, `collect data script/test_collectors.py` (authorized FIX-001), `comand.txt`, `schedule/20-9 list`, and `data/vocabulary/unified_dataset_v1.json`. The dataset has **no content diff** (`git diff --quiet` returned 0) and retains SHA-256 `644c2dc9899077dad15d2e2916d7dc3d1cef49ecd151ea406115bb3da19481bd`. Numerous pre-existing untracked files/directories include AGENTS.md, docs/agent, reports/ and Kaggle artifacts; A-003.1 adds its report directory and history notes. No unexpected production-data diff was found. Recheck Git on takeover.

## Verification and next action

Collector regression suite **162 OK**, Kaggle suite **19 OK**, vocabulary validator **100 physical rows / 0 structural issues**. `git diff --check` clean. All 82 A-003 downloaded raw/JPEG candidate hashes match source records; old A-003 results and canonical dataset content were preserved. These checks do not certify image rights or educational suitability.

Next: owner reviews unresolved A-003 items and candidate alternatives, then decides whether to revise conditional search. Potential later work is per-item query repair, rejection/no-image handling and human selection of lower candidates; these are recommendations only. No new retrieval, production ranking change, B-002, Game UX/UI design, deployment, commit or push is authorized by this diagnostic. Game UX/UI remains **UNDECIDED**.
