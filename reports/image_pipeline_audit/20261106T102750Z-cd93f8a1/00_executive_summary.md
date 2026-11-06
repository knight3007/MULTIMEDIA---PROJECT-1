# Forensic image pipeline audit — 2026-11-06

Audit ID: `20261106T102750Z-cd93f8a1`. This run used existing local files only. No Qwen inference, DDGS request, image download, media promotion, model replacement, directory move or Git mutation was performed.

## Answers to the owner's eight questions

**Q1. Where are the 100 Qwen outputs?** The original `data/query/generated_qwen.json` has **10** parsed queries. The isolated staging prefix `baseline/media-staging/image-queries/generated_qwen_full_v1.json` has **50** (its first 10 repeat the original); `generated_qwen_sparse_v1.json` has the remaining **50**. The combined, stable-ID-centered view is `02_qwen_queries_100.json` and `.csv` in this audit. No pre-existing single 100-row raw-output file exists.

**Q2. How many trace to actual inference?** There are **100 unique parsed queries labeled as Qwen output**, with matching model ID and signed canonical-order cache. Only **6 accepted decoded raw strings** were saved, all from corrected verb inference; raw text for the other **94** cannot be reconstructed. Six earlier rejected verb strings also survive in validation error text. The caches have no per-record Qwen run ID or timestamp; linked image run IDs are reported separately. Cache provenance supports the pipeline attribution but is not an independent per-inference attestation. Newly generated diagnostic queries: **0**; parsed-query gaps: **0**. A new inference would not recover historical raw text, so the optional Qwen-only recovery was not run.

**Q3. Which images are wrong?** There are 10 production JPEGs plus 92 staged versions, covering **99 of 100 IDs**; ID 038 has no image because approved friend sense lacks an image intent. Two legacy production images, rice and chicken, conflict directly with owner-approved meanings. Among the 99 paths selected by the latest staging inventory, 29 were flagged earlier and 25 more were flagged from this audit's contact sheets: **54 provisionally problematic**, 45 without a recorded issue, all still unapproved. Examples: ID 035 `shirt` is a nose anatomy diagram; ID 041 `today` is a wristwatch; ID 051 `go` and ID 065 `swim` are static portraits; ID 087 `hello` is from *Hello Objects*. These are model-assessed observations, not owner visual decisions.

**Q4. Where do failures first appear?** The 100-ID triage assigns 17 currently flagged assets to an observable Qwen query-stage error, two historical production assets to pre-approval wrong-sense queries, and five otherwise recognizable images to a watermark/reuse problem. **Thirty-two of the 54 flagged current images cannot be assigned to Bing versus SigLIP**, and 44 of the 100 have no flagged current image or earlier query mismatch. Thus the dominant cause cannot be established from retained evidence. The mapping audit found no ID/filename/metadata mismatch across 102 referenced versions.

**Q5. What is missing?** Full DDGS result lists, downloaded candidate files, all candidate SigLIP scores, per-candidate retry logs, 94 accepted raw Qwen texts, exact Qwen model revision/timestamps, and independent human labels. The candidate cache currently contains zero `.img` files. Only selected URLs and scores survive.

**Q6. What is disorganized?** The 100 queries span misleadingly named 10/50/50 cache files across `data/query/` and `baseline/media-staging/`. `baseline/` mixes snapshots, smoke assets, staged media and query cache. Generated but necessary registry/ledger/code/media are untracked at this HEAD, while production media are ignored. Several hard-coded paths and historic reports require careful state interpretation. `05_repository_inventory.md` and `.csv` show the details; the proposed structure is a plan only.

**Q7. What should improve next?** Test the existing Qwen model with a target-sense-aware prompt first. The current prompt receives only English and produces errors such as `rain illumination` and `today timepiece`. Broader search, a new ranker or visual verifier cannot be judged fairly while full candidates and human labels are missing. The smallest recommended experiment is a fixed 25-ID, query-only paired test with raw output retention and blind human semantic labels.

**Q8. What is the safe sequence?** (1) Label the fixed subset and run isolated query-only comparison; (2) if query quality improves, save all candidates and scores in a bounded retrieval benchmark; (3) separate candidate recall from top-1 rank quality; (4) only then decide on prompt/search/ranker changes and review licenses; (5) promote assets only under separate owner approval. Keep original caches and all historical runs intact.

## Baseline and integrity

- Branch `main`, HEAD `c090eae8dd257b114898bb096bc9f51ab5bfd34c`, with substantial pre-existing modified/untracked content. The audit added only its directory and a progress checkpoint.
- Offline suite: `.venv` ran **108 tests in 4.796 s, OK, exit 0**. Vocabulary validator: **100 rows, 0 structural issues, exit 0**. Read-only builder matched the saved 100-record dataset exactly, with 10 production images and 0 production audio.
- Asset scan: 14 image manifests, 101 target events, 102 referenced JPEG versions, 0 orphan JPEGs, 0 orphan metadata, 0 cross-ID duplicate SHA-256s, 0 manifest/metadata integrity findings. Ninety-one selected staged images have 240 successfully downloaded candidate counts in their manifests, but no complete candidate lists or score arrays.
- `audit_manifest.json` records command exit codes and the protected-file hash comparison. The audit's 100-row ledgers and five contact sheets are reproducible with `build_audit.py` from this unchanged working tree.

## Independent review packet

Start with `02_qwen_queries_100.csv`, `03_image_lineage_100.csv`, `04_image_quality_review.csv` and the five images in `contact_sheets/`; use the corresponding JSON files for all historical asset versions and run events. Read `01_pipeline_architecture.md`, `04_image_failure_analysis.md` and `06_benchmark_design.md` for interpretation and next steps. All files are under this one audit directory.
