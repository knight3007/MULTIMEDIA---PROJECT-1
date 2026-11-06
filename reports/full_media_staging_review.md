# Full media staging review — 2026-11-06

## Scope and result

This execution collected **staging media only** for the canonical 100-ID dataset. It did not promote files, alter the vocabulary/semantic ledger, rebuild the saved dataset, publish media URLs, or commit. The working tree started at HEAD `c090eae8dd257b114898bb096bc9f51ab5bfd34c` with substantial pre-existing modified and untracked files; all were preserved. [Machine-readable 100-ID inventory](full_media_staging_inventory_v1.json) records paths, hashes, provenance, per-ID blockers and screening notes. [Preflight hash snapshot](full_media_staging_preflight_hashes.json) protects 87 pre-existing source/media files.

| Measure | Verified outcome |
|---|---:|
| Stable source/dataset IDs | 100 / 100 |
| Technically valid staged Japanese MP3s | 100 / 100 |
| Existing MP3s reused from runs 001–020 | 20 |
| MP3s newly downloaded for IDs 021–100 | 80 |
| Audio failures / missing IDs | 0 / 0 |
| Existing production JPEGs accounted for | 10 |
| New technically valid staged JPEGs | 89 / 90 production-missing IDs |
| Image IDs with a technically available file | 99 / 100 |
| Image ID still blocked | `vocab-000038` |
| New images with locally observed visual issue | 29 / 89 |
| New images with confirmed reuse rights | 0 / 89 |
| Media eligible for immediate promotion / game use | 0 / 0 |

Technical presence is not semantic, visual, licensing, listening or owner approval. The 89 new images remain owner-review pending; 60 were not individually screened beyond technical validation. All 100 audio files remain in staging; production audio has zero MP3s.

## Slice A — prior media and protected assets

The three historical audio runs for IDs 001–020 passed stable-ID, canonical reading, provider/voice, complete MP3 frame, duration, size, metadata, SHA-256 and manifest checks. IDs 001–010 retain the recorded exact-hash listening approvals. The owner's later general comment about Batch 3 supports continued collection but is **not** exact-hash approval for IDs 011–020. IDs 021–100 have no listening approval yet. No Japanese gTTS distribution/usage permission or production promotion is recorded.

