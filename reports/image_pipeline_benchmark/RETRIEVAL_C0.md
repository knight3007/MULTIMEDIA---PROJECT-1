# Phase C0 retrieval benchmark contract

This is a version 1, isolated candidate-retention runner for the completed 25-row query experiment in `20261106-image-query-v1`. The Phase C0 run is an **offline dry run**. It performs no DDGS request, image download, Qwen inference, image scoring, media promotion, or production cache update. The current dry-run directory is `20261107-image-retrieval-c0-v1/`.

## Run layout

```text
<run-id>/
  input_snapshot/       frozen Phase A/B JSON, blank review CSV, mapping, prompts, registry, decisions
  retrieval_results/    one JSON per queried stable ID (empty in a dry run)
  candidates/           original downloaded bytes and normalized JPEG previews (empty in a dry run)
  candidate_metadata/   one JSON per search rank, including rejected/failed results (empty in a dry run)
  evaluation/           25-row query gate CSV; reviewed-label snapshot on a live run
  manifests/            run_manifest.json with hashes, settings, gate and retrieval status
```

`query_gate.csv` only plans Variant B retrieval, at most ten Bing/DDGS results per eligible ID. It records a skip reason for every blocked ID. The historical and fresh Variant A queries remain frozen in the input snapshot for comparison. The six pending semantic IDs (019, 035, 047, 049, 053, 087) are always skipped until the canonical semantic ledger is explicitly approved in a **new query experiment**. C0 does not approve them.

## Human review gate

For a future live run, a bilingual reviewer must independently complete a **copy** of the original `20261106-image-query-v1/owner_review.csv`, retaining all 75 blind IDs and the frozen query/context columns. Every available query requires explicit `true` or `false` in all four label columns, plus rationale, reviewer ID, and ISO timestamp. Missing or changed rows fail preflight. The runner uses `blind_mapping.json` only **after** validating completed human labels, to associate review IDs with variants; it never generates labels from that mapping or model confidence. An approved query requires correct intended meaning and visible depiction, with no wrong-sense ambiguity or text/brand lure. Any negative human finding blocks retrieval. JSON validity and model reasons are never approval.

The blind sheet displays the fresh A and B *parsed model queries*, while the historical arm displays its effective query. For live Variant B, the runner also requires the reviewed query to equal the effective search query. This prevents an approved override from silently changing what the reviewer labeled.

## Retrieval and candidate schemas

`retrieval_results/fresh_b/<vocab-id>.json` stores schema version, canonical ID, variant, effective query, provider `duckduckgo`, explicit backend `bing`, region `wt-wt`, safesearch `moderate`, result cap, search timing/attempts/error, the complete returned raw result list (up to ten), a per-rank status/metadata-path list, and the final checkpoint status. Search failures are retained as `search_failed`.

`candidate_metadata/fresh_b/<vocab-id>/<rank>.json` stores the canonical EN/JP/VN triple, source row, semantic status, target sense, and approved image intent; raw decoded query text, raw model query, parsed query, effective query, visual type/description/negative constraints, query version and provenance; raw provider result, retrieval rank, image and source-page URLs; reported license and its provider-field provenance, with `license_unknown=true` pending rights verification; HTTP status, attempts, search/download timing and failure detail; downloaded-byte and JPEG-preview SHA-256, and relative file paths. Per-result status is one of `downloaded`, `duplicate_url`, `duplicate_content`, `rejected_url`, `download_failed`, or `invalid_image`. A rejected or failed result retains its rank and raw metadata. Rank 1 carries no special suitability claim.

The nested `ranking` object reserves nullable `siglip2_model_id`, `siglip2_revision`, `scoring_text_variant`, `raw_score`, `reranked_position`, `verifier_result`, and `owner_relevance_label`, with retrieval rank repeated for joins. All scoring and relevance values remain null in C0.

## Safety and resume

The live adapter uses the production collector's URL normalization, image byte validation, and JPEG normalization. It adds public-IP DNS checks, pins the resolved public IP for the HTTP connection, verifies HTTPS against the hostname, rejects redirects, caps bytes at the collector's 20 MiB limit, and does not fetch source-page URLs. Search is fixed to DDGS/Bing with a ten-result maximum. Timeout (1–30 seconds), retries (0–2), backoff (0–5 seconds), and request spacing (0–30 seconds) are bounded. URL and original-byte SHA-256 deduplication spans the run. Raw search results and each candidate status are checkpointed. Resume reuses those checkpoints, verifies downloaded-byte and preview hashes, and refuses changed or orphaned candidate files. An interrupted result with no metadata is processed on resume.

The run manifest freezes the prior benchmark tree, its source-input hashes, 474 protected historical file hashes, snapshot hashes, human-label hash when supplied, and settings. The runner verifies protected hashes before and after. Existing production assets, prior benchmark files, and historical caches are read only.

## Commands

From the repository root, reproduce the existing offline plan safely:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe 'collect data script\image_retrieval_benchmark.py' --dry-run --run-id 20261107-image-retrieval-c0-v1 --resume
```

For a **new** dry-run directory, choose a new unique `--run-id` and omit `--resume`.

Proposed command after the independent review CSV is complete. **This command was not executed in C0**:

```powershell
.\.venv\Scripts\python.exe 'collect data script\image_retrieval_benchmark.py' --live --run-id 20261107-image-retrieval-live-v1 --review-labels 'reports\image_pipeline_benchmark\reviewed_query_labels.csv' --max-results 10 --timeout 12 --retries 1 --backoff 1 --rate-interval 2
```

The pending six remain skipped even if the reviewed CSV contains favorable query labels. A later semantic decision requires a new frozen upstream experiment rather than editing the prior one.
