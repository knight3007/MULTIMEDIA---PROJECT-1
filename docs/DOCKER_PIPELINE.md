# Docker: private Excel-to-multimedia pipeline

This packages the existing B-002 importer, frozen image pipeline (Qwen3-1.7B, DDG retrieval, SigLIP2), English/Japanese gTTS, Content Pack builder, and final HTML gallery. It does not select a different model or provider. The generated media and review gallery are private; existing internal-only asset restrictions remain in the pack.

## Build and run

Start Docker Desktop with the Linux engine. From the repository root in PowerShell:

```powershell
docker compose build pipeline
docker compose run --rm pipeline /input/test_vocabulary_15_B001.xlsx --reuse-reviewed-run /app/reports/EXCEL_15_SMOKE/run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291
```

The 15-word command reuses the exact hash-checked images from the owner's previously reviewed private run, retains `needs_review` and provenance, and generates new EN/JA audio. It does not claim those images were generated again or approved for release. The default input mount is `./tests/fixtures/b001` (read-only). The default output mount is `./docker-output`; each new import creates `docker-output/run-<UUID>/`. To process another workbook with the live configured pipeline, mount its containing directory and use the filename inside `/input`:

```powershell
$env:INPUT_DIR = 'D:/path/to/workbooks'
docker compose run --rm pipeline /input/words.xlsx
```

To resume an interrupted run, keep the same workbook and output directory:

```powershell
docker compose run --rm pipeline /input/words.xlsx --resume /app/reports/EXCEL_FULL_PIPELINE_FINAL/run-<UUID>
```

The runner rechecks the normalized workbook fingerprint. Existing per-item audio with matching metadata and SHA-256 is reused; image and pack state are read from the run. If a final gallery already exists for the same Content Pack, it is reused. A conflicting gallery or incomplete audio is preserved for inspection and causes an explicit failure. A stopped run can be resumed without changing its IDs. Completed per-item image failures are retained as evidence and require a fresh run after the environment is fixed; the wrapper exits nonzero for `*_FAILED` stages. Do not delete partial output to resume.

The entry point prints the run, active Content Pack and gallery paths. Host equivalents are `docker-output/run-<UUID>/content_pack*/content_pack.json` and `docker-output/run-<UUID>/final_review_gallery.html`. The active pack name is in `execution_report.json`; do not assume it is `content_pack` after a resumed change. `docker-output/docker_pipeline.log` keeps console output and tracebacks on the host. `execution_report.json`, `quality_report.json`, `image_selection_manifest.json`, and `audio_manifest.json` remain in each run.

Open the gallery through localhost after the run (use an available port):

```powershell
$run = Get-ChildItem 'docker-output' -Directory -Filter 'run-*' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
python -m http.server 8767 --bind 127.0.0.1 --directory $run.FullName
```

Open [http://127.0.0.1:8767/final_review_gallery.html](http://127.0.0.1:8767/final_review_gallery.html). It has English–Vietnamese and Japanese–Vietnamese modes, the matching audio, image preview, search, status filters and an explicit missing-image state. Media references are relative to the Content Pack and gallery. Stop the server with Ctrl+C.

## Mounts, providers and resources

| Host setting | Container path | Use |
|---|---|---|
| `INPUT_DIR` (default `./tests/fixtures/b001`) | `/input` | Read-only Excel files |
| `OUTPUT_DIR` (default `./docker-output`) | `/app/reports/EXCEL_FULL_PIPELINE_FINAL` | Persistent private runs and logs |
| `MODEL_CACHE_DIR` (default `./docker-model-cache`) | `/root/.cache/huggingface` | Persistent Qwen and SigLIP model downloads |
| `./data`, `./baseline`, `./reports`, `./tests/fixtures`, `./batch_inputs`, `./.github`, `./.git` | Same paths under `/app` | Read-only approved-image, historical audio/decision, test fixture, CI workflow and Git provenance inputs |

`./reports` is mounted read-only with the writable output mounted at its child path. The canonical vocabulary, approved registry and historical media cannot be changed by the container. To reuse a compatible native Hugging Face cache, set `MODEL_CACHE_DIR` to its host directory before the run, for example `$env:MODEL_CACHE_DIR = 'D:/huggingface-cache'`. The image itself contains no model weights, `.env` files or credentials.

The finalized provider/model choices are fixed in the existing pipeline. Optional `HF_ENDPOINT`, `HF_TOKEN`, `HF_HUB_OFFLINE`, `HTTP_PROXY`, `HTTPS_PROXY` and `NO_PROXY` pass through Compose for access to the configured Hugging Face endpoint and remote services. Leave `HF_HUB_OFFLINE=0` to download missing weights; the Docker entry point fills a missing SigLIP cache only for workbooks with new image work. Set offline mode to `1` only after the mounted cache contains both models. DDG image retrieval and gTTS English/Japanese require network access. Provider refusal, cache misses and model load errors are reported; no provider fallback is substituted.

The default service runs on CPU if CUDA is unavailable. Qwen3-1.7B and SigLIP2 need substantial RAM and CPU time; a full new-image run may be impractical on a small CPU machine. On a Linux Docker host with a working NVIDIA Container Toolkit and CUDA-capable PyTorch, use `docker compose run --rm pipeline-gpu /input/words.xlsx` (the `gpu` profile service requests all GPUs). Check `docker compose run --rm --entrypoint python pipeline-gpu -c "import torch; print(torch.cuda.is_available())"` first. If false, stop and inspect the GPU runtime rather than changing models. GPU is optional for the pipeline, but may be needed for feasible processing time.

## Tests and limits

Run the offline suites inside the built image:

```powershell
docker compose run --rm -v './reports/EXCEL_FULL_PIPELINE_FINAL:/app/reports/EXCEL_FULL_PIPELINE_FINAL:ro' --entrypoint python pipeline -m unittest discover -s '/app/collect data script' -p 'test_*.py' -q
docker compose run --rm --entrypoint python pipeline -m unittest discover -s /app/kaggle_batch/tests -p 'test_*.py' -q
```

The pipeline does not verify pronunciation by ear, educational image meaning, public image rights or owner approval. New ranked images remain `needs_review`; a missing image stays explicit. The final gallery is internal review tooling, not the Web Game. For a 100-word run, mount the directory containing the existing benchmark workbook or reconstruct one using the documented native fixture script, then pass its path under `/input`. A full 100-word run can make many remote requests and should be attempted only after the 15-word Docker run and resource check.

The reconstructed 100-word benchmark used for this verification is available under `reports/EXCEL_FULL_PIPELINE_FINAL`. To repeat that run:

```powershell
$env:INPUT_DIR = './reports/EXCEL_FULL_PIPELINE_FINAL'
docker compose run --rm pipeline /input/benchmark_reconstructed.xlsx
```

The [verification report](../reports/DOCKER_001/verification_report.md) records the actual 15-word and 100-word outputs, generated versus reused counts, browser checks, test results, diagnostic runs and remaining limits.
