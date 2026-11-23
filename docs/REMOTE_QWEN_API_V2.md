# Remote Qwen3-4B V4 contract and D1 benchmark

The Kaggle notebook's V4 contract raises the system-prompt limit from 800 to 4,096 characters. The local client now uses contract ID `kaggle-qwen3-4b-v4`. The endpoint paths, Bearer authentication, request and response fields, model ID, 3,000-character user-prompt limit, 2,048-token server input limit, 256 generated-token limit, and 8,192-byte JSON body limit remain as documented in [API v1](REMOTE_QWEN_API_V1.md). The v1 document and D0 experiment are preserved as historical records. A D0 manifest stays bound to v1 and cannot be run under the V4 command.

The frozen Phase A/B system prompts are 1,993 and 1,560 characters respectively, and both pass V4 validation unchanged. The client checks character count and encoded JSON bytes separately. It cannot calculate the notebook tokenizer's input-token count; a server HTTP 400 may still reject a request exceeding 2,048 input tokens. No prompt is truncated, rewritten, or normalized before submission.

Direct HTTPS, the exact one-label `*.trycloudflare.com` hostname allowlist, public DNS checks, pinned address, TLS hostname verification, redirect rejection, proxy avoidance, explicit timeout, bounded JSON response, and classified errors remain in force. The client never automatically retries a generation POST or falls back to local 1.7B.

## Frozen ten-request plan

`reports/remote_qwen/d1-five-20261107-qwen4b-v4/experiment_manifest.json` contains exactly one Variant A and one Variant B request for each stable ID: 004 rice, 009 chicken, 041 today, 054 study, and 065 swim. A uses the original system prompt and `Input: <english>\nQuery:` user format with 32 new tokens. B uses the original visual-intent system prompt and trilingual JSON user format with 256 new tokens. Both are greedy, non-thinking requests. The local Variant A benchmark's optional invalid-output retry is deliberately excluded: D1 allows at most ten remote generation attempts. This limits request count while preserving the initial A prompt and generation parameters.

Each request freezes its exact prompt text, UTF-8 SHA-256, canonical EN/JP/VN and semantic status, source file hashes, local 1.7B Variant A/B evidence, and the historical comparison. The review template includes historical, local A, local B, remote A, and remote B candidates for each word. Review labels start blank; `blind_mapping.json` should be withheld from reviewers. No local model is rerun.

## Owner-run commands

From the repository root, once the Kaggle V4 worker and tunnel are running:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:QWEN_REMOTE_URL = 'https://YOUR-SINGLE-LABEL.trycloudflare.com'
$env:QWEN_REMOTE_TOKEN = '<token supplied privately in this process>'
.\.venv\Scripts\python.exe 'collect data script/remote_qwen_probe.py' config
.\.venv\Scripts\python.exe 'collect data script/remote_qwen_probe.py' dry-run
.\.venv\Scripts\python.exe 'collect data script/remote_qwen_probe.py' health --live
.\.venv\Scripts\python.exe 'collect data script/remote_qwen_probe.py' benchmark-v4 --live --run-id d1-five-20261107-qwen4b-v4
```

`config` and `dry-run` make no DNS, HTTP, or model calls. `health --live` makes one authenticated GET and no generation attempt. `benchmark-v4 --live` first validates every frozen request, both environment variables, the model ID from `/health`, and sufficient budget for all ten calls. With the default 30-second timeout, it requires at least ten remaining generations and 350 remaining session seconds before the first POST. It checks health again before each later request. The session has at most 20 generation attempts and 15 minutes; the D1 plan requires at most ten POSTs. If a request fails or times out, the run stops and keeps the partial evidence. A second invocation refuses to restart it automatically.

The command has **not** been run against Kaggle during D1 preparation. The owner can inspect the manifest and review template before choosing to run it. A unique new run directory is required for a fresh attempt; existing D0, Phase A/B, C0, vocabulary, caches, and media files are never overwritten.

## Result interpretation

After a live run, `remote_generation/<ID>-<variant>.json` records the API-returned `text` field exactly as received, parsed query or visual intent when valid, validation errors, requested and returned model IDs, local round-trip latency, server-reported elapsed time, server input/output token counts, approximate output tokens per second, observed quota, and UTC execution time. Invalid text remains in its evidence file. `execution_summary.json` records completed and failed calls plus total wall time. `review_ready.csv` fills remote candidate cells while leaving every human label blank.

The API's `text` is already trimmed by the server and must not be called an untouched raw token stream. V4 still does not return a verified model revision, EOS flag, finish reason, tokenizer preflight count, or model loading time. Those fields remain null, `unverified`, or `unavailable`; the client does not infer them. A completed HTTP response only supports structural parsing, not proof that the model stopped with EOS. Local round-trip latency includes network overhead and differs from server-reported generation time. Model accuracy and speed remain unmeasured until a real run and independent human review.
