# Forensic audit work plan

1. Freeze the dirty-tree baseline: record branch, HEAD, status and hashes of existing source, media, staging and reports. Verify 100 stable IDs.
2. Reconstruct Qwen query provenance from original and staging caches, semantic decisions and run manifests; export one row per stable ID without inventing raw output.
3. Inventory every production and staged image version; compare manifests, metadata, files and saved dataset. Build labeled contact sheets from local JPEGs only.
4. Classify observed quality failures by the first stage supported by evidence; document missing candidate data and project organization. Recommend a small controlled benchmark.
5. Run offline tests and read-only dataset validation, compare protected hashes, write the audit manifest, and append a concise checkpoint to `CODEX_PROGRESS.md`.

The owner directly requested this audit and its files. No new retrieval, model inference, media promotion or directory migration is part of this run.
