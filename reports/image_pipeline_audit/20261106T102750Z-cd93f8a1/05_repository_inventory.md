# Repository and artifact inventory

The file-level CSV lists 547 existing files in relevant project directories and root (excluding virtual environments, `.git`, local context and this audit's own outputs). `tracked_in_HEAD=false` means Git does not track the path at the current HEAD; it does **not** mean the file is disposable.

| Current area | Role and observed state |
|---|---|
| `data/vocabulary/` | Three 100-row source files, stable ID registry, semantic decision ledger, image media reviews, and a **derived** saved unified dataset. The registry and ledgers are currently untracked but required to reproduce stable-ID behavior. |
| `data/query/` | Two byte-equivalent 10-record Qwen caches. `generated_qwen.json` sounds complete but contains only the first 10 words. |
| `data/image/en/` | Ten production JPEGs and ten word-named metadata files; JPEG/metadata outputs are ignored by `.gitignore`. The production rice/chicken images remain wrong for approved senses. `_candidates/` exists but retains no candidate files. |
| `data/audio/jp/` | No production MP3s. `_metadata/` is present but empty. |
| `baseline/media-staging/image-queries/` | One 50-record signed prefix cache and one 50-record sparse cache. They collectively cover 100 parsed Qwen queries; neither is named as a single 100-ID ledger. |
| `baseline/media-staging/images/` | Fourteen historical isolated run directories, 198 files total; 101 manifest target events, 92 JPEG asset versions, metadata and empty `_candidates` directories. Two IDs have multiple versions. |
| `baseline/media-staging/audio/` | Eleven run directories, 211 files total, holding 100 staged Japanese MP3s plus metadata/manifests. |
| `baseline/pipeline-2026-10-28/`, `baseline/gtts-smoke-2026-10-28/` | Historical snapshots and smoke assets. They are not production media. |
| `collect data script/` | Collectors, Qwen generator, SigLIP scorer, registry/decision/dataset helpers, staging runners, tests and MP3 fixture. The directory name contains spaces; source paths are embedded in several modules. |
| `reports/`, `CODEX_PROGRESS.md`, `docs/`, `tasks/` | Date-specific reviews, historical progress, contract and generated inventory. Some documents describe earlier partial states; the current tree and current audit take precedence. |
| `.venv/`, `.venv-audio/`, model cache | Local runtimes; `.venv` is used for image/dataset tests and `.venv-audio` for gTTS. Model weights are not tracked in this repository. Exact Qwen revision is not recorded in artifacts; the local SigLIP snapshot directory is `dd658faac399427308559e2c3ac1e99cbe43845d`. |
| `game/`, `web/`, `schedule/`, `CODEX_CONTEXT_BUNDLE/` | Existing project/historical areas; this audit did not modify them. The context bundle is intentionally local and ignored by Git. |

## Concrete organization problems

1. Query evidence is split among three active cache files plus the duplicate 10-record variant. The name `generated_qwen_full_v1.json` actually contains only 50 entries, and the original file contains 10. No pre-audit single file mapped all 100 IDs to raw, parsed and effective queries.
2. `baseline/` mixes snapshots, smoke outputs, staging media and query caches. Run manifests exist for staging but candidate images and score lists are cleaned; reconstruction therefore needs both manifests and separate reports.
3. Production assets are word-named while staging manifests are ID-centered. The saved dataset intentionally reflects only production, so its 10 images and 0 audio can appear inconsistent with a staging report of 99 images and 100 audio unless state is labeled.
4. Image, audio, staging and builder paths are hard-coded independently in `imagecollector.py`, `audiocollector.py`, `stage_*`, `query_generator.py`, `dataset_builder.py` and `tasks/build_full_media_inventory.py`. Moving directories without a coordinated compatibility layer would break joins and resume checks.
5. Critical reproducibility inputs (registry, semantic ledger, dataset builder, generic staging runner, manifests and staged media) are untracked or intentionally ignored at this HEAD. An external clone at `c090eae8` cannot reproduce the current local state from Git alone. The audit does not decide what should be committed.
6. Later reports and `CODEX_PROGRESS.md` are needed to interpret earlier status claims. For example, older documents say 10 Qwen queries or no staged audio; those were valid checkpoints, not current totals. Document titles do not encode whether they are historical or current.

## Findings from the asset scan

- All 10 production JPEGs, 92 staging JPEG versions and their metadata are accounted for by dataset paths or run manifests. The script found no orphan JPEG or metadata, cross-ID SHA-256 duplicate, or asset/metadata/manifest integrity mismatch. This is a structural check, not a semantic approval.
- ID 004 has two versions (production and cooked-rice staging). ID 009 has three (production, restricted Dreamstime candidate and later reviewed Commons candidate). The lineage JSON retains all three; no version was silently promoted.
- All 99 selected images have a source page URL in metadata. Its presence does not verify accuracy, authorship or redistribution rights.
- Candidate URL lists, candidate scores and saved candidate byte files are absent. Re-running remote search would create new evidence, not recover the old pool.

The exact per-file role, size and HEAD tracking state are in `05_repository_inventory.csv`.