All ten production JPEGs decoded with their metadata through the read-only dataset builder. The original rice and chicken JPEGs remain historical wrong-sense production assets. The cooked-rice staging candidate visually matches the approved sense, but its existing review marks use **restricted**. The older Dreamstime chicken candidate is visibly watermarked and restricted. The newer chicken-meat candidate at `baseline/media-staging/images/20261029T041516Z-eea4173d/chicken.jpg` matched SHA-256 `f897f975b60a61a1f98050fb71f84481dcf789475a86508bc046318f02078ccc`, metadata and source. Its recorded review marks the candidate suitable and permitted, with promotion still pending. The [Wikimedia Commons file page](https://commons.wikimedia.org/wiki/File:Kycklingfil%C3%A9.jpg) currently describes raw chicken breast, names Dnor as the author, and states a public-domain self-release. The [Lemon Blossoms policy](https://www.lemonblossoms.com/disclaimers-privacy-policy/) requires permission for other photo uses and states a default noncommercial, no-derivatives license; this supports keeping the rice candidate restricted. These statuses apply to the exact reviewed candidates, not to other files from those sites.

## Slice B — Japanese audio

The verified `.venv-audio` CLI ran eight isolated ten-ID batches using `--timeout 12 --retries 1 --retry-delay 2 --rate-limit-delay 1`. Each run wrote a per-item manifest and was rerun with the same IDs, run ID and `--resume`. All 80 first passes recorded `downloaded`, all 80 resume passes recorded valid cache hits, and hashes remained unchanged. No 403/429, individual audio failure or unnecessary retry was observed. Original provenance across all 100 assets is 97 downloads and three verified smoke-cache copies; 20 of those assets predated this execution.

| IDs | Run ID | New MP3s | Resume |
|---|---|---:|---:|
| 021–030 | `20261106T090418Z-d68cc7d3` | 10 | 10 cache hits |
| 031–040 | `20261106T090514Z-3e1524e5` | 10 | 10 cache hits |
| 041–050 | `20261106T090539Z-4a029141` | 10 | 10 cache hits |
| 051–060 | `20261106T090614Z-e0de17f1` | 10 | 10 cache hits |
| 061–070 | `20261106T090638Z-5aa78ca3` | 10 | 10 cache hits |
| 071–080 | `20261106T090712Z-c327a11a` | 10 | 10 cache hits |
| 081–090 | `20261106T090735Z-e2fd33b3` | 10 | 10 cache hits |
| 091–100 | `20261106T090809Z-a62c463b` | 10 | 10 cache hits |

Each inventory record includes its exact MP3 path, SHA-256, duration, size, `google_translate_gtts`, `ja`, voice `{tld: com, slow: false}`, source run and cache provenance. The saved unified dataset correctly still reports all production audio as missing because staged assets are not production assets.

## Slice C — generic image staging and Qwen queries

Added `collect data script/stage_vocabulary_images.py` to reuse the existing DDGS Bing search, bounded candidate download/normalization and SigLIP2 ranking. It accepts 1–10 explicit stable IDs, isolates each run, validates the canonical registry/dataset, rejects unsafe IDs/paths and production-present targets, preserves approved query precedence, writes a per-ID manifest and resumes only when JPEG, metadata, source and SHA-256 still match. Test-first recovery guards reject resume if a canonical query/target changed or a prior successful JPEG/hash/metadata no longer matches; the caller must preserve that run and investigate or use a new run ID. The legacy rice/chicken runner was not changed. Eight focused tests passed after red tests for the new behavior; the full suite later passed 108/108.

The first 50 valid Qwen queries live in the isolated, signed prefix cache `baseline/media-staging/image-queries/generated_qwen_full_v1.json`; its first ten were copied byte-for-byte from the original cache. The remaining queries live in `generated_qwen_sparse_v1.json`, bound to the same canonical 100-word order and prefix hash. Qwen initially rejected six verbs (`go`, `read`, `eat`, `help`, `choose`, `swim`) with outputs such as `go verb`. The sparse cache recorded those failures without halting other IDs. A second Qwen prompt explicitly requesting a person performing the action produced six validator-passing model queries; the cache preserves both the prior failure and correction prompt. All 100 query slots now have model output, but no new query is owner-approved. The original `data/query/generated_qwen.json` hash remained unchanged.

SigLIP2 loaded from the existing local model snapshot on CUDA with float16. Image runs used explicit Bing backend, at most three results per ID, `--timeout 10 --retries 1 --retry-delay 1 --rate-limit-delay 1`. No model substitution or DNS/proxy/certificate change occurred. The exact effective query was used for both search and scoring. Several Qwen queries are syntactically valid but semantically poor, e.g. `rain illumination`, `today timepiece`, `buy action` and `software device`; their selected images must not be treated as approved.

## Slice D — image collection and recovery

| IDs | Run ID | New valid JPEGs | Current blocker |
|---|---|---:|---|
| 011 | `20261106T092640Z-a11a8a8d` | 1 | None |
| 012–020 | `20261106T092753Z-f005e016` | 9 | None |
| 021–030 | `20261106T093018Z-b749e191` | 10 | None |
| 031–040 | `20261106T093301Z-67bd98cc` | 9 | ID 038 missing approved image intent |
| 041–050 | `20261106T093523Z-ef98c5c6` | 10 | None |
| 051–060 | `20261106T093745Z-ec8824e8` | 6 | Four initial Qwen failures, later recovered |
| 061–070 | `20261106T093948Z-5be953da` | 8 | Two initial Qwen failures, later recovered |
| 071–080 | `20261106T094206Z-a7c27573` | 10 | None |
| 081–090 | `20261106T094449Z-6cf101fa` | 10 | None |
| 091–100 | `20261106T094724Z-11be2473` | 10 | None |
| Recovered 051, 052, 057, 060, 064, 065 | `20261106T095405Z-255c864a` | 6 | None |

All 89 successful JPEGs passed independent decode, dimensions, exact ID/word/query/provenance, Bing source URL, SigLIP selection, metadata and SHA-256 checks. Same-run resume produced 89 cache hits with no new download and no changed hash. The manifests contain 265 raw search results, 259 normalized valid results and 236 successfully downloaded candidates across the 89 selected outputs. **Twenty-three** normalized candidates did not download; console output showed examples of HTTP 403/400, certificate failure and SSL timeout. The existing collector logs skipped-candidate reasons to the console but does not persist each reason in the manifest, so this report does not assign an exact reason count. No final selected-image search, scoring or JPEG validation failure remained.

`vocab-000038` is the only missing image ID. The semantic ledger approves “one friend (singular)” but supplies no `image_search_intent`; staging recorded `blocked_semantic_review` and made no Bing request for that ID. The six Qwen blocks remain visible in their original run manifests, while the recovered assets are referenced from a new run. No historical run was overwritten.

## Image quality and rights screening

Local viewing found issues in **29** of the 89 new files: 14 flags for a wrong referent, 16 for embedded text, 10 for visible watermark, 11 for low visual suitability and three for ambiguity (categories overlap). Examples include ID 019 `rain` (night resort plus logo), 041 `today` (watch), 043 `yesterday` (TV poster), 051 `go` and 065 `swim` (static portraits), 059 `buy` (Action-branded store), 085 `where` (film poster), and 088 `please` (watermarked iStock preview). ID 018 `sun` is a spectrum chart, 036 `family` and 070 `language` are text-heavy slides, and 069 `music` and 097 `firefighter` have visible stock marks. The [inventory](full_media_staging_inventory_v1.json) identifies all observed issues by exact ID and hash. The other 60 new images remain **unverified**, not cleared.

The two known wrong-sense production JPEGs plus 14 locally flagged new wrong-referent images yield 16 IDs with known semantic issues. Bing image results do not establish reuse rights. All 89 new candidate licenses remain `unknown`; 27 selected URLs point to Pinterest or stock/premium hosts that warrant source-specific review, and this host count is only a triage signal. The existing reviewed rice and older Dreamstime chicken candidates are the two `verified_restricted` historical candidates; the exact Commons chicken candidate remains the one `verified_permitted` candidate in the existing review ledger. No new candidate was silently labeled permitted or restricted. No watermark was removed.

## Slice E/F — inventory and verification

- [Inventory](full_media_staging_inventory_v1.json): exactly 100 unique stable IDs. Each record joins EN/JP/VN, semantic state, production and staging image assets, source/query/SigLIP/hash/license, audio path/hash/duration/provider/voice/listening state, owner approval, blockers and null public media URLs. Rice/chicken historical candidates remain separate from their production JPEGs. All `game_ready` fields are false.
- Full offline command `./.venv/Scripts/python.exe -m unittest discover -s 'collect data script' -p 'test_*.py'`: **108 tests in 4.466 s, OK, exit 0**. The earlier baseline was 100 tests; eight focused image-staging tests were added.
- Vocabulary validator: **100 physical rows, 0 structural issues, exit 0**.
- Read-only `.venv` dataset build exactly matched the saved 100-record unified dataset; production audio remained 0, and all dataset/inventory public media URLs remained null.
- All **87** SHA-256 entries in the preflight snapshot matched at the end: original vocabulary, stable registry, semantic decisions, original Qwen cache, unified dataset, production JPEG/metadata/audio paths, prior audio/image staging and smoke assets. New staged media were separately revalidated against their own run manifests.
- Scoped `git diff --check` for tracked affected context returned **exit 0**; a scan of newly created task/code/inventory files found zero trailing-whitespace issues. `git status` still shows the pre-existing dirty tree plus this task's new staging/report/code files. No commit, push, reset, clean or tag was used.

## Next decision

Request a concrete image search intent for ID 038, replace the 29 flagged image candidates through separately reviewed sources, then inspect the remaining 60 new images and eight unverified original production images. Confirm source-specific reuse rights and exact-hash owner visual/listening approvals, including Japanese audio distribution rights, before a separate production-promotion change. Backend integration should consume a reviewed production manifest only after that promotion; none was started here.
