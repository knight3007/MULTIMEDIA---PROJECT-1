# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Read first

[AGENTS.md](AGENTS.md) holds the binding repo rules: context-handoff protocol, data safety and the commit policy. Follow it. In short:

- Start from [docs/agent/INDEX.md](docs/agent/INDEX.md), then `STATE.md`, `TASKS.md` and `HANDOFF.md`. Compare branch, HEAD and `git status --short` with the recorded checkpoint before you trust it.
- `docs/agent/TASKS.md` is the live task list. `DECISIONS.md` records each decision as CONFIRMED, PROPOSED, BLOCKED or UNKNOWN. Older files (`PROJECT_CONTEXT.md`, `CODEX_PROGRESS.md`, `tasks/`, `progress.md`, `schedule/`) are historical and not current instructions.
- Task gates are strict. Run no inference, media download/generation, web/game implementation, deployment, commit or push unless the user's current instruction authorizes it.
- At task/phase/handoff boundaries, sync STATE, TASKS and HANDOFF (task ID and status, changed files, verification actually run, next action). Move replaced checkpoints and decisions to `docs/agent/history/`.

## What this repo is

This is an academic vocabulary-learning project. The confirmed target is an offline-first Web Game with Excel import and a public URL due 2026-12-02. **Only the Python data-preparation pipeline exists.** `web/` and `game/` are placeholders, and the repo has no frontend build or dev server. Final game UX/UI is explicitly undecided (D-014). The 100-word dataset is a model benchmark, not the product's vocabulary cap.

## Commands (PowerShell, repo root)

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s "collect data script" -p "test_*.py" -q
.\.venv\Scripts\python.exe -B -m unittest discover -s kaggle_batch/tests -p "test_*.py" -q
.\.venv\Scripts\python.exe -B "collect data script\validate_vocabulary.py"
git diff --check
```

- Single test file or case: tests import sibling modules by bare name (`import imagecollector`), so run them through discovery on that directory, for example `... -m unittest discover -s "collect data script" -p "test_collectors.py" -k test_audio_import_is_independent`.
- `kaggle_batch` tests import the package from the repo root (`python -m kaggle_batch.driver ...`).
- Audio work uses `requirements-audio.txt` and a separate `.venv-audio/`.
- `dataset_builder.py` run as a CLI **writes** `data/vocabulary/unified_dataset_v1.json` (the production manifest), so don't run it as a check. For a read-only check, call `build_dataset(root)` in memory.
- Root `test_qwen.py` and `test_ddg.py` are live network/model diagnostics, not part of the offline suite. The offline suites mock all external services and do not prove live inference or media quality.
- No formatter, linter or coverage threshold is configured.

## Architecture

All pipeline code lives in `collect data script/` (the folder name contains spaces, so always quote it). [docs/agent/PROJECT_MAP.md](docs/agent/PROJECT_MAP.md) maps modules to their tests.

- **Source vocabulary** is three line-aligned files, `data/vocabulary/{en,jp,vn}.txt`. A row's stable identity is a `vocab-NNNNNN` ID from `id_registry_v1.json`, managed by `vocabulary_registry.py`. Never renumber IDs or key anything on row position or filename alone.
- **Query generation**: `query_generator.py` lazily loads a local Qwen model and caches results under `data/query/`. `semantic_decisions.py` applies human overrides from `semantic_decisions_v1.json`, so the effective query can differ from the model's output.
- **Image collection**: `imagecollector.py` gets queries via `prepare_queries`, fetches DDG/Bing candidates, ranks them with a SigLIP scorer (`image_scorer.py`), and writes a JPEG plus metadata to `data/image/en/`.
- **Audio collection**: `audiocollector.py` produces gTTS MP3s in `data/audio/jp/`. It must stay importable without torch, PIL or the image modules, and a test enforces that.
- `collector_common.py` provides the shared CLI arguments, vocabulary loading, `CollectionError` and project-root path resolution.
- **Staging**: the `stage_*.py` scripts write isolated runs to `baseline/media-staging/` with manifests. They are matched by ID and hash, never by filename.
- **Review and promotion**: `media_review.py` validates `image_media_reviews_v1.json` with separate license, suitability and owner statuses. `promotion_eligible` requires all three. A media file existing never means it is approved.
- **Dataset build**: `validate_vocabulary.py` checks the source data, registry and decisions. `dataset_builder.py` joins vocabulary, IDs and approved media into `unified_dataset_v1.json` according to [docs/DATA_CONTRACT_V1.md](docs/DATA_CONTRACT_V1.md).
- **Experiments**: `image_query_benchmark.py`, `image_retrieval_benchmark.py` and `remote_qwen_*.py` are evaluation tooling. The remote Qwen API is documented in `docs/REMOTE_QWEN_API_V*.md`, and results go in `reports/`.
- **Kaggle batch** (`kaggle_batch/`): `driver.py` handles approval, gating and stepping. It is driven by the draft workflow `.github/workflows/kaggle_qwen3_4b_batch.yml` and refuses to run unless the experiment is listed in `approved_experiments.json` against a pinned commit. Live GPU gates are closed.
- **Track B contracts** (proposed, not implemented): the Excel workbook and content-pack specs are in `docs/contracts/`, with fixtures in `tests/fixtures/b001/` (check them with `verify_fixtures.py`).

## Conventions

- Use four-space indentation, snake_case modules and functions, PascalCase classes and UPPER_SNAKE constants. Use `pathlib.Path` for paths and write all text as UTF-8. Prefer the standard library over new dependencies.
- Put tests next to the code as `test_*.py` (or in `kaggle_batch/tests/`). Mock network and model calls, and use temporary directories for filesystem tests.
- Don't rewrite `data/vocabulary/` files, production media or existing `reports/` evidence as a side effect of other work.
