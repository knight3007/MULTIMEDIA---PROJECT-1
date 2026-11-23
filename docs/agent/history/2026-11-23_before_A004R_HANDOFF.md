# Latest handoff — A-004 resumed benchmark

Updated 2026-11-23 (Asia/Saigon) by Codex root. Repo `D:/MULTIMEDIA - PROJECT 1`, branch `main`, HEAD `936d9fdd27810e50a144fb6399e647b1ba18c371`. No active write claim, commit or push. Previous partial-run handoff: [archive](history/2026-11-23_before_A004_resume_HANDOFF.md).

## Result

- **A-004 DONE for all eligible automated image attempts and review package; owner decisions pending.** The newly authorized continuation used the frozen 10-ID checkpoint, a successful first resource-gate batch, then eight more batches. Qwen was not rerun; successful old downloads and SigLIP ranks were not repeated. The prior credit block remains historical evidence.
- Frozen dataset 100/100 IDs, SHA-256 `644c2dc9899077dad15d2e2916d7dc3d1cef49ecd151ea406115bb3da19481bd`. Original Qwen: 93 effective intents, six invalid outputs and one blocked semantic intent. Image states: 93 real searches, 620 candidate records, 548 valid raw/JPEG pairs, 72 failed downloads, 92 SigLIP rankings, seven skipped queries and one no-valid-candidate ID (vocab-000008, HTTP 404). Existing audio references hash-match 100/100; no audio generated.
- [Report](../../reports/image_pipeline_experiments/A004_FULL_100_RERUN/evaluation_report.md), [manifest](../../reports/image_pipeline_experiments/A004_FULL_100_RERUN/experiment_manifest.json), [100-ID matrix](../../reports/image_pipeline_experiments/A004_FULL_100_RERUN/evaluation_matrix.csv), [gallery](../../reports/image_pipeline_experiments/A004_FULL_100_RERUN/review_gallery.html), [review instructions](../../reports/image_pipeline_experiments/A004_FULL_100_RERUN/review_instructions.md), [verification](history/2026-11-23_A004_resume_verification.md). AI_PRELIMINARY top-image educational suitability: 30 PASS / 13 NEEDS_REVIEW / 49 FAIL; eight no new image. Query desk review: 48 PASS / 23 NEEDS_REVIEW / 22 FAIL / seven blocked. No human labels yet.
- Verification: all 548 raw/JPEG pairs and hashes, score/rank associations and 100 unique states checked; gallery 100 cards, 739 local image references resolving, live filter and 100-item JSON export tested. Collector 174 tests OK, Kaggle 19 OK, vocabulary validation 100 rows/zero structural issues, dataset content unchanged and `git diff --check` exit 0. No production promotion or public-rights approval.

## Existing work and next action

B-003.1 offline adapter remains DONE; B-003.2 is paused. A-003.3 remains DONE for six owner-approved quality selections and one `NO_SUITABLE_IMAGE`; five other A-003 holdout items remain unreviewed. The D-015/D-016 `because` image stays internal-only. Game UX/UI is UNDECIDED. Pre-existing uncommitted modifications and untracked artifacts remain; do not overwrite them.

Stop here. The owner can review the internal gallery and export JSON for a separately scoped decision-consolidation task. The seven query-blocked IDs are in `query_remediation.json`; no Qwen repair or prompt change was authorized. Do not begin B-003.2, Game UX/UI, production promotion, commit or push automatically.
