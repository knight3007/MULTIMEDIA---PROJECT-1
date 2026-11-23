# Latest handoff — Image pipeline v2 frozen

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

## Freeze (D-021)

The owner chose "Chốt như hiện tại": image pipeline v2 is **FROZEN as is**.
- `freeze_manifest.json` status is FROZEN with the known limitations listed; the frozen prompt SHA equals the one validated in iteration 3.
- `test_image_pipeline_v2.FreezeTests` fails if the policy, runner, imagecollector, image_scorer, query_generator or approved registry changes.
- The freeze commit is pushed to origin/main.

## Next action

No active task. Possible next steps, each needing owner instruction:
- B-003.2: run Excel imports through `image_pipeline_v2.process_item`, with a review UI or export.
- Rights review for a public release subset.
- Game UX/UI (D-014).

To change pipeline v2, record a new decision and a new `POLICY_VERSION`, then update `freeze_manifest.json`.
