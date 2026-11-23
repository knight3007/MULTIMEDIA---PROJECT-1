# Latest handoff — A-003 conditional image search

Updated 2026-11-22T14:15+07:00 by the Claude Code session. Repo `D:/MULTIMEDIA - PROJECT 1`, branch `main`, HEAD `936d9fdd27810e50a144fb6399e647b1ba18c371`.

- **Status**: A-003 is NEEDS_REVIEW (automated stages done, human review 0/12).
- **Write claims**: none active.
- **Previous handoff**: archived as `history/2026-11-22_before_A003_HANDOFF.md`.
- **Repository**: no commit or push.
- **Git**: tracked diffs are only `comand.txt` and `schedule/20-9 list`. `unified_dataset_v1.json` may show as modified because of cached timestamps, but its content is identical (`git diff --quiet` exits 0; SHA-256 `644c2dc9…`).

## Earlier in this session

- The owner asked to put "because" V3-01 into the dataset. A rebuild changed the dataset hash that historical manifests pin, so it was reverted.
- Per the owner's choice (D-016), the image is recorded in `data/vocabulary/internal_image_overrides_v1.json`: INTERNAL_ONLY, licence unknown, not read by the builder.

## A-003 results

- **Sample**: 12 IDs frozen before retrieval.
  - Concrete: apple, cat, mountain, house, car, book.
  - Action: eat, buy, receive.
  - Abstract: happy, hungry, sometimes.
- **Arms**: NORMAL (cached Qwen query) vs ICON (`<english> icon`), with identical production-default settings.
- **Technical**:
  - Searches: 24/24 succeeded. Downloads: NORMAL 74/81, ICON 73/77. SigLIP ranked 24/24.
  - Transparency defect: ICON had 29 transparent candidates, 8 of them black squares (6/7 for car). In the earlier pilot, 10/20 selected icons were flattened.
- **AI preliminary**:
  - Icon was better for house and book (the normal queries drift in sense), buy and hungry.
  - Icon was worse for car (watermark and black squares) and eat (it returned a musician).
  - Both were good for apple (but the icon pool is full of Apple logos), cat, mountain and happy.
  - Both were bad for receive (ranking miss; the icon pool was good) and sometimes.
  - Conclusion: a mixed result, not a general win. SigLIP is unreliable here.
- **Report**: `evaluation_report.md` answers the 8 decision-gate questions, proposes `NO_SUITABLE_IMAGE` rejection criteria with a fallback order, and gives a category strategy. Recommendation: **revise before integrating**.
- **Verification**: [record](history/2026-11-22_A003_verification.md). Collector tests 160 OK, kaggle_batch 19 OK, vocabulary validation 0 issues.

## FIX-001 (D-017), done after A-003

- Owner approved the black-background fix. `flatten_to_rgb` in `image_scorer.py` composites transparency onto white and is used by `score_batch` and `imagecollector.normalize_image_to_jpeg`. Two regression tests were added to `test_collectors.py`.
- Collector suite 162 OK; kaggle_batch 19 OK; vocabulary validation 0 issues. Uncommitted.
- Offline re-check with no network, in `reports/image_pipeline_experiments/ALPHA_FIX_RECHECK/`:
  - Black squares went 8→0 (A-003) and 4→0 (pilot); car icons are now usable.
  - SigLIP picks changed for cat, mountain, buy and happy (A-003) and for easy and work (pilot). They are not uniformly better (work: collage; happy: watermark).
- The A-003 and pilot galleries still show pre-fix images as historical evidence.

## Next action

The owner reviews the 12 A-003 pairs (`reports/image_pipeline_experiments/A003_CONDITIONAL_SEARCH/review_gallery.html`) and exports JSON. ALPHA_FIX_RECHECK shows the fixed versions of the affected icons.

Then the owner decides whether to integrate or revise conditional search. Possible next development steps, which need instruction:

- A `NO_SUITABLE_IMAGE` outcome with rejection rules.
- A dual pool + human pick for flagged words.
- Detection of baked-in checkerboard images.

Do not integrate conditional search, start B-002 or design Game UX/UI without instruction.
