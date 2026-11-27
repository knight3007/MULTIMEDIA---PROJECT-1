# Project map

## Identity and boundaries

Multimedia Project 1 is an academic, non-commercial vocabulary learning project. Implemented: Python preparation/validation pipeline, standalone Excel importer and private Docker packaging. The owner prefers Unity Desktop 2D for Meteor Defense and Flashcard; [GDD v0.1](../game/GDD_v0.1.md) is a draft. Lecturer acceptance of desktop submission and public-URL implications remain open. No game runtime is implemented. The 100-ID dataset is a model benchmark, not the product's vocabulary limit.

| Area | Responsibilities / entry points | Tests or configuration |
|---|---|---|
| Query | `collect data script/query_generator.py`: lazy local Qwen/cache; `prepare_queries` called by image collector | `test_collectors.py`, `test_image_query_benchmark.py` alongside source; `requirements.txt` |
| Image | `imagecollector.py` CLI → DDG/Bing candidates → SigLIP → JPEG/metadata; `image_scorer.py`; `stage_vocabulary_images.py`, `stage_image_replacements.py` isolate runs | `test_collectors.py`, `test_stage_vocabulary_images.py`, `test_stage_image_replacements.py`; `test_ddgs_diagnostics.py` |
| Audio | `audiocollector.py` gTTS MP3; `stage_japanese_audio.py` stable-ID staging | `test_audio_collector.py`, `test_stage_japanese_audio.py`; `requirements-audio.txt`, `.venv-audio/` |
| Identity/data | `vocabulary_registry.py`, `semantic_decisions.py`, `validate_vocabulary.py`; `dataset_builder.py:build_dataset` read-only, CLI writes manifest | `test_vocabulary_validation.py`, `test_dataset_builder.py`, `test_media_review.py`; `media_review.py` |
| Experiments | `image_query_benchmark.py`, `image_retrieval_benchmark.py`, `remote_qwen_client.py`, `remote_qwen_probe.py`, `remote_qwen_v4_benchmark.py` | Corresponding `test_*.py`; remote API docs in `docs/` |
| Kaggle batch | `kaggle_batch/driver.py`, `snapshot.py`, `notebook_runtime.py`, `notebook_template.ipynb` | `kaggle_batch/tests/test_driver.py`; `approved_experiments.json` empty at checkpoint; `.github/workflows/kaggle_qwen3_4b_batch.yml` is experiment draft, not web deployment |
| Product | `game/background/background_idea.md` is the byte-preserved separate background plan; `game/UXUI/` holds the owner's original ZIPs and extracted game-art/font library. `docs/game/GDD_v0.1.md` is a draft; `GAMEPLAY_MECHANICS_SPEC_v0.1.md`, `ASSET_AUDIT.md`, `GAME_ASSET_INVENTORY.md`, `VISUAL_DESIGN_SYSTEM.md`, `UX_UI_SPEC_v0.1.md`, `USER_FLOW_v0.1.md` and `VFX_PLAN.md` are G-002 planning documents. `projectframework.md` retains the earlier Web direction | No Unity project, game runtime or product build/test tooling yet; no public deployment. Asset selection, TMP and performance unverified |
| Docker preparation | Root `Dockerfile`, `compose.yaml`, `.dockerignore`; `collect data script/docker_pipeline.py` calls the existing runner and final gallery, with optional reviewed-image cache | [Docker usage](../DOCKER_PIPELINE.md), [verification](../../reports/DOCKER_001/verification_report.md), `test_docker_pipeline.py`; host mounts keep input/reference data read-only and output/model cache persistent |
| B-001 contracts/fixtures | `docs/contracts/`: workbook, pack and integration contracts; `tests/fixtures/b001/`: five authored XLSX files, synthetic pack and tiny PNG/tone WAV | `tests/fixtures/b001/verify_fixtures.py` checks examples/negative mutations |
| B-002 Excel importer | `collect data script/excel_vocabulary_importer.py`: standalone XLSX validation, preview, accepted private import record and retry; [usage](../B002_EXCEL_IMPORTER.md) | `collect data script/test_excel_vocabulary_importer.py`; [synthetic demo output](../../reports/b002_import_demo/fixture_private_import.json). No runtime pack or AI integration |
| B-003.1 private adapter | `collect data script/import_pipeline_adapter.py`: accepted import mapping → per-import processing plan/evidence under `baseline/imports/<import_id>/`; [boundary guide](../B003_1_IMPORT_PIPELINE_ADAPTER.md) | `collect data script/test_import_pipeline_adapter.py`; [three-item dry run](../../baseline/imports/imp-3e130d77-9848-4f67-b52a-aab79c2512c7/processing_manifest.json). No live processing or runtime pack |

