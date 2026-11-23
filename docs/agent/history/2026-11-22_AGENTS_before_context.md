# Repository Guidelines

## Project Structure & Module Organization

This repository prepares vocabulary and media for a planned web learning game. The working Python pipeline lives in `collect data script/`: collectors, query generation, validation, dataset building, and adjacent `test_*.py` files. `kaggle_batch/` contains the batch runner and its `tests/`. Source vocabulary and review decisions live in `data/vocabulary/`; collected images, audio, and query data live under `data/`. Use `docs/` for contracts and architecture notes, `reports/` for experiment results, and `tasks/` for work plans. `web/` and `game/` are placeholders, not runnable applications.

## Build, Test, and Development Commands

Run these from the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s "collect data script" -p "test_*.py"
.\.venv\Scripts\python.exe -m unittest discover -s kaggle_batch/tests -p "test_*.py"
.\.venv\Scripts\python.exe "collect data script\validate_vocabulary.py"
.\.venv\Scripts\python.exe "collect data script\dataset_builder.py"
```

The two `unittest` commands run the offline regression suites; validation checks vocabulary data, and the builder regenerates `data/vocabulary/unified_dataset_v1.json`. Install `requirements-audio.txt` only for audio work. There is no frontend build or dev server yet. Collector entry points support `--help`; collection may use network services, local models, or Windows audio facilities.

## Coding Style & Naming Conventions

Follow the existing Python style: four-space indentation, `snake_case` modules/functions, `PascalCase` classes, and `UPPER_SNAKE_CASE` constants. Keep file paths in `pathlib.Path`, write text as UTF-8, and use standard-library utilities where practical. No formatter or linter is configured; keep changes consistent with nearby code.

## Testing Guidelines

Add focused `unittest` cases named `test_*.py` next to collector code or in `kaggle_batch/tests/`. Mock external services and use temporary directories for filesystem tests. Run the relevant suite before a pull request. No coverage threshold is configured.

## Commits & Pull Requests

Git history uses short descriptive subjects, with occasional prefixes such as `chore:`; there is no enforced commit format. Write a specific, imperative subject. In pull requests, summarize behavior and data changes, link the relevant task or issue, list commands run, and include sample output or screenshots when media or UI results change.

## Agent Workflow & Data Safety

At the start of every task, use `using-agent-skills` to select applicable skills and apply `ponytail` before doing the work. Read their instructions and choose the smallest complete change. Keep credentials and local `.env` files out of commits. Preserve source vocabulary IDs and review provenance; do not mark generated media approved solely because a file exists.
