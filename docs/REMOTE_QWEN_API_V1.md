# Remote Qwen3-4B demo API v1

This is an opt-in experiment against a temporary Kaggle GPU worker behind a Cloudflare Quick Tunnel. The existing local `Qwen/Qwen3-1.7B` collectors, their defaults, and their caches are unchanged. No automatic model fallback or generation retry occurs.

## Contract

Set `QWEN_REMOTE_URL` to `https://<one-label>.trycloudflare.com` with no trailing slash, port, credentials, path, query, or fragment. Set `QWEN_REMOTE_TOKEN` to the bearer token in the process environment. Do not save the token in a file. The client makes direct HTTPS connections without environment proxies, rejects DNS results containing nonpublic IP addresses, pins a checked address for the connection, validates TLS against the configured hostname, and does not follow redirects.

`GET /health` sends `Authorization: Bearer <token>` and expects JSON with `status: "ok"`, `model: "Qwen/Qwen3-4B"`, a GPU string, and nonnegative `remaining_generations` and `remaining_seconds`. The probe checks for at least one generation and at least `request_timeout + 5` remaining seconds before POST.

`POST /generate` sends the same authorization plus JSON content type. The body has `prompt`, `system_prompt`, and `max_new_tokens`. The client rejects user prompts over 3,000 characters, system prompts over 800 characters, token requests outside 1–256, and encoded bodies over 8,192 bytes. The server's 2,048 input-token cap is authoritative: v1 provides no tokenizer or token-count preflight endpoint, so the client cannot prove that limit locally. A server HTTP 400 is retained as `invalid_request`, without inventing the cause.

The expected response has the exact model ID, `text`, nonnegative integer `input_tokens` and `output_tokens`, and nonnegative numeric `elapsed_seconds`. JSON responses are limited to 64 KiB. `text` is the API's returned, trimmed text field; it is **not** an untouched raw token stream. The API does not return model revision, EOS or finish reason, input tokenization details, or model loading time. Those fields remain unknown unless independently verified. No claim of exact reproducibility or prompt equivalence with local 1.7B is made.

Errors have a stable `code`, safe message, optional HTTP status, and optional local request duration. Codes include `missing_url`, `missing_token`, `invalid_url`, `invalid_token`, `invalid_host_address`, `contract_incompatible`, `connection_failure`, `timeout`, `redirect_rejected`, `unauthorized`, `invalid_request`, `quota_or_busy`, `remote_unavailable`, `upstream_failure`, `invalid_json`, `response_too_large`, `unexpected_schema`, `model_mismatch`, `invalid_generated_output`, and `insufficient_quota`. HTTP bodies and authorization headers are not logged. POST generation is never automatically retried, including after timeout. A remote failure remains in the experimental record; a local rerun is a separate owner choice.

## Commands from repository root

Use the pinned virtual environment and avoid bytecode writes:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:QWEN_REMOTE_URL = 'https://YOUR-SINGLE-LABEL.trycloudflare.com'
$env:QWEN_REMOTE_TOKEN = '<token in environment only>'
.\.venv\Scripts\python.exe 'collect data script/remote_qwen_probe.py' config
.\.venv\Scripts\python.exe 'collect data script/remote_qwen_probe.py' dry-run
```

`config` and `dry-run` validate local settings only. The dry run makes zero DNS, HTTP, and inference calls. Its JSON diagnostic is created under `reports/remote_qwen/` with a unique name; existing files are never replaced.

After the tunnel and token are available, each live action requires `--live`:

```powershell
.\.venv\Scripts\python.exe 'collect data script/remote_qwen_probe.py' health --live
.\.venv\Scripts\python.exe 'collect data script/remote_qwen_probe.py' generate --live --prompt 'Describe a bowl of cooked rice.' --system-prompt 'You are a vocabulary assistant.' --max-new-tokens 96
```

The single-generation probe checks health first, then makes one POST if quota is sufficient. It writes a separate diagnostic JSON file. Neither command was run during D0.

Prepare the fixed five records or an explicit smaller subset, without remote calls:

```powershell
.\.venv\Scripts\python.exe 'collect data script/remote_qwen_probe.py' prepare --run-id d0-five-unique
.\.venv\Scripts\python.exe 'collect data script/remote_qwen_probe.py' prepare --run-id d0-rice-swim --vocab-id 4 --vocab-id 65
```

The eventual benchmark command is explicit:

```powershell
.\.venv\Scripts\python.exe 'collect data script/remote_qwen_probe.py' benchmark --live --run-id d0-five-unique
```

**Current blocker:** the existing Variant A system prompt is 1,993 characters and the saved Variant B system prompt is 1,560 characters. Both exceed API v1's 800-character limit. The prepared benchmark uses Variant B and returns `contract_incompatible` before DNS or HTTP. Do not shorten either prompt in place or present a modified prompt under its old version. A separately versioned notebook/API revision must raise the system-prompt limit while retaining the exact prompt, and the client contract/version must then be reviewed and updated. The service's 20-attempt and 15-minute limits remain; each selected row uses one generation attempt, with health checked before it.

## Experiment evidence and interpretation

Each prepared run occupies a new directory under `reports/remote_qwen/`. `experiment_manifest.json` freezes the selected stable vocabulary IDs, exact submitted prompts, source SHA-256 hashes, historical 1.7B evidence, existing Variant B evidence, requested remote model, prompt and API versions, provider, generation settings, and unresolved revision. `review_template.csv` has blank independent review labels and shuffled candidate IDs; keep `blind_mapping.json` separate from reviewers. Remote candidate cells stay empty until a compatible run produces `review_ready.csv`.

When compatible, `remote_generation/<row>.json` stores the response text, structural visual-intent parse result, validation errors, local round-trip time, server-reported generation time, token counts, approximate output tokens per second, quota observed before POST, and execution time. A malformed visual-intent JSON object remains as invalid evidence; it is never evaluated, repaired, or promoted. The existing parser checks the five-field JSON structure, but the API's missing EOS signal means completion cannot be confirmed. `execution_summary.json` separates attempted, successful, failed, and structurally valid outputs and records total wall time.

Server-reported `elapsed_seconds` describes model-side generation as measured by the notebook. Local `round_trip_seconds` includes transport and request overhead. Neither is model loading time. No image retrieval, download, SigLIP2 evaluation, semantic approval, or production media promotion is part of this experiment.

Run offline tests with `python -m unittest discover -s 'collect data script' -p 'test_remote_qwen_*.py'`. The full repository suite uses `-p 'test_*.py'`; vocabulary validation uses `collect data script/validate_vocabulary.py`.
