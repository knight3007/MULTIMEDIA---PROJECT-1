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

## Next action

The owner opens `reports/image_pipeline_experiments/A003_CONDITIONAL_SEARCH/review_gallery.html`, labels the 12 pairs (with NO_SUITABLE_IMAGE per arm if needed), enters a reviewer name and uses Export JSON. The file goes to the browser's Downloads folder.

Then the owner decides:

- Approve the transparency fix as the next development task (smallest, clear defect).
- Whether to pursue the dual-pool + human pick approach for flagged words.

Do not integrate, start B-002 or design Game UX/UI without instruction.
