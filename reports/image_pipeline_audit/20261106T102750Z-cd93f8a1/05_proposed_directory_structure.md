# Proposed future layout and safe migration sequence

This is a proposal only. No file or directory was moved in this audit.

```text
data/
  source/vocabulary/{en,jp,vn}.txt
  registry/{id_registry_v1,semantic_decisions_v1,image_media_reviews_v1}.json
  generated_queries/{qwen_parsed,query_ledger}.json
  media/production/{images,audio}/
  media/staging/<run-id>/
runs/{query,image,audio}/<run-id>/{manifest,candidates,scores,logs}/
reports/{audits,reviews}/
models/                 # local cache pointer or manifest; weights stay out of Git
tests/
```

The current path contract is explicit in `query_generator.py:DEFAULT_QUERY_CACHE`, `imagecollector.py:IMAGE_DIR`, `audiocollector.py:AUDIO_DIR`, `stage_image_replacements.py:STAGING_BASE`, `stage_japanese_audio.py:STAGING_BASE`, `stage_vocabulary_images.py:QUERY_CACHE`, `dataset_builder.py:OUTPUT_PATH` and `tasks/build_full_media_inventory.py`. Existing JSON manifests also embed current relative paths. A direct rename would invalidate saved references and cache validation.

## Future migration, if separately approved

1. Define one versioned path map and a manifest schema that distinguishes source, derived cache, staging and production. Add read-only resolution for legacy paths first, with tests for all 100 ID joins and resume of old runs.
2. Snapshot every source/asset with SHA-256, copy into a new versioned tree without deleting originals, and write an old-to-new path mapping for manifests, dataset and reviews. Keep source-of-truth registry/decisions separate from reproducible derived files.
3. Verify copied bytes, metadata, stable IDs, license and owner approval references, plus production/staging separation. Run the full offline suite and read-only dataset comparison against the old tree.
4. Switch one consumer at a time behind the path map, keeping old readers operational. Preserve old run IDs and hashes; never rewrite historical manifests to look like new runs.
5. For rollback, point consumers back to original paths and retain the copy and mapping as evidence. Remove old files only in a separate, owner-approved cleanup after production verification and backups.

Future run manifests should save raw/parsed/effective query separately, every candidate URL and fetch status, candidate hash/preview, all SigLIP scores, model revision and timing. A candidate-retention policy should balance reproducibility with disk and rights constraints.
