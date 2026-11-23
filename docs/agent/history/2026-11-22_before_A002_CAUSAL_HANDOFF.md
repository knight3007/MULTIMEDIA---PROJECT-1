# Latest handoff — A-002-PILOT icon search (20 IDs)

Updated 2026-11-22T12:45+07:00 by the Claude Code session that took over from Codex root. Repo `D:/MULTIMEDIA - PROJECT 1`, branch `main`, HEAD `936d9fdd27810e50a144fb6399e647b1ba18c371`.

- **Status**: A-002-PILOT is NEEDS_REVIEW. The automated stages are done and the human A/B review is pending.
- **Write claims**: none active.
- **Previous handoff**: archived as `history/2026-11-22_before_A002_PILOT_HANDOFF.md`.
- **Repository**: no commit or push. Tracked diffs are still only the pre-existing `comand.txt` and `schedule/20-9 list`.

## What happened

- On takeover, the previous agent's `run_pilot.py` was still running (15/20 IDs done). This session waited for it to exit and confirmed that no further writes followed. It did not rerun or duplicate any search or download.
- Selection: 20 A-001 image-learning-FAIL IDs.
  - Time words: today, tomorrow, yesterday, always.
  - Action verbs: go, write, study, work, sleep, drink, understand, remember, swim.
  - Abstract words: easy, difficult, experience, important, different, because.
  - Weather: rain.
  - No simple concrete nouns. The production query strategy is unchanged.
- Query: exactly `<english> icon`, with no Qwen call.
- Results:
  - 20/20 real DDG searches succeeded.
  - 129/130 candidates downloaded (`vocab-000078-07` failed with HTTP 403).
  - SigLIP2-so400m scored all 20 items.
  - All hashes verified.
- Deviations from production: timeout 12 s vs 20 s; search/download retries 1/0 vs 2/2; searched on a different date. The baseline candidate pools were not retained, so baseline A has only its single chosen image.
- New this session:
  - `automated_visual_observations.md`. These are AI-preliminary notes.
    - B often gives a clearer pictogram: swim, rain, sleep, write.
    - Several B images contain the English word (today, easy, always, go), and tomorrow and yesterday use near-identical icons.
    - Several B images have ICON-ICONS or depositphotos watermarks.
    - drink's B is a cocktail glass.
  - The report now lists deviations, a per-ID table and failures.
  - `render_pilot.py` was extended. Rerunning it regenerates `comparison.csv`, the gallery and the report deterministically.
- Verification: [record](history/2026-11-22_A002_PILOT_verification.md). Collector tests: 160 OK. Vocabulary validation: 0 structural issues. No file under `data/`, `baseline/` or `collect data script/` changed.

## Next action

The owner opens `reports/image_pipeline_experiments/A002_ICON_PILOT_20/review_gallery.html` and picks one label per ID: ORIGINAL_BETTER, ICON_BETTER, BOTH_GOOD, BOTH_BAD or NEEDS_REVIEW. They enter their reviewer name and use Export JSON.

A later, separately authorized task validates that export (20 IDs, hashes, reviewer) and only then considers a query-strategy recommendation, scoped to hard words.

Do not expand to 100 IDs, change the production pipeline, start A-003 or B-002, or design any game UX/UI.
