# Latest handoff — A-003.2 selective image repair

Updated 2026-11-23 (Asia/Saigon) by Codex root. Repo `D:/MULTIMEDIA - PROJECT 1`, branch `main`, HEAD `936d9fdd27810e50a144fb6399e647b1ba18c371`. No commit/push and no active write claim. Previous handoff archived at [2026-11-23_before_A003_2_HANDOFF.md](history/2026-11-23_before_A003_2_HANDOFF.md).

## Status

- **A-003.2 NEEDS_REVIEW**: [repair report](../../reports/image_pipeline_experiments/A003_SELECTIVE_REPAIR/repair_report.md), [seven-item review gallery](../../reports/image_pipeline_experiments/A003_SELECTIVE_REPAIR/review_gallery.html), manifest, retrieval ledger and proposals are complete, but no owner approval/export was received. [Verification](history/2026-11-23_A003_2_verification.md).
- Hungry `ICON-01` and eat `NORMAL-06` preserve owner A/B preferences; receive `ICON-07`, buy `ICON-01`, house `NORMAL-05`, book `ICON-03` are proposals for owner choice. Sometimes proposes `NO_SUITABLE_IMAGE`. No asset was promoted. The five other original A-003 items still await human review.
- Only sometimes triggered new retrieval. Book already had a clear open-book icon, so book made 0 new requests. Two exact sometimes queries were frozen before search; both eventually succeeded. New result: 14 candidates, 13 valid downloaded JPEGs, 1 failure. No clear occasional-frequency image was found. Initial sandbox searches timed out; retry used the same queries with network access. No new model download or SigLIP experiment.
- A-003.1 remains DONE for diagnostic scope; A-003 parent remains NEEDS_REVIEW. Historical A-003 gallery is pre-FIX-001. FIX-001 is preserved. D-015/D-016 `because` V3-01 stays internal-only via `data/vocabulary/internal_image_overrides_v1.json`; no public rights are inferred. Game UX/UI remains **UNDECIDED**.

## Verification and Git

- Seven proposals all have `OWNER_REVIEW_PENDING`; all proposed/current/baseline paths and hashes validate. All 13 new raw/JPEG pairs validate against the retrieval ledger. Manifest pins exact source hashes and HEAD. Canonical dataset SHA-256 remains `644c2dc9899077dad15d2e2916d7dc3d1cef49ecd151ea406115bb3da19481bd`; `git diff --quiet` returned 0.
- Collector offline suite exit 0; Kaggle **19 OK**; vocabulary **100 physical rows / 0 structural issues**; `git diff --check` clean. Static gallery checks: seven cards, 27 resolving local images, seven choice controls and note fields; export script parses. **Browser runtime not verified** because the browser tool rejected `file://` under its protocol policy and prohibited workarounds. The user can open the HTML locally and export the decision JSON.
- Tracked `git status --short` modifications are still the pre-existing FIX-001 files (`collect data script/image_scorer.py`, `imagecollector.py`, `test_collectors.py`), `comand.txt`, `schedule/20-9 list`, and a status-only `data/vocabulary/unified_dataset_v1.json` entry with identical content. Many pre-existing untracked experiment/context files remain. A-003.2 adds only its isolated report directory and this checkpoint/history. Recheck Git on takeover.

## Next action

Owner opens the [A-003.2 gallery](../../reports/image_pipeline_experiments/A003_SELECTIVE_REPAIR/review_gallery.html), decides on the four replacement candidates and sometimes no-image outcome, confirms or revises hungry/eat, adds notes and exports `A003-selective-repair-review.json`. A later scoped task validates that export against IDs/hashes and rights before any promotion or production query change. Do not start B-002, Game UX/UI, general SigLIP work, or commit/push automatically.
