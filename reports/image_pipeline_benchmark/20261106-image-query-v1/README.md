# Image query benchmark v1

This directory contains a query-only paired experiment on source rows 004, 009, 019, 035, 041, 042, 043, 047, 048, 049, 050, 051, 053, 054, 055, 061, 062, 065, 066, 067, 071, 074, 077, 082 and 087. Source rows resolve to stable vocabulary IDs through `id_registry_v1.json`. No image retrieval, scoring, downloads or media promotion occurs.

## Reproduce

From the repository root, with the pinned `.venv` and a local snapshot of `Qwen/Qwen3-1.7B` in `HF_HOME`:

```powershell
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONDONTWRITEBYTECODE = '1'
.\.venv\Scripts\python.exe 'collect data script/image_query_benchmark.py' --run-id YOUR_UNIQUE_RUN_ID
```

The runner requires a new directory under `reports/image_pipeline_benchmark/`, records SHA-256 of every input and protected data file, and uses the local model snapshot offline. It refuses to overwrite an existing run. To continue an interrupted run, use the same ID with `--resume`. Resume checks hashes and keeps each completed raw generation file. A completed run can be resumed without regenerating outputs; existing owner labels are preserved. If an input or protected file changes, create a new run after resolving the change.

Run offline tests with:

```powershell
cd 'collect data script'
..\.venv\Scripts\python.exe -m unittest test_image_query_benchmark -v
```

## Evidence and interpretation

`experiment_manifest.json` records the schema, model revision, device, prompt settings, input and protected file hashes, duration and failures. `prompts.json` freezes both exact system prompts and input formats. `raw_generation/variant_a/` and `raw_generation/variant_b/` contain one JSON evidence file per source row. Variant A calls the original Qwen generator logic with its 32-token greedy, non-thinking decode and one invalid-output retry. Variant B uses a versioned visual-intent prompt, 256-token greedy, non-thinking decode and strict five-field JSON validation. Invalid output is retained verbatim with an error and no generated fallback.

`query_experiment.json` is the versioned, complete 25-row record; `query_experiment.csv` is its flat comparison view. Historical parsed queries are read from the audit ledger and kept separate from fresh Variant A and B generation. The historical raw decoded text is `null` where it was never persisted. `raw_model_query` means the Qwen-produced parsed query; `effective_search_query` applies only an existing human-approved override, when present. For 004 and 009 those are `cooked rice` and `chicken meat`. A pending semantic decision stays pending.

`owner_review.csv` is a blind, seeded shuffle of historical current queries, fresh Variant A queries and fresh Variant B queries. All human-label columns are blank. Give this file to a bilingual reviewer without `blind_mapping.json`; keep the mapping aside until labels are complete. For each candidate, the reviewer should assess intended meaning, visible depiction, ambiguous or wrong sense, and text or brand lure, with rationale and reviewer identity. An empty candidate query signals generation failure and should be handled as a failure rather than labeled as a semantic query. Query quality cannot be ranked from these model outputs alone; independent labels are required.