Bare source names above are under `collect data script/` unless a prefix is given. Four-space Python, snake_case functions/modules, PascalCase classes, pathlib paths and UTF-8; no formatter/linter configured. Reuse existing code/stdlib before dependencies.

## Data and evidence locations

- `data/vocabulary/`: EN/JP/VN TXT, stable registry, semantic/review ledgers, `unified_dataset_v1.json` production manifest. Do not rewrite for a documentation task.
- `data/query/`: original query caches. `data/image/en/`, `data/audio/jp/`: production media/metadata, not automatically approved.
- `baseline/media-staging/`: isolated image/audio/query runs; use manifests and exact ID/hash, not filenames alone.
- `reports/full_media_staging_inventory_v1.json`: join of 100 IDs and media evidence. `reports/image_pipeline_audit/20261106T102750Z-cd93f8a1/`: query/image lineage and historical quality observations.
- `reports/image_pipeline_benchmark/`: 25-row A/B experiment and C0 dry-run. `reports/remote_qwen/`: D0 incompatible, D1 V4 prepared; not a successful live 4B benchmark.
- `reports/architecture_reassessment/`: six immutable reports for that study. `reports/phase0_quality_review/`: newer scope/rubric, initial 100-ID review and input hashes.
- `reports/phase0_quality_review/a001_20261122/`: current 100-ID reconstruction/preliminary assessments, owner audio acceptance bound to hashes, local human-review gallery, report builders/checker and contact sheets. Evaluation tools only, not Web Game implementation.
- `docs/agent/`: current context/tasks/checkpoint. Older logs and schedules remain referenced history.

## Verification commands (PowerShell, repository root)

```powershell
git branch --show-current
git rev-parse HEAD
git status --short
.\.venv\Scripts\python.exe -B -m unittest discover -s "collect data script" -p "test_*.py" -q
.\.venv\Scripts\python.exe -B -m unittest discover -s kaggle_batch/tests -p "test_*.py" -q
.\.venv\Scripts\python.exe -B "collect data script\validate_vocabulary.py"
git diff --check
```

Choose checks relevant to the change. Tests use mocks; they do not establish live inference/media quality. Do not run builder CLI as a read-only check: it writes production JSON. Use `build_dataset(root)` in memory only when needed. Root `test_qwen.py`/`test_ddg.py` are live diagnostics, not default offline tests. Initial setup used existing environments; no dependency installation is authorized by a documentation checkpoint.
- `game/New Unity Project/Assets/Scripts/Game/` (G-006 Meteor Defense): pure rules `GameConfig`, `VocabularyDeck`, `AnswerChecker`, `TargetSelector`, `LaneChooser`, `MeteorDefenseSession` (tests `Tests/EditMode/GameLogicTests.cs`); scene side `MeteorDefenseController`, `MeteorView`, `GameEntry` (tests `Tests/PlayMode/MeteorDefenseFlowTests.cs`). `Scripts/Content/PackAudience.cs` marks developer fixtures (D-036). `Scripts/Dev/MeteorDefenseDevBot.cs` is verification-only (`-g006Bot`). Scenes come from `Assets/Editor/G003Builder.cs`.
- G-007 additions in `Scripts/Game/`: `BlankPuzzle`, `GameCompatibility`, `SpawnLayout`, `GameSetupController` (scene GameSetup), presets in `GameConfig`, targeting modes in `TargetSelector`; tests `Tests/EditMode/G007LogicTests.cs`, `Tests/PlayMode/GameConfigFlowTests.cs`. `Assets/Editor/BatchBuild.cs` gives headless `RebuildScenes` / `Windows` entry points. Dev switches `-g007Difficulty -g007Hint -g007Answer -g007Target -g007Hold`.
- G-007-R2/R3 and G-008 in `Scripts/Game/`: `TypingCombat` (per-character combat, tests `TypingCombatTests`, `TypingCombatFlowTests`), `VocabularyDeck` deck cycles (`VocabularyDeckTests` in `GameLogicTests`), `SpeechSlot` and `LearningHistory` (`G008AudioHistoryTests`), session waves, combo and records (`G008SessionTests`), flow (`G008FlowTests`). Headless runner `game/New Unity Project/Tools/headless.ps1`.
- `collect data script/promote_reviewed_pack.py` (G-004-R1): owner review form and needs_review to ready/failed promotion into a new pack folder; tests `test_promote_reviewed_pack.py`.
