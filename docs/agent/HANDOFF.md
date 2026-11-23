# Latest handoff — PIPELINE-V2 candidate

Updated 2026-11-23T22:00+07:00 by the Claude Code session. Repo `D:/MULTIMEDIA - PROJECT 1`, branch `main`.

- **Write claims**: none active.
- **Repository**: code and docs pushed to `origin/main` at the owner's request. Experiment media stays local.
- **Previous handoff**: archived as `history/2026-11-23_before_PIPELINE_V2_HANDOFF.md`.

## Done

- **A-004R-FU is DONE.** The owner review JSON was validated, and the final 100/100 selection is in `reports/image_pipeline_experiments/A004R_FINAL_SELECTION/`. The registry `data/vocabulary/approved_images_v1.json` is not promoted, rights are unknown, and `because` is internal-only.
- **PIPELINE-V2 candidate:**
  - Policy and runner: `collect data script/visual_query_policy.py` and `image_pipeline_v2.py`.
  - Spec: `docs/IMAGE_PIPELINE_V2.md`. Decision: D-020 PROPOSED.
  - Validation iteration 3: PHOTO 44/44, NON_PHOTO 34/35, CURATE 1/1, valid 99/100 → **NOT PASSED**; budget used.
  - Known example-copying and wrong-sense queries are listed in `validation_report.md`.
- **Verification:** [record](history/2026-11-23_PIPELINE_V2_verification.md).

## Next action

The owner decides:

- (a) Freeze v2 as is; invalid or weak queries reach the reviewer as `needs_review` or a failure.
- (b) Authorise further prompt work: for example removing the copied scenes, tolerating `TYPE` noise such as "RAIN ABSTRACT", or a fallback to the v1 query when classification fails.

Wiring v2 into Excel imports (B-003.2), public release and Game UX/UI each need separate instruction.
